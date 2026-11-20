"""Exploratory (DEVIATIONS.md): does a cheap OCR measure predict what the extractor gets right?

    python src/ocr_ladder_downstream.py

Joins, per OCR text version and book on the 16 TEST pages,
  - Opus G1 value-level F1 / recall (runs 20261120-ocrladder*, plus the frozen test run for
    legacy, dots-mocr and the expert text), scored by score.py against the frozen test gold;
  - median page CER and gold-entity preservation from src/ocr_ladder.py (test pages only).
Reports Spearman correlations of F1 with page CER and with preservation, per book, and draws
results/ocr_ladder/downstream.png. Writes results/ocr_ladder/downstream.csv and DOWNSTREAM.md.
"""
from __future__ import annotations

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from scipy.stats import spearmanr

from common import ROOT
from score import score_run_detail

OUT = ROOT / "results" / "ocr_ladder"
RUNS = ["20261120-ocrladder_claude-opus-5-5_test_G1", "20261120-ocrladder2_claude-opus-5-5_test_G1",
        "20261119-2052_claude-opus-5-5_test_batch", "20261120-ocrladder3_claude-opus-5-5_test_G1"]
GOLD = ROOT / "gold" / "gold_mentions_gloria_test.csv"
PRIMARY = ["taxon", "person", "locality", "institution", "date"]
INK, MUTED, ACCENT, GRID = "#0b0b0b", "#52514e", "#2a78d6", "#e6e5e1"


def ocr_name(version: str) -> str:
    v = version.removeprefix("modern_")
    return {"legacy": "legacy (BHL)", "lighton-ocr3-0p8b": "lighton-ocr3-0.8b",
            "mistral-ocr-openrouter": "mistral-ocr (OpenRouter)"}.get(v, v)


def main() -> None:
    parts = []
    for r in RUNS:
        s = score_run_detail(r, GOLD, "test")["summary"]
        parts.append(s[(s.condition == "G1") & (s.field == "ALL_PRIMARY")])
    sc = pd.concat(parts)
    sc = sc[sc.version != "modern_dots-mocr_plain"]
    sc["ocr"] = sc.version.map(ocr_name)

    pages = pd.read_csv(OUT / "pages.csv").query("split == 'test'")
    ments = pd.read_csv(OUT / "mentions.csv").query("split == 'test'")
    ments = ments[ments.field.isin(PRIMARY)]
    lad = pages.groupby(["ocr", "book"]).page_cer.median().rename("median_page_cer").to_frame() \
        .join(ments.groupby(["ocr", "book"]).preserved.mean()) \
        .join(ments.groupby(["ocr", "book"]).preserved_folded.mean()).reset_index()
    d = sc[["ocr", "book", "value_F1", "value_F1_lo", "value_F1_hi", "value_R", "lenient_F1"]] \
        .merge(lad, on=["ocr", "book"], how="left")
    d.loc[d.ocr == "expert", ["median_page_cer", "preserved", "preserved_folded"]] = [0.0, 1.0, 1.0]
    d = d.sort_values(["book", "value_F1"])
    d.to_csv(OUT / "downstream.csv", index=False)

    lines = ["# Does a cheap OCR measure predict downstream extraction? (exploratory, test pages)", "",
             "Opus G1 value F1 (ALL_PRIMARY) on each OCR text, against the OCR's median page CER and the share "
             "of gold mentions preserved intact (`src/ocr_ladder.py`). 21 FineBooks OCR rows (Datalab rows "
             "not sent to the API: their outputs carry use restrictions), BHL legacy OCR and the expert text; "
             "7 Butler and 9 Reeve test pages. Decided after unsealing: exploratory.", "",
             "| book | Spearman F1 vs page CER | Spearman F1 vs preservation | Spearman recall vs preservation |",
             "|---|---|---|---|"]
    ocr_only = d[d.ocr != "expert"]
    for book, b in ocr_only.groupby("book"):
        r1 = spearmanr(b.value_F1, b.median_page_cer)
        r2 = spearmanr(b.value_F1, b.preserved)
        r3 = spearmanr(b.value_R, b.preserved)
        lines.append(f"| {book} | {r1.statistic:.2f} (p={r1.pvalue:.3f}) | {r2.statistic:.2f} (p={r2.pvalue:.3f}) "
                     f"| {r3.statistic:.2f} (p={r3.pvalue:.3f}) |")
    gap = (ocr_only.preserved - ocr_only.value_R)
    lines += ["", f"Recall minus preservation, across OCR versions: median {gap.median():+.3f}, "
                  f"range {gap.min():+.3f} to {gap.max():+.3f} (negative = the extractor gets fewer right "
                  "than survive the OCR).", "",
              d[["book", "ocr", "median_page_cer", "preserved", "preserved_folded", "value_R", "value_F1",
                 "value_F1_lo", "value_F1_hi"]].round(3).to_markdown(index=False), ""]
    (OUT / "DOWNSTREAM.md").write_text("\n".join(lines), encoding="utf-8")

    # 2 x 2 small multiples: rows = book, columns = predictor. One series per panel, so no legend;
    # three reference points are labelled directly.
    fig, axes = plt.subplots(2, 2, figsize=(10, 8), sharey=True)
    for i, book in enumerate(["Butler", "Reeve"]):
        b = d[d.book == book]
        for j, (col, label) in enumerate([("median_page_cer", "Median page CER (case-insensitive)"),
                                           ("preserved", "Gold mentions preserved intact by the OCR")]):
            ax = axes[i][j]
            ax.scatter(b[col], b.value_F1, s=36, color=ACCENT, edgecolor="white", linewidth=1, zorder=3)
            for _, r in b[b.ocr.isin(["legacy (BHL)", "dots-mocr", "expert", "tesseract"])].iterrows():
                off = (6, -12) if r.ocr == "dots-mocr" else (6, -3)     # keep it off the "expert" label
                ax.annotate(r.ocr, (r[col], r.value_F1), xytext=off, textcoords="offset points",
                            fontsize=8.5, color=MUTED)
            ax.grid(color=GRID, linewidth=0.8)
            ax.set_axisbelow(True)
            for s in ("top", "right"):
                ax.spines[s].set_visible(False)
            for s in ("left", "bottom"):
                ax.spines[s].set_color(MUTED)
            ax.tick_params(colors=MUTED, labelsize=9)
            ax.set_xlabel(label, color=INK, fontsize=9.5)
            if j == 0:
                ax.set_ylabel(f"{book}: extraction value F1", color=INK, fontsize=9.5)
            rho = spearmanr(b[b.ocr != "expert"][col], b[b.ocr != "expert"].value_F1).statistic
            ax.set_title(f"{book}, Spearman ρ = {rho:.2f} (OCR versions only)", color=INK, fontsize=10, loc="left")
    fig.suptitle("Entity preservation predicts extraction far better than page CER\n"
                 "Opus G1 on 16 test pages, 22 OCR versions + expert text (exploratory)",
                 x=0.02, ha="left", fontsize=11.5, color=INK)
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    fig.savefig(OUT / "downstream.png", dpi=160, facecolor="#fcfcfb")
    print("\n".join(lines[:12]))


if __name__ == "__main__":
    main()
