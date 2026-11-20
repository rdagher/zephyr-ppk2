#!/usr/bin/env python3
"""Trim a capture to N whole cycles, aligned at the first cycle edge.

Non-simultaneous captures slice the periodic workload differently, so
whole-capture stats disagree even when the instruments agree; trimming
both to the same marker-aligned window makes them comparable.

Usage:
    python trim_cycles.py in.csv[.gz] out.csv [--cycles 9] [--channel 0]
"""

import argparse
import gzip
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[3] / "scripts"))
from attribute import POWER_ON_UA, SYNC_PULSE_MAX_S, collect_pulses, load_rows


def main() -> None:
    ap = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    ap.add_argument("src")
    ap.add_argument("dst")
    ap.add_argument("--cycles", type=int, default=9)
    ap.add_argument("--channel", type=int, default=0)
    args = ap.parse_args()

    rows = load_rows(Path(args.src))
    i = next((i for i, r in enumerate(rows) if r[1] > POWER_ON_UA), 0)
    rows = rows[i:]
    cycles = [p for p in collect_pulses(rows, args.channel) if p.duration_s >= SYNC_PULSE_MAX_S]
    if len(cycles) <= args.cycles:
        raise SystemExit(f"only {len(cycles)} cycles in capture, need {args.cycles + 1}")
    t0 = cycles[0].start_s * 1000.0
    t1 = cycles[args.cycles].start_s * 1000.0

    opener = gzip.open if args.src.endswith(".gz") else open
    with opener(args.src, "rt", newline="") as f, open(args.dst, "w") as g:
        g.write(f.readline())
        for line in f:
            t = float(line.split(",", 1)[0])
            if t0 <= t < t1:
                g.write(line)
    print(f"{args.dst}: {args.cycles} cycles, {t1 - t0:.1f} ms")


if __name__ == "__main__":
    main()
