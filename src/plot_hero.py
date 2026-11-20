"""The README's hero figure: where reliability is lost on the 16 locked test pages.

    python src/plot_hero.py            # -> docs/figures/hero.png and hero_zh.png

Left: extraction value F1 (Opus 5.5, G1, ALL_PRIMARY) on the same pages read as legacy BHL OCR,
modern OCR (dots.mocr) and the expert transcription, per book, with 95% page-bootstrap intervals
(pre-registered run). Right: Butler link recall on the expert text, plain GBIF lookup
(pre-registered) vs the LLM linker (exploratory). Numbers are read from the run records, never typed.
Colours: categorical slots 1-2 of the dataviz reference palette (validated adjacent pair).
"""
from __future__ import annotations

import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from common import ROOT
from score import score_run_detail

RUN = "20261119-2052_claude-opus-5-5_test_batch"
OUT = ROOT / "docs" / "figures"
SURFACE, INK, MUTED, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e4e3df"
COL = {"Butler": "#2a78d6", "Reeve": "#eb6834"}
TXT = {
    "en": {"versions": ["Legacy\nBHL OCR", "Modern OCR\n(dots.mocr)", "Expert\ntranscription"],
           "a": "Extraction: value F1, same 16 pages", "b": "Linking bird names to GBIF\n(Butler, expert text)",
           "plain": "Plain GBIF\nlookup", "llm": "LLM\nlinker", "recall": "link recall",
           "pre": "pre-registered", "exp": "exploratory",
           "Butler": "Butler 1907 (birds)", "Reeve": "Reeve 1849 (shells)"},
    "zh": {"versions": ["BHL 旧 OCR", "现代 OCR\n(dots.mocr)", "专家转录"],
           "a": "抽取：值 F1（同样的 16 页）", "b": "鸟类学名关联到 GBIF\n（Butler，专家转录）",
           "plain": "直接查\nGBIF", "llm": "LLM\n关联器", "recall": "关联召回率",
           "pre": "预注册", "exp": "探索性",
           "Butler": "Butler 1907（鸟类）", "Reeve": "Reeve 1849（贝类）"},
}


def data():
    s = score_run_detail(RUN, ROOT / "gold" / "gold_mentions_gloria_test.csv", "test")["summary"]
    s = s[(s.field == "ALL_PRIMARY") & (s.condition == "G1")]
    lv = pd.read_csv(ROOT / "results" / "linking_variants" / "summary.csv")
    lv = lv[(lv.run == RUN) & (lv.version == "expert")].set_index("linker")
    return s, lv


def draw(lang: str, s: pd.DataFrame, lv: pd.DataFrame) -> None:
    t = TXT[lang]
    if lang == "zh":
        plt.rcParams["font.family"] = ["Noto Sans CJK SC", "WenQuanYi Zen Hei", "DejaVu Sans"]
    else:
        plt.rcParams["font.family"] = ["DejaVu Sans"]
    fig, (a, b) = plt.subplots(1, 2, figsize=(10, 4.2), gridspec_kw={"width_ratios": [2.3, 1]},
                               facecolor=SURFACE)
    order = ["legacy", "modern_dots-mocr", "expert"]
    for book, off in (("Butler", -0.06), ("Reeve", 0.06)):
        d = s[s.book == book].set_index("version").loc[order]
        x = [i + off for i in range(3)]
        a.vlines(x, d.value_F1_lo, d.value_F1_hi, color=COL[book], lw=2, alpha=0.45)
        a.plot(x, d.value_F1, color=COL[book], lw=2, marker="o", ms=8,
               markeredgecolor=SURFACE, markeredgewidth=2, label=t[book])
        dy = -0.045 if book == "Butler" else 0.045        # Butler's labels below its points, Reeve's above
        a.text(x[0] - 0.1 if book == "Butler" else x[0] + 0.1, d.value_F1.iloc[0], f"{d.value_F1.iloc[0]:.2f}",
               ha="right" if book == "Butler" else "left", va="center", fontsize=10, color=INK)
        for i in (1, 2):
            a.text(x[i], d.value_F1.iloc[i] + dy, f"{d.value_F1.iloc[i]:.2f}", ha="center",
                   va="top" if dy < 0 else "bottom", fontsize=10, color=INK)
    a.set_xticks(range(3), t["versions"], fontsize=10, color=INK)
    a.set_xlim(-0.5, 2.5)
    a.set_title(f"{t['a']}\n({t['pre']})", loc="left", fontsize=12, color=INK, pad=10)
    a.legend(loc="lower right", frameon=False, fontsize=9.5, labelcolor=INK, handlelength=1.5)
    vals = [lv.loc["expanded", "link_recall"], lv.loc["llm", "link_recall"]]
    lo = [lv.loc["expanded", "link_recall_lo"], lv.loc["llm", "link_recall_lo"]]
    hi = [lv.loc["expanded", "link_recall_hi"], lv.loc["llm", "link_recall_hi"]]
    b.bar([0, 1], vals, width=0.5, color=[COL["Butler"], SURFACE], edgecolor=COL["Butler"], linewidth=2)
    b.vlines([0, 1], lo, hi, color=MUTED, lw=1.5)
    for i, v in enumerate(vals):
        b.text(i, hi[i] + 0.02, f"{v:.2f}", ha="center", va="bottom", fontsize=10, color=INK)
    b.set_xticks([0, 1], [f"{t['plain']}\n({t['pre']})", f"{t['llm']}\n({t['exp']})"], fontsize=9.5, color=INK)
    b.set_title(t["b"], loc="left", fontsize=12, color=INK, pad=10)
    b.set_xlim(-0.6, 1.6)
    for ax in (a, b):
        ax.set_facecolor(SURFACE)
        ax.set_ylim(0, 1.1)
        ax.set_yticks([0, 0.25, 0.5, 0.75, 1.0])
        ax.tick_params(colors=MUTED, labelsize=9, length=0)
        ax.grid(axis="y", color=GRID, lw=0.8)
        ax.set_axisbelow(True)
        for sp in ("top", "right", "left"):
            ax.spines[sp].set_visible(False)
        ax.spines["bottom"].set_color(MUTED)
    b.set_ylabel(t["recall"], color=MUTED, fontsize=9)
    fig.tight_layout()
    OUT.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT / ("hero.png" if lang == "en" else "hero_zh.png"), dpi=200, facecolor=SURFACE)
    plt.close(fig)


if __name__ == "__main__":
    s, lv = data()
    for lang in (sys.argv[1:] or ["en", "zh"]):
        draw(lang, s, lv)
    print("written", OUT)
