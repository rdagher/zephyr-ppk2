#!/usr/bin/env python3
"""Attribute captured time, current, and energy to trace markers.

Reads a GUI-parity CSV (from ``ppk2 capture`` or a Nordic GUI export)
and reports, per marker channel D0..D7: region count, energy
(mean ± std µJ), width (ms), and mean current (µA). Energy per region
is the charge integral times VDD — each row is one 10 µs sample.

Pulses shorter than 5 ms count as sync bursts, not regions. Samples
with no marker high are the idle floor. Stdlib only.

Usage:
    python attribute.py trace.csv --vdd 3.0 --name 1=cycle --name 2=wakeup
"""

import argparse
import csv
import gzip
import statistics
from dataclasses import dataclass
from pathlib import Path

SAMPLE_PERIOD_S = 10e-6  # 100 kSPS
SYNC_PULSE_MAX_S = 0.005  # pulses shorter than this are a sync burst
POWER_ON_UA = 200.0  # rail-up detection: logic pins float while the DUT is unpowered


@dataclass
class Pulse:
    """One contiguous high region of a logic pin."""

    start_s: float
    duration_s: float
    charge_uc: float  # integral of current over the pulse, in µC

    def energy_uj(self, vdd_v: float) -> float:
        """Energy over the pulse in µJ (charge x VDD)."""
        return self.charge_uc * vdd_v

    def mean_current_ua(self) -> float:
        """Mean current over the pulse in µA."""
        return self.charge_uc / self.duration_s if self.duration_s else 0.0


def load_rows(path: Path) -> list[tuple[float, float, int]]:
    """CSV -> one (t_ms, current_µA, D0..D7 bitmask) tuple per sample."""
    rows: list[tuple[float, float, int]] = []
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", newline="") as f:
        for rec in csv.DictReader(f):
            levels = 0
            for i in range(8):
                if rec.get(f"D{i}") == "1":
                    levels |= 1 << i
            rows.append((float(rec["Timestamp(ms)"]), float(rec["Current(uA)"]), levels))
    return rows


def collect_pulses(rows: list[tuple[float, float, int]], pin: int) -> list[Pulse]:
    """Walk the samples once, closing a Pulse at each falling edge of `pin`.

    A pulse only opens on a real rising edge — a pin already high at
    the first sample is ignored (its start is unknown), just like a
    pulse still high at the last sample (its end is unknown).
    """
    pulses: list[Pulse] = []
    high = False
    seen_low = False
    start_s = 0.0
    charge_uc = 0.0
    for t_ms, ua, levels in rows:
        level = (levels >> pin) & 1
        if level and not high and seen_low:
            high, start_s, charge_uc = True, t_ms / 1000.0, 0.0
        if high and level:
            charge_uc += ua * SAMPLE_PERIOD_S
        if not level:
            seen_low = True
            if high:
                high = False
                pulses.append(Pulse(start_s, t_ms / 1000.0 - start_s, charge_uc))
    return pulses


def first_region_start_ms(rows: list[tuple[float, float, int]]) -> float:
    """Start (ms) of the earliest ≥5 ms pulse on any channel; 0.0 if none."""
    starts = [
        p.start_s * 1000.0
        for ch in range(8)
        for p in collect_pulses(rows, ch)
        if p.duration_s >= SYNC_PULSE_MAX_S
    ]
    return min(starts, default=0.0)


def stats_line(name: str, pulses: list[Pulse], vdd_v: float) -> str:
    """One report row: count, energy mean ± std, mean width, mean current."""
    energies = [p.energy_uj(vdd_v) for p in pulses]
    durations = [p.duration_s * 1000.0 for p in pulses]
    currents = [p.mean_current_ua() for p in pulses]
    mean_e = statistics.fmean(energies)
    sd_e = statistics.stdev(energies) if len(energies) > 1 else 0.0
    return (
        f"{name:<22} n={len(pulses):<4} "
        f"energy {mean_e:9.2f} ± {sd_e:6.2f} µJ   "
        f"width {statistics.fmean(durations):8.2f} ms   "
        f"current {statistics.fmean(currents):8.2f} µA"
    )


def main() -> None:
    """Parse the CSV, split pulses per channel, print the report."""
    ap = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    ap.add_argument("csv_path", help="GUI-parity capture CSV")
    ap.add_argument("--vdd", type=float, default=3.0, help="DUT VDD in volts (default 3.0)")
    ap.add_argument(
        "--name",
        action="append",
        default=[],
        metavar="CH=LABEL",
        help="label a channel, e.g. --name 2=wakeup (repeatable)",
    )
    ap.add_argument(
        "--power-on-ua",
        type=float,
        default=POWER_ON_UA,
        help="rail-up threshold in µA — leading samples below it are trimmed as "
        "unpowered; lower it for DUTs that wake below 200 µA, 0 disables (default 200)",
    )
    args = ap.parse_args()

    names: dict[int, str] = {}
    for spec in args.name:
        ch_s, sep, label = spec.partition("=")
        if not sep or not label or not ch_s.isdigit() or int(ch_s) > 7:
            ap.error(f"--name expects CH=LABEL with CH 0..7, got {spec!r}")
        names[int(ch_s)] = label

    rows = load_rows(Path(args.csv_path))
    if not rows:
        raise SystemExit("empty capture")

    # Boot-inclusive captures begin before the rail comes up; while the
    # DUT is unpowered its logic reference floats and the pins read as
    # garbage. Start attribution at the first sample with real current.
    if args.power_on_ua > 0:
        power_i = next((i for i, r in enumerate(rows) if r[1] > args.power_on_ua), 0)
        if power_i:
            print(f"pre-power region skipped: {rows[power_i][0] / 1000.0:.3f} s")
            rows = rows[power_i:]

    sync: dict[int, list[Pulse]] = {}
    regions: dict[int, list[Pulse]] = {}
    for ch in range(8):
        pulses = collect_pulses(rows, ch)
        s = [p for p in pulses if p.duration_s < SYNC_PULSE_MAX_S]
        r = [p for p in pulses if p.duration_s >= SYNC_PULSE_MAX_S]
        if s:
            sync[ch] = s
        if r:
            regions[ch] = r

    total_s = (rows[-1][0] - rows[0][0]) / 1000.0
    # Idle floor: exclude the boot region (rail-up to the first marked
    # region), which otherwise pollutes the stats with boot current.
    boot_end_ms = first_region_start_ms(rows)
    idle_ua = [ua for t, ua, levels in rows if t > boot_end_ms and not levels]

    print(f"capture: {len(rows)} samples, {total_s:.2f} s, VDD {args.vdd:.2f} V")
    for ch in sorted(set(sync) | set(regions)):
        label = f"D{ch} {names.get(ch, '')}".rstrip()
        if ch in sync:
            first = sync[ch][0]
            print(f"{label}: sync burst, {len(sync[ch])} short pulses (t={first.start_s:.3f} s)")
        if ch in regions:
            print(stats_line(label, regions[ch], args.vdd))
    if idle_ua:
        print(
            f"{'idle (no marker)':<22} median "
            f"{statistics.median(idle_ua):9.2f} µA   mean {statistics.fmean(idle_ua):9.2f} µA"
        )


if __name__ == "__main__":
    main()
