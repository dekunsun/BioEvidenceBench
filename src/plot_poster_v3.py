"""Charts for the A1 poster, version 3 (poster/poster.html): one typeface (Inter), one accent colour
(Penn navy) and one grey, sized to the poster's 7.27 in column so every label prints at the caption size
(21 px = 15.75 pt). Values are read from the run records, as in src/plot_poster_charts.py.

    python src/plot_poster_v3.py   -> poster/fig/v3/f1_by_text.png, names_vs_f1.png
"""
from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from scipy.stats import spearmanr

from common import ROOT
from score import score_run_detail

OUT = ROOT / "poster" / "fig" / "v3"
RUN = "20261119-2052_claude-opus-5-5_test_batch"
INK, GREY, RULE, NAVY, LIGHT = "#1b1f24", "#5f6670", "#d7dbe0", "#011F5B", "#8d96a3"
COL = {"Butler": NAVY, "Reeve": LIGHT}
MARK = {"Butler": "o", "Reeve": "s"}
FS = 20.0
W, H = 7.27, 3.0

plt.rcParams.update({"font.family": ["Inter", "DejaVu Sans"], "font.size": FS, "axes.edgecolor": GREY,
                     "axes.labelcolor": INK, "xtick.color": INK, "ytick.color": INK, "axes.spines.top": False,
                     "axes.spines.right": False, "axes.linewidth": 1.2})


def f1_by_text() -> None:
    s = score_run_detail(RUN, ROOT / "gold" / "gold_mentions_gloria_test.csv", "test")["summary"]
    s = s[(s.field == "ALL_PRIMARY") & (s.condition == "G1")]
    order = ["legacy", "modern_dots-mocr", "expert"]
    fig, ax = plt.subplots(figsize=(W, H))
    for book, off in (("Butler", -0.06), ("Reeve", 0.06)):
        d = s[s.book == book].set_index("version").loc[order]
        x = [i + off for i in range(3)]
        ax.errorbar(x, d.value_F1, yerr=[d.value_F1 - d.value_F1_lo, d.value_F1_hi - d.value_F1], color=COL[book],
                    lw=2, marker=MARK[book], ms=11, capsize=5, label=f"{book} ({'birds 1907' if book == 'Butler' else 'shells 1849'})")
        # labels: library OCR beside the points, modern OCR below (Butler) or above (Reeve); expert in the caption
        ax.text(x[0] + (-0.09 if book == "Butler" else 0.09), d.value_F1.iloc[0], f"{d.value_F1.iloc[0]:.2f}",
                ha="right" if book == "Butler" else "left", va="center", fontsize=FS, color=INK)
        if book == "Butler":  # below right of the point, clear of the line and the legend
            ax.text(x[1] + 0.08, d.value_F1.iloc[1] - 0.04, f"{d.value_F1.iloc[1]:.2f}", ha="left", va="top",
                    fontsize=FS, color=COL[book])
        else:
            ax.text(x[1], d.value_F1.iloc[1] + 0.035, f"{d.value_F1.iloc[1]:.2f}", ha="center", va="bottom",
                    fontsize=FS, color=COL[book])
    ax.set_xticks(range(3), ["Library\nOCR", "Modern\nOCR", "Expert\ntranscription"])
    ax.set_xlim(-0.5, 2.5)
    ax.set_ylim(0.4, 1.08)
    ax.set_yticks([0.4, 0.6, 0.8, 1.0])
    ax.set_ylabel("Value F1")
    ax.grid(axis="y", color=RULE, lw=1)
    ax.set_axisbelow(True)
    ax.tick_params(length=0)
    ax.legend(loc="lower right", frameon=False, handlelength=1.4, fontsize=FS - 3, borderaxespad=0.2)
    fig.tight_layout()
    fig.savefig(OUT / "f1_by_text.png", dpi=200, facecolor="white")
    plt.close(fig)


def names_vs_f1() -> None:
    d = pd.read_csv(ROOT / "results" / "ocr_ladder" / "downstream.csv")
    d = d[d.ocr != "expert"]
    fig, ax = plt.subplots(figsize=(W, H))
    for book in ("Butler", "Reeve"):
        x = d[d.book == book]
        rho = spearmanr(x.preserved, x.value_F1).statistic
        ax.scatter(x.preserved, x.value_F1, s=90, marker=MARK[book], color=COL[book], edgecolor="white", lw=0.8,
                   label=f"{book}, Spearman ρ = {rho:.2f}", zorder=3)
    ax.plot([0.5, 1.0], [0.5, 1.0], color=LIGHT, lw=1.2, ls=(0, (4, 4)))
    ax.set_xlim(0.5, 1.02)
    ax.set_ylim(0.38, 1.02)  # room under the diagonal for the legend
    ax.set_xticks([0.6, 0.8, 1.0])
    ax.set_yticks([0.4, 0.6, 0.8, 1.0])
    ax.set_xlabel("Share of gold names intact after OCR")
    ax.set_ylabel("Value F1")
    ax.grid(color=RULE, lw=1)
    ax.set_axisbelow(True)
    ax.tick_params(length=0)
    ax.legend(loc="lower right", frameon=False, handletextpad=0.3, fontsize=FS - 3, borderaxespad=0.2)
    fig.tight_layout()
    fig.savefig(OUT / "names_vs_f1.png", dpi=200, facecolor="white")
    plt.close(fig)


def link_recall() -> None:
    """Butler link recall on the expert text: plain GBIF lookup (pre-registered) against an LLM linker
    (exploratory), as in src/plot_poster_charts.py chart C."""
    base = pd.read_csv(ROOT / "results" / "linking_variants" / "summary.csv")
    base = base[(base.run == RUN) & (base.version == "expert")].set_index("linker")
    rows = [("Plain GBIF\nlookup", base.loc["expanded", "correct"] / base.loc["expanded", "gold_resolved"], True),
            ("GBIF with\ncontext hint", base.loc["hinted", "correct"] / base.loc["hinted", "gold_resolved"], False)]
    for name, folder in (("LLM linker\n(Haiku)", "linking_variants_haiku-5-5"), ("LLM linker\n(Opus)", "linking_variants")):
        x = pd.read_csv(ROOT / "results" / folder / "summary.csv")
        x = x[(x.run == RUN) & (x.version == "expert") & (x.linker == "llm")]
        rows.append((name, float(x.correct.iloc[0] / x.gold_resolved.iloc[0]), False))
    fig, ax = plt.subplots(figsize=(W, H))
    for i, (lab, v, pre) in enumerate(rows):
        ax.bar(i, v, width=0.58, color=NAVY if pre else "white", edgecolor=NAVY, lw=2)
        ax.text(i, v + 0.025, f"{v:.2f}", ha="center", va="bottom", fontsize=FS, color=INK)
    ax.set_xticks(range(len(rows)), [r[0] for r in rows])
    ax.set_ylim(0, 1.1)
    ax.set_yticks([0, 0.5, 1.0])
    ax.set_ylabel("Link recall")
    ax.grid(axis="y", color=RULE, lw=1)
    ax.set_axisbelow(True)
    ax.tick_params(length=0)
    fig.tight_layout()
    fig.savefig(OUT / "link_recall.png", dpi=200, facecolor="white")
    plt.close(fig)
    print("link recall", [(r[0].replace(chr(10), " "), round(r[1], 2)) for r in rows])


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    f1_by_text()
    names_vs_f1()
    link_recall()
    print("written", OUT)
