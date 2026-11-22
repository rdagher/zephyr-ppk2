#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0 OR MIT
"""Width, current and charge of the regions marked on D0..D7 of a capture.

Reads a capture in the CSV format of Nordic's Power Profiler app, from
``ppk2 capture`` or exported from the app, plain or compressed (``.gz``,
``.xz``), at 100,000 samples per second: an export at a lower rate is
refused. A region is a stretch where a channel is high.

The charge of a region is the integral of its current: each row is one
10 µs sample. The PPK2 measures current only. With ``--vdd`` an energy
is added, as charge times that voltage: an estimate that holds as far
as the supply voltage is constant.

Usage:
    python attribute.py trace.csv --name 0=cycle --name 1=wakeup
    python attribute.py trace.csv --vdd 3.3
"""

import argparse
import csv
import gzip
import lzma
import statistics
from dataclasses import dataclass
from pathlib import Path

SAMPLE_PERIOD_S = 10e-6  # the PPK2 sends 100,000 samples per second
POWER_ON_UA = 200.0  # below this the DUT is taken as unpowered

Row = tuple[float, float, int]  # timestamp in ms, current in µA, D0..D7 as bits


@dataclass
class Region:
    """One stretch where a channel is high."""

    start_s: float
    duration_s: float
    charge_uc: float
    peak_ua: float

    @property
    def mean_ua(self) -> float:
        """Mean current over the region, in µA."""
        return self.charge_uc / self.duration_s


def load_rows(path: Path) -> list[Row]:
    """Read a capture. Exits when its rows are not 10 µs apart."""
    opener = {".gz": gzip.open, ".xz": lzma.open}.get(path.suffix, open)
    with opener(path, "rt", newline="") as f:
        rows = [
            (
                float(rec["Timestamp(ms)"]),
                float(rec["Current(uA)"]),
                sum(1 << i for i in range(8) if rec[f"D{i}"] == "1"),
            )
            for rec in csv.DictReader(f)
        ]
    if len(rows) > 1:
        # The charge counts 10 µs per row, so any other rate would give a wrong one.
        step_s = (rows[-1][0] - rows[0][0]) / 1000.0 / (len(rows) - 1)
        if abs(step_s - SAMPLE_PERIOD_S) > 0.01 * SAMPLE_PERIOD_S:
            raise SystemExit(
                f"error: {path}: rows are {step_s * 1e6:.1f} µs apart on average, not 10: "
                "a capture at 100,000 samples per second is needed"
            )
    return rows


def powered(rows: list[Row], threshold_ua: float = POWER_ON_UA) -> list[Row]:
    """The rows from power-on. Before it the digital inputs float and mean nothing.

    Exits when no sample is above the threshold: nothing in such a
    capture can be told apart from an unpowered DUT.
    """
    start = next((i for i, row in enumerate(rows) if row[1] > threshold_ua), None)
    if start is None:
        raise SystemExit(
            f"error: no sample above {threshold_ua:g} µA: the DUT was not powered. "
            "For a DUT that draws less, pass --power-on-ua"
        )
    return rows[start:]


def regions(rows: list[Row], channel: int) -> list[Region]:
    """The complete regions of ``channel``: those that start and end inside the capture."""
    found: list[Region] = []
    high = seen_low = False
    start_s = charge_uc = peak_ua = 0.0
    for t_ms, ua, levels in rows:
        level = (levels >> channel) & 1
        if level and not high and seen_low:
            high, start_s, charge_uc, peak_ua = True, t_ms / 1000.0, 0.0, 0.0
        if high and level:
            charge_uc += ua * SAMPLE_PERIOD_S
            peak_ua = max(peak_ua, ua)
        if not level:
            seen_low = True
            if high:
                high = False
                found.append(Region(start_s, t_ms / 1000.0 - start_s, charge_uc, peak_ua))
    return found


def idle(rows: list[Row]) -> list[float]:
    """The currents with no channel high, from the first region on.

    When no channel is ever high, all of them.
    """
    first = next((i for i, row in enumerate(rows) if row[2]), 0)
    return [ua for _, ua, levels in rows[first:] if not levels]


def report_line(label: str, found: list[Region], vdd_v: float | None) -> str:
    """One line of the report for one channel."""
    charges = [r.charge_uc for r in found]
    charge = statistics.fmean(charges)
    spread = statistics.stdev(charges) if len(found) > 1 else 0.0
    line = (
        f"{label:<22} n={len(found):<5} "
        f"width {statistics.fmean(r.duration_s for r in found) * 1000:9.3f} ms  "
        f"avg {statistics.fmean(r.mean_ua for r in found):9.2f} µA  "
        f"peak {max(r.peak_ua for r in found):8.0f} µA  "
        f"charge {charge:9.3f} ± {spread:.3f} µC (median {statistics.median(charges):.3f})"
    )
    if vdd_v is not None:
        line += f"  energy {charge * vdd_v:9.3f} µJ"
    return line


def main() -> None:
    """Print the report of a capture."""
    ap = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    ap.add_argument("csv_path", type=Path, help="a capture in the app's CSV format")
    ap.add_argument("--vdd", type=float, help="supply voltage in volts: adds an energy column")
    ap.add_argument(
        "--name",
        action="append",
        default=[],
        metavar="CH=LABEL",
        help="name a channel, as in --name 2=wakeup (repeatable)",
    )
    ap.add_argument(
        "--power-on-ua",
        type=float,
        default=POWER_ON_UA,
        help="current above which the DUT counts as powered (default 200)",
    )
    args = ap.parse_args()

    names: dict[int, str] = {}
    for spec in args.name:
        ch, sep, label = spec.partition("=")
        if not sep or not label or ch not in "01234567" or len(ch) != 1:
            ap.error(f"--name expects CH=LABEL with CH from 0 to 7, got {spec!r}")
        names[int(ch)] = label

    rows = powered(load_rows(args.csv_path), args.power_on_ua)

    print(f"capture: {len(rows)} samples, {(rows[-1][0] - rows[0][0]) / 1000.0:.2f} s powered")
    if args.vdd is not None:
        print(f"energy: charge times {args.vdd:.2f} V, taken as constant")
    for ch in range(8):
        found = regions(rows, ch)
        if found:
            print(report_line(f"D{ch} {names.get(ch, '')}".rstrip(), found, args.vdd))
    idle_ua = idle(rows)
    if idle_ua:
        print(
            f"{'idle (no channel high)':<22} median {statistics.median(idle_ua):9.2f} µA  "
            f"mean {statistics.fmean(idle_ua):9.2f} µA"
        )


if __name__ == "__main__":
    main()
