#!/usr/bin/env python3
"""Fail (exit 1) when a capture exceeds its energy, width, current or idle budgets.

CI gate on top of attribute.py's region logic:

    python check_budget.py trace.csv --vdd 3.3 --channel 0 \\
        --workload-max-uj 2300 --workload-max-ms 1025 --idle-max-ua 5.2
"""

import argparse
import statistics
import sys
from pathlib import Path

from attribute import (
    POWER_ON_UA,
    SYNC_PULSE_MAX_S,
    collect_pulses,
    first_region_start_ms,
    load_rows,
)


def main() -> int:
    """Evaluate the budgets against the capture; return the exit code."""
    ap = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    ap.add_argument("csv_path", help="GUI-parity capture CSV")
    ap.add_argument("--vdd", type=float, default=3.0, help="DUT VDD in volts (default 3.0)")
    ap.add_argument(
        "--channel",
        type=int,
        choices=range(8),
        metavar="{0..7}",
        default=0,
        help="workload marker channel (default 0)",
    )
    ap.add_argument("--workload-max-uj", type=float, help="max mean workload energy in µJ")
    ap.add_argument("--workload-max-ms", type=float, help="max mean workload width in ms")
    ap.add_argument("--workload-max-ua", type=float, help="max mean workload current in µA")
    ap.add_argument("--workload-max-peak-ua", type=float, help="max peak workload current in µA")
    ap.add_argument("--idle-max-ua", type=float, help="max median idle current in µA")
    ap.add_argument(
        "--power-on-ua",
        type=float,
        default=POWER_ON_UA,
        help="rail-up trim threshold in µA, 0 disables (default 200)",
    )
    args = ap.parse_args()

    budgets = (
        args.workload_max_uj,
        args.workload_max_ms,
        args.workload_max_ua,
        args.workload_max_peak_ua,
        args.idle_max_ua,
    )
    if all(b is None for b in budgets):
        ap.error("at least one budget option is required")

    rows = load_rows(Path(args.csv_path))
    if not rows:
        print("FAIL empty capture")
        return 1

    # Skip the unpowered pre-rail region (logic pins float there).
    if args.power_on_ua > 0:
        power_i = next((i for i, r in enumerate(rows) if r[1] > args.power_on_ua), 0)
        rows = rows[power_i:]

    pulses = collect_pulses(rows, args.channel)
    workloads = [p for p in pulses if p.duration_s >= SYNC_PULSE_MAX_S]
    boot_end_ms = first_region_start_ms(rows)
    idle_ua = [ua for t, ua, levels in rows if t > boot_end_ms and not levels]

    failed = False
    if args.workload_max_uj is not None:
        if not workloads:
            print("FAIL no workloads on the channel — cannot check workload budget")
            failed = True
        else:
            mean_uj = statistics.fmean(p.energy_uj(args.vdd) for p in workloads)
            ok = mean_uj <= args.workload_max_uj
            print(
                f"{'PASS' if ok else 'FAIL'} workload mean "
                f"{mean_uj:.1f} µJ (budget {args.workload_max_uj:.1f} µJ, n={len(workloads)})"
            )
            failed |= not ok
    if args.workload_max_ms is not None:
        if not workloads:
            print("FAIL no workloads on the channel — cannot check width budget")
            failed = True
        else:
            mean_ms = statistics.fmean(p.duration_s * 1000.0 for p in workloads)
            ok = mean_ms <= args.workload_max_ms
            print(
                f"{'PASS' if ok else 'FAIL'} workload width "
                f"{mean_ms:.1f} ms (budget {args.workload_max_ms:.1f} ms, n={len(workloads)})"
            )
            failed |= not ok
    if args.workload_max_ua is not None:
        if not workloads:
            print("FAIL no workloads on the channel — cannot check current budget")
            failed = True
        else:
            mean_ua = statistics.fmean(p.mean_current_ua() for p in workloads)
            ok = mean_ua <= args.workload_max_ua
            print(
                f"{'PASS' if ok else 'FAIL'} workload current "
                f"{mean_ua:.1f} µA (budget {args.workload_max_ua:.1f} µA, n={len(workloads)})"
            )
            failed |= not ok
    if args.workload_max_peak_ua is not None:
        if not workloads:
            print("FAIL no workloads on the channel — cannot check peak budget")
            failed = True
        else:
            peak_ua = max(p.peak_ua for p in workloads)
            ok = peak_ua <= args.workload_max_peak_ua
            print(
                f"{'PASS' if ok else 'FAIL'} workload peak "
                f"{peak_ua:.1f} µA (budget {args.workload_max_peak_ua:.1f} µA, n={len(workloads)})"
            )
            failed |= not ok
    if args.idle_max_ua is not None:
        if not idle_ua:
            print("FAIL no idle samples found — cannot check idle budget")
            failed = True
        else:
            median_ua = statistics.median(idle_ua)
            ok = median_ua <= args.idle_max_ua
            print(
                f"{'PASS' if ok else 'FAIL'} idle median "
                f"{median_ua:.2f} µA (budget {args.idle_max_ua:.2f} µA)"
            )
            failed |= not ok
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
