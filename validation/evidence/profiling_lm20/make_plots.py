#!/usr/bin/env python3
"""Regenerate the CLI-vs-GUI parity plot from the committed captures.

Overlays both traces on a log current axis (aligned at the first
cycle's rising edge) plus ECDFs for the cycle region and the idle
floor — the eyeball version of the report numbers.

Run from the zephyr-ppk2 root (matplotlib is not a dependency)::

    uv run --with matplotlib python validation/evidence/profiling_lm20/make_plots.py
"""

import sys
from pathlib import Path

import matplotlib.pyplot as plt

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parents[2] / "scripts"))
from attribute import POWER_ON_UA, SYNC_PULSE_MAX_S, collect_pulses, load_rows

CAPTURES = [
    ("CLI", HERE / "captures/profiling_lm20_cli.csv.gz", "tab:blue"),
    ("GUI", HERE / "captures/profiling_lm20_gui.csv.gz", "tab:orange"),
]
STRIDE = 20  # plot every Nth sample; ECDFs use every 10th


def aligned(path):
    """Rows with t=0 at the first cycle's rising edge, pre-power trimmed."""
    rows = load_rows(path)
    i = next((i for i, r in enumerate(rows) if r[1] > POWER_ON_UA), 0)
    rows = rows[i:]
    cycles = [p for p in collect_pulses(rows, 0) if p.duration_s >= SYNC_PULSE_MAX_S]
    t0 = cycles[0].start_s * 1000.0
    return [(t - t0, ua, lv) for t, ua, lv in rows if t >= t0]


def ecdf(ax, values, label, color):
    xs = sorted(values[::10])
    ax.plot(xs, [i / len(xs) for i in range(len(xs))], label=label, color=color, lw=1)


def main() -> None:
    fig, (ax_tr, ax_cy, ax_id) = plt.subplots(
        3, 1, figsize=(9, 9), gridspec_kw={"height_ratios": [2, 1, 1]}
    )
    for label, path, color in CAPTURES:
        rows = aligned(path)
        ax_tr.plot(
            [t / 1000.0 for t, _, _ in rows[::STRIDE]],
            [max(ua, 0.1) for _, ua, _ in rows[::STRIDE]],
            label=label, color=color, lw=0.4, alpha=0.8,
        )
        ecdf(ax_cy, [ua for _, ua, lv in rows if lv & 1], label, color)
        ecdf(ax_id, [ua for _, ua, lv in rows if not lv], label, color)

    ax_tr.set_yscale("log")
    ax_tr.set_xlabel("time from first cycle edge (s)")
    ax_tr.set_ylabel("current (µA)")
    ax_tr.set_title("profiling sample, nRF54LM20DK ammeter 3.3 V — CLI vs GUI")
    ax_cy.set_title("ECDF: cycle region (D0 high)")
    ax_cy.set_xscale("log")
    ax_id.set_title("ECDF: idle (no marker)")
    ax_id.set_xscale("log")
    for ax in (ax_tr, ax_cy, ax_id):
        ax.legend(loc="lower right", fontsize=8)
    fig.tight_layout()
    out = HERE / "plots/profiling_lm20_parity.png"
    fig.savefig(out, dpi=110)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
