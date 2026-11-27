#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0 OR MIT
"""Tell which digital input of the PPK2 sees which channel, from the wiring check at boot.

    python check_wiring.py trace.csv --name 1=wakeup --name 2=measure

The firmware is built with ``CONFIG_PPK2_TRACE_WIRING_CHECK=y``: at boot
it holds each wired channel high in turn, channel n for n + 1 ms, three
times over. The capture must start at power-on, as ``ppk2 capture``
does. A named channel is expected on its own input; one named ``radio``
is skipped, since the hardware drives it. Exits 1 when a channel is on
another input, on several, or on none.
"""

import argparse
import sys
from pathlib import Path

from attribute import POWER_ON_UA, Region, load_rows, powered, regions

ROUNDS = 3  # how many times the firmware holds each channel high
TOLERANCE_MS = 0.25  # how far a width may be from its channel's
SPAN_S = 0.2  # the rounds of eight channels last 0.16 s at most


def carried(found: list[Region]) -> int | None:
    """The channel whose width the first regions of an input have, or None.

    The check is three regions of the same width, close together. The
    regions of an application are further apart: a sensor read of 5 ms
    once a second is not channel 4.
    """
    first = found[:ROUNDS]
    if len(first) < ROUNDS:
        return None
    ms = round(first[0].duration_s * 1000.0)
    if not 1 <= ms <= 8 or any(abs(r.duration_s * 1000.0 - ms) > TOLERANCE_MS for r in first):
        return None
    if first[-1].start_s + first[-1].duration_s - first[0].start_s > SPAN_S:
        return None
    return ms - 1


def main() -> int:
    """Print where each channel is seen; return the exit code."""
    ap = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    ap.add_argument("csv_path", type=Path, help="a capture from power-on, in the app's CSV format")
    ap.add_argument(
        "--name",
        action="append",
        default=[],
        metavar="CH=LABEL",
        help="name a channel and expect it, as in --name 2=wakeup (repeatable)",
    )
    ap.add_argument(
        "--power-on-ua",
        type=float,
        default=POWER_ON_UA,
        help="current in µA above which the DUT counts as powered (default 200)",
    )
    args = ap.parse_args()

    names: dict[int, str] = {}
    for spec in args.name:
        ch, sep, label = spec.partition("=")
        if not sep or not label or ch not in "01234567" or len(ch) != 1:
            ap.error(f"--name expects CH=LABEL with CH from 0 to 7, got {spec!r}")
        names[int(ch)] = label

    rows = powered(load_rows(args.csv_path), args.power_on_ua)
    inputs: dict[int, list[int]] = {}  # channel -> the inputs that carry its width
    for d in range(8):
        ch = carried(regions(rows, d))
        if ch is not None:
            inputs.setdefault(ch, []).append(d)
    if not inputs:
        print(
            "FAIL no wiring check in this capture: build with "
            "CONFIG_PPK2_TRACE_WIRING_CHECK=y and capture from power-on"
        )
        return 1

    failed = False
    for ch in sorted(set(names) | set(inputs)):
        label = f"D{ch} {names.get(ch, '')}".rstrip()
        seen = inputs.get(ch, [])
        if names.get(ch) == "radio" and not seen:
            print(f"SKIP {label}: driven by the hardware")
        elif seen == [ch]:
            print(f"PASS {label}: on D{ch}")
        elif not seen:
            print(f"FAIL {label}: not seen on any input")
            failed = True
        else:
            print(f"FAIL {label}: on {' and '.join(f'D{d}' for d in seen)}")
            failed = True
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
