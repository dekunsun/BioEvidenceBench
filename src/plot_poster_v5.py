"""Charts for the A1 poster, version 5 (poster/poster.html, LiveLab layout): the three charts of
src/plot_poster_v3.py redrawn at the LiveLab poster's chart size and type (Liberation Sans, as Arial /
Helvetica in the poster's CSS), so every label prints at the poster's body size (26 px).
Each chart is shown about 460 px wide, three in a row (2026-11-25); at 4.5 in x 200 dpi that is a 0.51 scale.

    python src/plot_poster_v5.py   -> poster/fig/v5/f1_by_text.png, names_vs_f1.png, link_recall.png
"""
from __future__ import annotations

import matplotlib.pyplot as plt

import plot_poster_v3 as v3

v3.OUT = v3.ROOT / "poster" / "fig" / "v5"
v3.FS = 17.0
v3.W, v3.H = 4.5, 5.6
v3.NARROW_F1 = True
v3.STAR_LLM = True
v3.LINK_LABELS = {'Plain GBIF\nlookup': 'Plain\nGBIF', 'GBIF with\ncontext hint': 'GBIF\n+ hint', 'LLM linker\n(Haiku)': 'LLM\nHaiku', 'LLM linker\n(Opus)': 'LLM\nOpus'}
v3.INK, v3.GREY = "#15201c", "#4d5a55"
plt.rcParams.update({"font.family": ["Liberation Sans", "DejaVu Sans"], "font.size": v3.FS,
                     "axes.edgecolor": v3.GREY, "axes.labelcolor": v3.INK, "xtick.color": v3.INK,
                     "ytick.color": v3.INK})

def bencao_bars() -> None:
    """Box 04: the 本草綱目 pilot as horizontal bars (value F1, p2 dev runs), ordered by OCR CER, so the
    reversal shows: Haiku OCR has the lower CER but the lower F1. Numbers from
    results/bencao_pilot/ocr_to_extraction_p2.csv (CER: results/bencao_pilot REPORT, median vs the
    scan-verified reference). Six development half-leaves; exploratory."""
    import pandas as pd
    d = pd.read_csv(v3.ROOT / "results" / "bencao_pilot" / "ocr_to_extraction_p2.csv").set_index("text")
    rows = [("Scan-verified", "verified_plain", "0"), ("Opus OCR", "claude_opus", "0.03"),
            ("Haiku OCR", "claude_haiku", "0.15"), ("PaddleOCR", "paddleocr", "0.26")]
    fig, ax = plt.subplots(figsize=(3.4, 1.62))
    for i, (lab, key, cer) in enumerate(rows):
        from decimal import Decimal, ROUND_HALF_UP
        f1 = float(Decimal(str(d.loc[key, "ALL_PRIMARY_value_f1"])).quantize(Decimal("0.01"), ROUND_HALF_UP))  # 0.865 -> 0.87, as in the README
        ax.barh(i, f1, height=0.55, color=v3.NAVY if i == 0 else "#7f8fb3")
        ax.text(f1 + 0.02, i, f"{f1:.2f}", va="center", fontsize=10, color=v3.INK)
        ax.text(-0.02, i - 0.1, f"{lab}  ", va="center", ha="right", fontsize=10, color=v3.INK)
        ax.text(-0.02, i + 0.36, f"CER {cer}  ", va="center", ha="right", fontsize=8.5, color=v3.GREY)
    ax.set_xlim(0, 1.18)
    ax.set_ylim(3.6, -0.6)
    ax.set_xticks([])
    ax.set_yticks([])
    for side in ("top", "right", "left", "bottom"):
        ax.spines[side].set_visible(False)
    ax.set_title("Value F1", fontsize=8.5, color=v3.GREY, loc="left", x=0)
    fig.subplots_adjust(left=0.37, right=0.98, top=0.86, bottom=0.04)
    fig.savefig(v3.OUT / "bencao_bars.png", dpi=200, facecolor="white")
    plt.close(fig)


if __name__ == "__main__":
    v3.OUT.mkdir(parents=True, exist_ok=True)
    v3.f1_by_text()
    v3.names_vs_f1()
    v3.link_recall()
    bencao_bars()
    print("written", v3.OUT)
