"""Charts for the poster (poster/fig/*_poster.png), drawn at the width they occupy on the poster so
that every label is the poster's body size (26 px = 19.5 pt). Values are read from the run records.

    python src/plot_poster_charts.py

A  extraction value F1 on legacy OCR, modern OCR and expert transcription, per book (pre-registered run)
B  value F1 against gold-name preservation over 24 OCR versions of the same pages (exploratory)
C  Butler link recall by linker, expert text (plain GBIF lookup pre-registered; others exploratory)
If a column width in poster/poster.html changes, change WIDTH here and regenerate.
"""
from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from scipy.stats import spearmanr

from common import ROOT
from score import score_run_detail

OUT = ROOT / "poster" / "fig"
RUN = "20261119-2052_claude-opus-5-5_test_batch"
INK, SOFT, FAINT, RULE, NAVY = "#15201c", "#4d5a55", "#6f7b76", "#d9dee6", "#011F5B"
COL = {"Butler": "#2a78d6", "Reeve": "#eb6834"}          # dataviz reference palette, slots 1-2
FS = 19.5                                                # 26 px body size on the poster
WIDTH = {"A": 4.9, "B": 4.9, "C": 4.9}                   # inches on the poster

plt.rcParams.update({"font.family": ["Helvetica Neue", "Helvetica", "FreeSans", "DejaVu Sans"],
                     "font.size": FS, "axes.edgecolor": SOFT, "axes.labelcolor": SOFT,
                     "xtick.color": SOFT, "ytick.color": SOFT, "axes.spines.top": False,
                     "axes.spines.right": False, "axes.spines.left": False})


def style(ax, ylabel):
    ax.set_ylim(0, 1.12)
    ax.set_yticks([0, 0.5, 1.0])
    ax.grid(axis="y", color=RULE, lw=1.2)
    ax.set_axisbelow(True)
    ax.tick_params(length=0, labelsize=FS)
    ax.set_ylabel(ylabel, fontsize=FS, color=SOFT)


def chart_a():
    s = score_run_detail(RUN, ROOT / "gold" / "gold_mentions_gloria_test.csv", "test")["summary"]
    s = s[(s.field == "ALL_PRIMARY") & (s.condition == "G1")]
    fig, ax = plt.subplots(figsize=(WIDTH["A"], 4.0))
    order = ["legacy", "modern_dots-mocr", "expert"]
    for book, off in (("Butler", -0.07), ("Reeve", 0.07)):
        d = s[s.book == book].set_index("version").loc[order]
        x = [i + off for i in range(3)]
        ax.vlines(x, d.value_F1_lo, d.value_F1_hi, color=COL[book], lw=3, alpha=0.4)
        ax.plot(x, d.value_F1, color=COL[book], lw=3, marker="o", ms=12, mec="white", mew=2.5, label=book)
        ax.text(x[0] + (-0.12 if book == "Butler" else 0.12), d.value_F1.iloc[0], f"{d.value_F1.iloc[0]:.2f}",
                ha="right" if book == "Butler" else "left", va="center", fontsize=FS, color=INK)
        dy = -0.06 if book == "Butler" else 0.05
        ax.text(x[1], d.value_F1.iloc[1] + dy, f"{d.value_F1.iloc[1]:.2f}", ha="center",
                va="top" if dy < 0 else "bottom", fontsize=FS, color=INK)
    ax.set_xticks(range(3), ["Legacy\nOCR", "Modern\nOCR", "Expert"], fontsize=FS)
    ax.set_xlim(-0.55, 2.45)
    style(ax, "value F1")
    ax.legend(loc="lower right", frameon=False, fontsize=FS, handlelength=1.2)
    fig.tight_layout()
    fig.savefig(OUT / "extraction_poster.png", dpi=150, facecolor="white")
    plt.close(fig)


def chart_b():
    d = pd.read_csv(ROOT / "results" / "ocr_ladder" / "downstream.csv")
    d = d[d.ocr != "expert"]                             # the 24 OCR versions (22 FineBooks rows + Mistral OCR + legacy)
    fig, ax = plt.subplots(figsize=(WIDTH["B"], 4.0))
    for book in ("Butler", "Reeve"):
        x = d[d.book == book]
        rho = spearmanr(x.preserved, x.value_F1).statistic
        ax.scatter(x.preserved, x.value_F1, s=110, color=COL[book], edgecolor="white", lw=1.5,
                   label=f"{book} ρ {rho:.2f}", zorder=3)
    ax.plot([0.55, 1.0], [0.55, 1.0], color=FAINT, lw=1.5, ls=(0, (4, 4)))
    ax.set_xlim(0.55, 1.02)
    ax.set_ylim(0.55, 1.02)
    ax.set_yticks([0.6, 0.8, 1.0])
    ax.set_xticks([0.6, 0.8, 1.0])
    ax.grid(color=RULE, lw=1.2)
    ax.set_axisbelow(True)
    ax.tick_params(length=0, labelsize=FS)
    ax.set_xlabel("gold names intact after OCR", fontsize=FS)
    ax.set_ylabel("value F1", fontsize=FS)
    ax.legend(loc="lower right", frameon=False, fontsize=FS, handletextpad=0.2)
    fig.tight_layout()
    fig.savefig(OUT / "ladder_poster.png", dpi=150, facecolor="white")
    plt.close(fig)


def chart_c():
    rows = []
    base = pd.read_csv(ROOT / "results" / "linking_variants" / "summary.csv")
    base = base[(base.run == RUN) & (base.version == "expert")].set_index("linker")
    rows += [("Plain\nGBIF", base.loc["expanded", "correct"] / base.loc["expanded", "gold_resolved"], True),
             ("GBIF\n+ hint", base.loc["hinted", "correct"] / base.loc["hinted", "gold_resolved"], False)]
    for name, folder in (("LLM\nHaiku", "linking_variants_haiku-5-5"), ("LLM\nOpus", "linking_variants")):
        x = pd.read_csv(ROOT / "results" / folder / "summary.csv")
        x = x[(x.run == RUN) & (x.version == "expert") & (x.linker == "llm")]
        rows.append((name, float(x.correct.iloc[0] / x.gold_resolved.iloc[0]), False))
    fig, ax = plt.subplots(figsize=(WIDTH["C"], 4.0))
    for i, (lab, v, pre) in enumerate(rows):
        ax.bar(i, v, width=0.6, color=NAVY if pre else "white", edgecolor=NAVY, lw=3)
        ax.text(i, v + 0.03, f"{v:.2f}", ha="center", va="bottom", fontsize=FS, color=INK)
    ax.set_xticks(range(len(rows)), [r[0] for r in rows], fontsize=FS)
    style(ax, "link recall")
    fig.tight_layout()
    fig.savefig(OUT / "linking_poster.png", dpi=150, facecolor="white")
    plt.close(fig)


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    chart_a()
    chart_b()
    chart_c()
    print("written", OUT)
