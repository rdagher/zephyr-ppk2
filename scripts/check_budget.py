#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0 OR MIT
"""Exit 1 when the mean over the regions of a channel, or the idle current, exceeds a budget.

    python check_budget.py trace.csv --channel 0 --max-uc 700 --max-ms 1025 --idle-max-ua 5.2

An energy budget (``--max-uj``) needs ``--vdd``: the energy is the
charge times that voltage.
"""

import argparse
import statistics
import sys
from pathlib import Path

from attribute import POWER_ON_UA, idle, load_rows, powered, regions, volts


def main() -> int:
    """Check the budgets; return the exit code."""
    ap = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    ap.add_argument("csv_path", type=Path, help="a capture in the app's CSV format")
    ap.add_argument("--channel", type=int, choices=range(8), default=0, metavar="{0..7}")
    ap.add_argument("--max-ua", type=float, help="mean current of a region, in µA")
    ap.add_argument("--max-peak-ua", type=float, help="highest sample of any region, in µA")
    ap.add_argument("--max-uc", type=float, help="mean charge of a region, in µC")
    ap.add_argument("--max-ms", type=float, help="mean width of a region, in ms")
    ap.add_argument("--max-uj", type=float, help="mean energy of a region, in µJ; needs --vdd")
    ap.add_argument("--idle-max-ua", type=float, help="median current with no channel high")
    ap.add_argument("--vdd", type=volts, help="supply voltage in volts, for --max-uj")
    ap.add_argument("--power-on-ua", type=float, default=POWER_ON_UA, help="as in attribute.py")
    args = ap.parse_args()
    if args.max_uj is not None and args.vdd is None:
        ap.error("--max-uj needs --vdd")

    rows = powered(load_rows(args.csv_path), args.power_on_ua)
    found = regions(rows, args.channel)
    idle_ua = idle(rows)
    mean = statistics.fmean
    # (budget, what it limits, unit, the measured value)
    checks = (
        (args.max_ua, "mean region current", "µA", lambda: mean(r.mean_ua for r in found)),
        (args.max_peak_ua, "highest region peak", "µA", lambda: max(r.peak_ua for r in found)),
        (args.max_uc, "mean region charge", "µC", lambda: mean(r.charge_uc for r in found)),
        (args.max_ms, "mean region width", "ms", lambda: mean(r.duration_s for r in found) * 1000),
        (
            args.max_uj,
            "mean region energy",
            "µJ",
            lambda: mean(r.charge_uc for r in found) * args.vdd,
        ),
        (args.idle_max_ua, "idle median", "µA", lambda: statistics.median(idle_ua)),
    )
    if all(budget is None for budget, *_ in checks):
        ap.error("give at least one budget")

    failed = False
    for budget, what, unit, measure in checks:
        if budget is None:
            continue
        if not (idle_ua if what.startswith("idle") else found):
            print(f"FAIL {what}: nothing to measure on D{args.channel}")
            failed = True
            continue
        value = measure()
        ok = value <= budget
        print(f"{'PASS' if ok else 'FAIL'} {what} {value:.2f} {unit} (budget {budget:.2f} {unit})")
        failed |= not ok
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
