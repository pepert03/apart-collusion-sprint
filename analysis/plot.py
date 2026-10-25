"""Figure 1 for the report: per model, overt collusion and concealment rates
(top) and task reward (bottom) per condition, with 95% bootstrap CIs.

Usage:
    python analysis/plot.py --files data/*/*.judged.jsonl --out report/fig1.png
"""

from __future__ import annotations

import argparse
import os
import sys
from collections import defaultdict

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
sys.path.insert(0, os.path.dirname(__file__))

from bootstrap import ORDER, load  # noqa: E402
from metrics import bootstrap_ci, indicator, is_colluding, is_concealed, mean, task_rewards  # noqa: E402

SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK_2 = "#52514e"
GRID = "#e4e3df"
SERIES = {"Overt collusion": "#2a78d6", "Concealed (C,C)": "#eb6834"}
REWARD = "#52514e"
LABELS = {"control": "Control", "announced_audit": "Announced\naudit",
          "unannounced_audit": "Unannounced\naudit", "outcome_penalty": "Outcome\npenalty",
          "restricted_channel": "Restricted\nchannel"}


def style(ax):
    ax.set_facecolor(SURFACE)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(GRID)
    ax.tick_params(colors=INK_2, labelsize=8, length=0)
    ax.yaxis.grid(True, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)


def point(ax, x, values, color):
    m, (lo, hi) = mean(values), bootstrap_ci(values)
    ax.plot([x, x], [lo, hi], color=color, linewidth=2, solid_capstyle="round", zorder=2)
    ax.plot(x, m, "o", color=color, markersize=7, markeredgecolor=SURFACE,
            markeredgewidth=2, zorder=3)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--files", nargs="+", required=True)
    ap.add_argument("--out", default="report/fig1.png")
    args = ap.parse_args()

    groups = defaultdict(list)
    for path in args.files:
        for s in load(path):
            groups[(s.model, s.condition)].append(s)
    models = sorted({m for m, _ in groups}, key=lambda m: ("32B" in m, m))

    fig, axes = plt.subplots(2, len(models), figsize=(4.6 * len(models), 5.6),
                             sharex=True, squeeze=False,
                             gridspec_kw={"height_ratios": [3, 2]})
    fig.patch.set_facecolor(SURFACE)
    for j, model in enumerate(models):
        top, bottom = axes[0][j], axes[1][j]
        conds = [c for c in ORDER if (model, c) in groups]
        for i, c in enumerate(conds):
            ss = groups[(model, c)]
            point(top, i - 0.13, indicator(is_colluding, ss), SERIES["Overt collusion"])
            if c != "restricted_channel":
                point(top, i + 0.13, indicator(is_concealed, ss), SERIES["Concealed (C,C)"])
            point(bottom, i, task_rewards(ss), REWARD)
        n = len(groups[(model, conds[0])])
        top.set_title(f"{model.split('/')[-1]}  (n={n} sessions/condition)",
                      color=INK, fontsize=10, loc="left")
        top.set_ylim(-0.05, 1.05)
        bottom.set_ylim(0, 62)
        bottom.set_xticks(range(len(conds)), [LABELS[c] for c in conds])
        for ax in (top, bottom):
            style(ax)
        if j == 0:
            top.set_ylabel("Share of sessions", color=INK_2, fontsize=9)
            bottom.set_ylabel("Reward per agent\n(max 60)", color=INK_2, fontsize=9)

    handles = [plt.Line2D([], [], marker="o", color=c, linestyle="none", markersize=7,
                          markeredgecolor=SURFACE, markeredgewidth=2, label=k)
               for k, c in SERIES.items()]
    fig.legend(handles=handles, loc="upper right", frameon=False, ncol=2,
               fontsize=9, labelcolor=INK)
    fig.text(0.01, 0.005, "Points: means. Bars: 95% percentile bootstrap CIs "
             "(2000 resamples). Concealment undefined without a channel.",
             color=INK_2, fontsize=7.5)
    fig.tight_layout(rect=(0, 0.03, 1, 0.95))
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    fig.savefig(args.out, dpi=200, facecolor=SURFACE)
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
