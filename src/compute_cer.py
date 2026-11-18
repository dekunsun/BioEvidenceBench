"""Task 3b: per-page character error rate (CER) of legacy OCR against the
expert transcription, and a per-book summary.

CER = Levenshtein edit distance(OCR, expert) / number of expert characters,
computed after `normalize_for_cer` on both sides (see common.py).
We also report:
  cer_nocase    same as cer but case-insensitive. Reeve prints running heads
                and English species names in SMALL CAPS; the experts typed
                them as upper case, the OCR as mixed case. Those are not
                misreads, so cer_nocase is the value used for the CER bands
                and for sampling.
  cer_raw       whitespace-only normalisation (stricter; ligatures, long-s,
                curly quotes all count as errors)
  word_miss     share of expert word tokens that do not appear in the OCR
                (bag of words, order ignored). If CER is high but word_miss
                is low, the page is probably *re-ordered* (columns, captions,
                footnotes) rather than misread. A high CER alone does not
                prove the characters were misread.
  n_illegible   U+FFFD in the expert text (transcriber's "illegible" mark).
                It counts as one error per character. This affects few pages.

Outputs
  data/cer_legacy.csv               one row per page (committed, no text)
  data/reports/02_cer_legacy.md     distribution per book
  data/reports/02_cer_legacy.png    histogram per book

Run:  python src/compute_cer.py
"""
from __future__ import annotations

import re
from collections import Counter

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from rapidfuzz.distance import Levenshtein

from common import BOOK_SHORT, CACHE, DATA, REPORTS, TEXT, collapse_ws, normalize_for_cer

_WORD = re.compile(r"\w+")

# CER bands used for stratified sampling. Fixed in advance (not tuned on the
# data) and roughly in line with common OCR practice: <2% is good print OCR,
# 2-10% is usable with errors, >10% is poor.
BANDS = [(0, 0.02, "low"), (0.02, 0.10, "medium"), (0.10, float("inf"), "high")]


def band(cer: float) -> str:
    for lo, hi, name in BANDS:
        if lo <= cer < hi:
            return name
    return "high"


def cer(ocr: str, ref: str) -> float:
    if not ref:
        return float("nan")
    return Levenshtein.distance(ocr, ref) / len(ref)


def word_miss(ocr: str, ref: str) -> float:
    ref_w = Counter(w.lower() for w in _WORD.findall(ref))
    ocr_w = Counter(w.lower() for w in _WORD.findall(ocr))
    total = sum(ref_w.values())
    if total == 0:
        return float("nan")
    hit = sum(min(c, ocr_w[w]) for w, c in ref_w.items())
    return 1 - hit / total


def main() -> None:
    gt = pd.read_parquet(CACHE / "gt_english.parquet")
    gt = gt[gt.gt_chars > 0]
    rows = []
    for r in gt.itertuples():
        legacy_path = TEXT / "legacy" / f"{r.PageID}.txt"
        if not legacy_path.exists():
            continue
        ocr = legacy_path.read_text(encoding="utf-8")
        ref_n, ocr_n = normalize_for_cer(r.text), normalize_for_cer(ocr)
        rows.append({
            "PageID": r.PageID, "book": BOOK_SHORT[r.BarCode], "SequenceOrder": r.SequenceOrder,
            "PageTypeName": r.PageTypeName, "gt_chars": len(ref_n), "ocr_chars": len(ocr_n),
            "cer": round(cer(ocr_n, ref_n), 4),
            "cer_nocase": round(cer(ocr_n.lower(), ref_n.lower()), 4),
            "cer_raw": round(cer(collapse_ws(ocr), collapse_ws(r.text)), 4),
            "word_miss": round(word_miss(ocr_n, ref_n), 4),
            "n_illegible": r.n_illegible, "has_reading_order": r.has_reading_order,
        })
    df = pd.DataFrame(rows)
    df["cer_band"] = df.cer_nocase.map(band)
    df.to_csv(DATA / "cer_legacy.csv", index=False)

    # Very short pages (a page number, a one-line caption) give unstable CER:
    # one wrong digit on a 3-character page is 33%. Summaries are shown for
    # all pages and for pages with >= 200 expert characters.
    def summarise(d: pd.DataFrame) -> pd.DataFrame:
        q = d.groupby("book").cer_nocase.describe(percentiles=[.1, .25, .5, .75, .9])
        q = q[["count", "mean", "10%", "25%", "50%", "75%", "90%", "max"]]
        bands = pd.crosstab(d.book, d.cer_band).reindex(columns=["low", "medium", "high"], fill_value=0)
        return q.round(3).join(bands)

    long_ = df[df.gt_chars >= 200]
    reorder = df[(df.cer_nocase > 0.10) & (df.word_miss < 0.05)]

    # Histogram, one panel per book.
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.4), sharey=False)
    for ax, (book, d) in zip(axes, long_.groupby("book")):
        ax.hist(d.cer_nocase.clip(upper=0.5), bins=50, color="#4C72B0")
        for x in (0.02, 0.10):
            ax.axvline(x, color="#999", ls="--", lw=1)
        ax.set_title(f"{book} (n={len(d)}, pages >= 200 chars)")
        ax.set_xlabel("legacy OCR CER, case-insensitive (clipped at 0.5)")
    axes[0].set_ylabel("pages")
    fig.tight_layout()
    fig.savefig(REPORTS / "02_cer_legacy.png", dpi=150)

    lines = [
        "# 02 Legacy OCR CER against the expert transcription",
        "",
        "Generated by `src/compute_cer.py`. CER = edit distance / expert characters, after light",
        "normalisation (NFKC, ASCII quotes and dashes, whitespace collapsed). `cer_raw` skips all but",
        "the whitespace step. Tables and bands use `cer_nocase` (case-insensitive), because the experts typed",
        "small capitals as upper case and the OCR did not; that is a convention, not a misread.",
        "Bands: low < 2%, medium 2-10%, high >= 10% (fixed before looking at data).",
        "",
        "## All text pages",
        "",
        summarise(df).to_markdown(),
        "",
        "## Pages with at least 200 expert characters",
        "",
        "Short pages (a page number, a one-line plate caption) make CER jumpy, so this is the fairer view.",
        "",
        summarise(long_).to_markdown(),
        "",
        "![CER histogram](02_cer_legacy.png)",
        "",
        "## Things to know before reading these numbers",
        "",
        f"- **Re-ordering, not misreading.** {len(reorder)} pages have CER > 10% but miss < 5% of the "
        "expert words. Their characters are mostly right but in a different order (captions, columns, "
        "footnotes, missing `<ReadingOrder>`). Their CER overstates how badly the OCR misread the page. "
        "The `word_miss` column in `data/cer_legacy.csv` lets you spot them.",
        f"- Mean `cer` (case-sensitive) minus mean `cer_nocase`: {(df.cer.mean() - df.cer_nocase.mean()):.3f}. "
        "This is how much error comes only from small capitals.",
        f"- Mean `cer_raw` minus mean `cer`: {(df.cer_raw.mean() - df.cer.mean()):.3f}. This is how much "
        "of the raw error comes only from ligatures, long-s, quotes and dashes.",
        f"- Pages with U+FFFD (illegible) in the expert text: {(df.n_illegible > 0).sum()}. Each U+FFFD counts as one error.",
        "- The sample is two books. These distributions describe these two books only.",
        "",
    ]
    (REPORTS / "02_cer_legacy.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
