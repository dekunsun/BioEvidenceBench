"""Two README figures in the style of the overview set (docs/assets/overview/, Gloria's drafts):

    python src/plot_readme_figs.py
    -> docs/assets/overview/fig05_name_preservation.png   (OCR ladder, exploratory)
    -> docs/assets/overview/fig06_rl_repair.png           (RL module, locked test)

Cream background, teal band on top, navy title, teal / orange marks; values read from the run
records (`results/ocr_ladder/summary.csv`, `rl/training/results_test/metrics.csv`).
"""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "assets" / "overview"
BG, BAND, NAVY, GREY = "#fffdf8", "#137f7d", "#1b2a3a", "#5b6573"
TEAL, ORANGE, LIGHT = "#1f8683", "#db8562", "#c9cfd6"
plt.rcParams.update({"font.family": "Inter", "font.size": 13})


def frame(w: float, h: float, title: str, subtitle: str, note: str):
    fig = plt.figure(figsize=(w, h), dpi=150, facecolor=BG)
    fig.patches.append(plt.Rectangle((0, 0.985), 1, 0.015, transform=fig.transFigure, color=BAND))
    fig.text(0.04, 0.9, title, fontsize=24, fontweight="bold", color=NAVY, va="top")
    fig.text(0.04, 0.81, subtitle, fontsize=14, color=GREY, va="top")
    fig.text(0.04, 0.03, note, fontsize=11, color=GREY, style="italic")
    ax = fig.add_axes([0.09, 0.17, 0.86, 0.55], facecolor=BG)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(LIGHT)
    ax.tick_params(colors=GREY, labelsize=12)
    ax.grid(axis="y", color="#ece9e1", lw=0.8)
    ax.set_axisbelow(True)
    return fig, ax


def fig05() -> None:
    s = pd.read_csv(ROOT / "results" / "ocr_ladder" / "summary.csv")
    b = s[s.book == "Butler"].copy()
    b["cer"] = b.median_page_cer * 100
    b["names"] = b.preserved_taxon * 100
    fig, ax = frame(12, 5.4, "Few character errors, but missing names",
                    "Butler (1907), 10 sample pages: each dot is one OCR system reading the same pages",
                    "Exploratory comparison, not a ranking of OCR systems; legacy = the library's older OCR text.")
    low = b[b.cer < 0.5]
    ax.axvspan(0, 0.5, color="#e8f3f2", zorder=0)
    ax.text(0.04, 103, "under 0.5% page error", fontsize=12, color=TEAL, va="bottom")
    ax.scatter(b.cer, b.names, s=70, color=LIGHT, edgecolors=BG, linewidths=1.5, zorder=2)
    ax.scatter(low.cer, low.names, s=80, color=TEAL, edgecolors=BG, linewidths=1.5, zorder=3)
    leg = b[b.ocr.str.startswith("legacy")]
    ax.scatter(leg.cer, leg.names, s=90, color=ORANGE, edgecolors=BG, linewidths=1.5, zorder=3)
    for r in leg.itertuples():
        ax.annotate("legacy OCR", (r.cer, r.names), xytext=(-12, -4), textcoords="offset points",
                    ha="right", fontsize=12, color=NAVY)
    lo, hi = low.names.min(), low.names.max()
    ax.annotate(f"some keep only {lo:.0f}% of names", (low.cer[low.names.idxmin()], lo), xytext=(18, -6),
                textcoords="offset points", fontsize=12, color=NAVY)
    ax.set_xlabel("median page character error rate (%)", color=GREY, fontsize=12)
    ax.set_ylabel("scientific names kept intact (%)", color=GREY, fontsize=12)
    ax.set_ylim(20, 108)
    ax.set_xlim(0, max(b.cer) * 1.08)
    fig.savefig(OUT / "fig05_name_preservation.png", facecolor=BG)


def fig06() -> None:
    m = pd.read_csv(ROOT / "rl" / "training" / "results_test" / "metrics.csv")
    m = m[m.set == "p0_test_inbook"].set_index("model").repair_rate
    rows = [("Untrained model", ["base"], LIGHT), ("Supervised (SFT)", ["sft_s1", "sft_s2"], TEAL),
            ("Reinforcement only (GRPO)", ["grpo_s1", "grpo_s2"], ORANGE),
            ("SFT, then GRPO", ["sft_grpo_s1", "sft_grpo_s2"], TEAL)]
    fig, ax = frame(12, 5.4, "Supervised training taught repair; reinforcement learning did not",
                    "Share of damaged words repaired · 500 locked test lines · small open model (Qwen3-0.6B)",
                    "Mean of two training seeds; pre-registered test, run once. Details: docs/rl_results.md")
    for i, (name, labels, c) in enumerate(rows):
        v = sum(m[x] for x in labels) / len(labels)
        ax.bar(i, v * 100, width=0.55, color=c, zorder=2)
        ax.text(i, v * 100 + 1.2, f"{v * 100:.0f}%", ha="center", va="bottom", fontsize=15, fontweight="bold", color=NAVY)
    ax.set_xticks(range(len(rows)), [r[0] for r in rows], fontsize=13, color=NAVY)
    ax.set_ylim(0, 50)
    ax.set_ylabel("damaged words repaired (%)", color=GREY, fontsize=12)
    fig.savefig(OUT / "fig06_rl_repair.png", facecolor=BG)


if __name__ == "__main__":
    fig05()
    fig06()
    print("wrote", OUT / "fig05_name_preservation.png", "and", OUT / "fig06_rl_repair.png")
