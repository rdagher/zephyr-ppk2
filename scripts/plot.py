#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0 OR MIT
"""Plot a capture: the current, the marked channels under it, and their figures.

Needs matplotlib and numpy, which the other scripts do not:

    uv run --with matplotlib --with numpy scripts/plot.py trace.csv \\
        --name 0=cycle --name 1=wakeup --window 2.0 3.4 --out cycle.png
"""

import argparse
import statistics
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from attribute import POWER_ON_UA, load_rows, powered, regions

# One colour per channel, in this order whatever is plotted. Checked for
# colour-vision deficiency; names are always written out as well.
COLOURS = ("#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948")
SURFACE, INK, MUTED, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e4e3df"
BINS = 4000  # the trace is drawn as the lowest and highest sample of each bin


def unit(ua: float) -> str:
    """A current with the unit that fits it."""
    return f"{ua / 1000:.2f} mA" if ua >= 1000 else f"{ua:.1f} µA"


def main() -> None:
    """Draw the figure."""
    ap = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    ap.add_argument("csv_path", type=Path)
    ap.add_argument("--name", action="append", default=[], metavar="CH=LABEL")
    ap.add_argument("--window", nargs=2, type=float, metavar=("START", "END"), help="seconds")
    ap.add_argument("--title", default="")
    ap.add_argument("--out", type=Path, default=Path("capture.png"))
    ap.add_argument("--power-on-ua", type=float, default=POWER_ON_UA, help="as in attribute.py")
    args = ap.parse_args()
    names = {int(ch): label for ch, _, label in (spec.partition("=") for spec in args.name)}

    rows = powered(load_rows(args.csv_path), args.power_on_ua)
    t0 = rows[0][0] / 1000.0
    found = {ch: r for ch in range(8) if (r := regions(rows, ch))}
    start, end = args.window or (0.0, rows[-1][0] / 1000.0 - t0)
    shown = [(t / 1000.0 - t0, ua) for t, ua, _ in rows if start <= t / 1000.0 - t0 <= end]
    ms = (end - start) < 0.5  # a short window reads better in milliseconds
    scale = 1000.0 if ms else 1.0

    plt.rcParams.update(
        {
            "font.size": 10,
            "axes.edgecolor": GRID,
            "text.color": INK,
            "axes.labelcolor": MUTED,
            "xtick.color": MUTED,
            "ytick.color": MUTED,
        }
    )
    fig = plt.figure(figsize=(11, 6.6), facecolor=SURFACE)
    grid = fig.add_gridspec(
        4, 1, height_ratios=(3.2, 0.34 * len(found) + 0.2, 0.45, 1.5), hspace=0.12
    )
    ax, lanes, _, table = (fig.add_subplot(g) for g in grid)
    _.axis("off")

    # The current: the envelope of each bin, so that no peak is lost.
    ua = np.maximum(np.array([u for _, u in shown]), 0.1)
    width = max(1, len(ua) // BINS)
    binned = ua[: len(ua) // width * width].reshape(-1, width)
    x = (np.linspace(start, end, len(binned)) - start) * scale
    ax.fill_between(x, binned.min(axis=1), binned.max(axis=1), color=MUTED, linewidth=0.6)
    ax.set_yscale("log")
    ax.set_ylabel("current (µA)")
    ax.set_facecolor(SURFACE)
    ax.grid(True, which="major", color=GRID, linewidth=0.6)
    ax.tick_params(labelbottom=False, length=0)
    ax.set_title(args.title, loc="left", fontsize=12, color=INK, pad=10)

    # One lane per channel, named on the left.
    for lane, (ch, items) in enumerate(found.items()):
        spans = [((r.start_s - t0 - start) * scale, r.duration_s * scale) for r in items]
        lanes.broken_barh(spans, (-lane - 0.36, 0.72), color=COLOURS[ch], linewidth=0)
    lanes.set_yticks(
        [-i for i in range(len(found))],
        [f"D{ch} {names.get(ch, '')}".rstrip() for ch in found],
        color=INK,
    )
    lanes.set_ylim(-len(found) + 0.4, 0.6)
    lanes.set_xlabel("time (ms)" if ms else "time (s)")
    lanes.set_facecolor(SURFACE)
    lanes.tick_params(length=0)
    for side in ("top", "right", "left"):
        lanes.spines[side].set_visible(False)
        ax.spines[side].set_visible(False)
    for axis in (ax, lanes):
        axis.set_xlim(0, (end - start) * scale)

    # The figures of every region of the capture, not only of the window,
    # in the order of the lanes.
    table.axis("off")
    cells = [
        [
            f"D{ch} {names.get(ch, '')}".rstrip(),
            str(len(items)),
            f"{statistics.fmean(r.duration_s for r in items) * 1000:.3f} ms",
            unit(statistics.fmean(r.mean_ua for r in items)),
            unit(max(r.peak_ua for r in items)),
            f"{statistics.fmean(r.charge_uc for r in items):.3f} µC",
        ]
        for ch, items in found.items()
    ]
    if not cells:
        table.text(0.5, 0.5, "no marked region in this capture", ha="center", color=MUTED)
    else:
        drawn = table.table(
            cells,
            loc="center",
            cellLoc="right",
            colLoc="right",
            edges="horizontal",
            colLabels=["channel", "regions", "width", "mean current", "peak", "charge"],
        )
        drawn.auto_set_font_size(False)
        drawn.set_fontsize(10)
        drawn.scale(1, 1.35)
        for (row, col), cell in drawn.get_celld().items():
            cell.set_edgecolor(GRID)
            cell.get_text().set_color(MUTED if row == 0 else INK)
            if col == 0:
                cell.get_text().set_ha("left")

    fig.savefig(args.out, dpi=150, facecolor=SURFACE, bbox_inches="tight")
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
