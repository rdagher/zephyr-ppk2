#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0 OR MIT
"""Charge of a BLE advertising event, above the baseline, in a capture of samples/ble_advertising.

An event is three radio pulses on D0. Its charge is taken from 3 ms
before the first pulse to 4 ms after it, less the baseline: the median
current away from any event. Events next to a sensor read are left out.

    python evidence/event_charge.py evidence/ble_advertising.csv.xz
"""

import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from attribute import SAMPLE_PERIOD_S, load_rows, powered, regions

BEFORE, AFTER, CLEAR = 300, 400, 800  # samples of 10 µs
LEAK_UA = 20_000  # a sample this far above the baseline is a leaked range-switch reading


def figures(path: Path) -> str:
    """The baseline and the charge per event of one capture."""
    rows = powered(load_rows(path))
    t0 = rows[0][0]
    ua = [row[1] for row in rows]
    starts = {
        ch: [round((r.start_s * 1000.0 - t0) * 100) for r in regions(rows, ch)] for ch in (0, 1)
    }
    pulses = [p for p in starts[0] if p > 200_000]
    events = [p for k, p in enumerate(pulses) if k == 0 or p - pulses[k - 1] > 500]
    busy = set()
    for start in events:
        busy.update(range(start - 500, start + 500))
    for start in starts[1]:
        busy.update(range(start - 500, start + 2500))
    baseline = statistics.median(u for i, u in enumerate(ua) if i > 200_000 and i not in busy)
    charges, leaks = [], 0
    for start in events:
        if start + AFTER >= len(ua) or any(abs(start - s) < CLEAR + 1700 for s in starts[1]):
            continue
        window = ua[start - BEFORE : start + AFTER]
        charges.append(sum(u - baseline for u in window) * SAMPLE_PERIOD_S)
        leaks += max(window[: BEFORE - 20]) - baseline > LEAK_UA
    return (
        f"{path.name}: baseline {baseline:.1f} µA, {len(charges)} events, "
        f"charge {statistics.fmean(charges):.2f} ± {statistics.stdev(charges):.2f} µC "
        f"(median {statistics.median(charges):.2f}), with a leaked sample: {leaks}"
    )


def main() -> None:
    """Print the figures of each capture given."""
    for path in sys.argv[1:]:
        print(figures(Path(path)))


if __name__ == "__main__":
    main()
