"""Preprint figure 2 at paper size (the poster's chart has 26 px poster text and is too big in the paper):

    python src/plot_preprint_figs.py      # -> docs/figures/preprint_ladder.png

Same data as the poster's chart (`results/ocr_ladder/downstream.csv`, 24 OCR versions, expert left out):
value F1 against the share of gold names intact after OCR, one panel per book, dashed line y = x.
"""
from __future__ import annotations

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402
from scipy.stats import spearmanr  # noqa: E402

from common import ROOT  # noqa: E402

OUT = ROOT / "docs" / "figures" / "preprint_ladder.png"
INK, SOFT, FAINT, RULE = "#15201c", "#4d5a55", "#6f7b76", "#d9dee6"
COL = {"Butler": "#2a78d6", "Reeve": "#eb6834"}            # same colours as the poster
FS = 9.5

plt.rcParams.update({"font.family": ["Helvetica Neue", "Helvetica", "FreeSans", "DejaVu Sans"],
                     "font.size": FS, "axes.edgecolor": SOFT, "axes.labelcolor": SOFT,
                     "xtick.color": SOFT, "ytick.color": SOFT, "axes.spines.top": False,
                     "axes.spines.right": False})


def main() -> None:
    d = pd.read_csv(ROOT / "results" / "ocr_ladder" / "downstream.csv")
    d = d[d.ocr != "expert"]
    fig, axes = plt.subplots(1, 2, figsize=(6.6, 2.9), sharey=True)
    for ax, book in zip(axes, ("Butler", "Reeve")):
        x = d[d.book == book]
        rho = spearmanr(x.preserved, x.value_F1).statistic
        ax.plot([0.5, 1.0], [0.5, 1.0], color=FAINT, lw=0.9, ls=(0, (3, 3)), zorder=1)
        ax.scatter(x.preserved, x.value_F1, s=26, color=COL[book], edgecolor="white", lw=0.7, zorder=3)
        leg = x[x.ocr.str.startswith("legacy")]
        for r in leg.itertuples():
            ax.annotate("legacy OCR", (r.preserved, r.value_F1), xytext=(6, -2), textcoords="offset points",
                        fontsize=FS - 1, color=INK)
        ax.set_title(f"{book}  (n = {len(x)}, Spearman ρ = {rho:.2f})", fontsize=FS, color=INK, loc="left")
        ax.set_xlim(0.55, 1.01)
        ax.set_ylim(0.55, 1.01)
        ax.set_xticks([0.6, 0.7, 0.8, 0.9, 1.0])
        ax.set_yticks([0.6, 0.7, 0.8, 0.9, 1.0])
        ax.grid(color=RULE, lw=0.6)
        ax.set_axisbelow(True)
        ax.tick_params(length=0)
        ax.set_xlabel("gold names intact after OCR")
    axes[0].set_ylabel("value F1 (Opus, G1)")
    fig.tight_layout()
    fig.savefig(OUT, dpi=220, facecolor="white")
    print("wrote", OUT)


if __name__ == "__main__":
    main()
