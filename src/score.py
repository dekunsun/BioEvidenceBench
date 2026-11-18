"""Score located mentions against Gloria's gold labels.

Gold mentions point into the EXPERT transcription. A run's mentions point into
whatever text version the extractor read (expert, legacy OCR, modern OCR). So
each predicted span is first mapped to expert-text offsets through a character
alignment of the two texts (case-insensitive edit-distance alignment). A
predicted span that falls entirely inside text the expert version does not
have (or that the alignment cannot place, e.g. re-ordered paragraphs) is
counted as UNALIGNED: it is a false positive, and it is also reported on its
own.

Three matching levels, per field, one-to-one (each gold mention matches at
most one prediction):
  lenient   same field and the spans overlap by at least one character
  exact     same field and the mapped span equals the gold span exactly
  value     lenient, AND the predicted value equals the gold text after light
            normalisation (NFKC, case-folded, Markdown emphasis marks,
            whitespace and line-end hyphenation removed). A correct position with a misread value
            ("BuLIMUS CASTDS" for "BULIMUS CASTUS") is lenient but not value.
For each level: TP, FP, FN, precision, recall, F1, with a 95% bootstrap
interval from resampling PAGES (1,000 resamples), reported per book.

Entity-span CER (RQ1): for every gold mention and every OCR version, the
characters aligned to the gold span are cut out of the OCR text and compared
with the gold text: CER and "preserved" (identical after normalisation).

Run:  python src/score.py --run <run_id> --gold gold/gold_mentions_gloria.csv --split dev
      (test scores need the run unsealed first: src/unseal.py)
Output: results/<run_id>/scores_<split>.csv, scores_<split>_by_page.csv,
        and results/entity_span_cer_<split>.csv
"""
from __future__ import annotations

import argparse
import re
import unicodedata
from functools import lru_cache

import numpy as np
import pandas as pd
from rapidfuzz.distance import Levenshtein

from common import DATA, ROOT, TEXT

RESULTS = ROOT / "results"
FIELDS = ["taxon", "person", "locality", "institution", "date"]
OCR_VERSIONS = ["legacy", "modern_dots-mocr"]
N_BOOT = 1000


# ---------------------------------------------------------------- text helpers
def lower_same_length(s: str) -> str:
    """Lower-case without changing the string length (offsets must survive)."""
    return "".join(c.lower() if len(c.lower()) == 1 else c for c in s)


_HYPH = re.compile(r"[-‐­]\s*\n\s*")


_MD = re.compile(r"[*_]+|^#+\s*", re.M)


def norm_value(s: str) -> str:
    """For value comparison only: NFKC, Markdown emphasis and heading marks
    (modern OCR output is Markdown), line-end hyphenation, whitespace, case."""
    s = unicodedata.normalize("NFKC", s or "")
    s = _MD.sub("", s)
    s = _HYPH.sub("", s)
    return re.sub(r"\s+", " ", s).strip(" .,;:()[]").casefold()


def page_text(version: str, page_id: int) -> str:
    if version == "expert":
        p = DATA / "sample" / "expert" / f"{page_id}.txt"
        if p.exists():
            return p.read_text(encoding="utf-8")
    return (TEXT / version / f"{page_id}.txt").read_text(encoding="utf-8")


# ---------------------------------------------------------------- alignment
@lru_cache(maxsize=256)
def char_map(src: str, dst: str) -> tuple:
    """For each character of src, the aligned position in dst, or -1."""
    m = [-1] * len(src)
    if src == dst:
        return tuple(range(len(src)))
    for tag, i1, i2, j1, j2 in Levenshtein.opcodes(lower_same_length(src), lower_same_length(dst)):
        if tag in ("equal", "replace"):
            n_src, n_dst = i2 - i1, j2 - j1
            for k in range(n_src):
                m[i1 + k] = j1 + min(n_dst - 1, int(k * n_dst / n_src))
    return tuple(m)


def map_span(cmap: tuple, start: int, end: int) -> tuple[int, int] | None:
    pos = [cmap[i] for i in range(start, min(end, len(cmap))) if cmap[i] >= 0]
    if not pos:
        return None
    return min(pos), max(pos) + 1


# ---------------------------------------------------------------- matching
def match_page(gold: pd.DataFrame, pred: pd.DataFrame) -> dict:
    """One-to-one greedy matching per field; returns counts per level."""
    out = {}
    for level in ("exact", "lenient", "value"):
        tp = fp = fn = 0
        for field in FIELDS:
            g = gold[gold.field == field].to_dict("records")
            p = pred[pred.field == field].to_dict("records")
            used = set()
            for pr in p:
                if pr["m_start"] is None or pd.isna(pr["m_start"]):
                    fp += 1
                    continue
                hit = None
                for gi, gr in enumerate(g):
                    if gi in used:
                        continue
                    same = (pr["m_start"] == gr["start"] and pr["m_end"] == gr["end"])
                    overlap = pr["m_start"] < gr["end"] and gr["start"] < pr["m_end"]
                    ok = {"exact": same, "lenient": overlap,
                          "value": overlap and norm_value(pr["value"]) == norm_value(gr["text"])}[level]
                    if ok:
                        hit = gi
                        break
                if hit is None:
                    fp += 1
                else:
                    used.add(hit)
                    tp += 1
            fn += len(g) - len(used)
        out[level] = (tp, fp, fn)
    return out


def prf(tp: int, fp: int, fn: int) -> tuple[float, float, float]:
    p = tp / (tp + fp) if tp + fp else float("nan")
    r = tp / (tp + fn) if tp + fn else float("nan")
    f = 2 * p * r / (p + r) if p + r and not np.isnan(p) and not np.isnan(r) else float("nan")
    return p, r, f


def bootstrap_f1(per_page: pd.DataFrame, level: str, rng: np.random.Generator) -> tuple[float, float]:
    tp, fp, fn = (per_page[f"{level}_{k}"].to_numpy() for k in ("tp", "fp", "fn"))
    n = len(tp)
    if n < 2:
        return float("nan"), float("nan")
    f1s = []
    for _ in range(N_BOOT):
        idx = rng.integers(0, n, n)
        f1s.append(prf(tp[idx].sum(), fp[idx].sum(), fn[idx].sum())[2])
    return tuple(np.nanpercentile(f1s, [2.5, 97.5]))


# ---------------------------------------------------------------- main scoring
def load_gold(path) -> pd.DataFrame:
    g = pd.read_csv(path, dtype={"text": str}, keep_default_na=False)
    g = g[g.field != "none"].copy()
    g["start"], g["end"] = g.start.astype(int), g.end.astype(int)
    return g


def score_run(run_id: str, gold_path, split: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    run_dir = RESULTS / run_id
    mentions = pd.read_csv(run_dir / f"{split}_mentions.csv", dtype={"value": str, "model_text": str},
                           keep_default_na=False)
    gold = load_gold(gold_path)
    pages = pd.read_csv(DATA / "sample_split.csv").query("split == @split")[["PageID", "book"]]
    missing = set(pages.PageID) - set(pd.read_csv(gold_path).page_id.astype(int))
    if missing:
        raise SystemExit(f"Gold has no rows for {split} pages {sorted(missing)}")

    rows = []
    combos = mentions[["version", "condition"]].drop_duplicates().itertuples(index=False)
    for version, condition in combos:
        for pid, book in pages.itertuples(index=False):
            expert = page_text("expert", pid)
            src = page_text(version, pid)
            cmap = char_map(src, expert)
            pr = mentions[(mentions.page_id == pid) & (mentions.version == version)
                          & (mentions.condition == condition)].copy()
            spans = [map_span(cmap, int(s), int(e)) if str(s) != "" else None
                     for s, e in zip(pr.start, pr.end)]
            pr["m_start"] = [s[0] if s else None for s in spans]
            pr["m_end"] = [s[1] if s else None for s in spans]
            counts = match_page(gold[gold.page_id == pid], pr)
            row = {"page_id": pid, "book": book, "version": version, "condition": condition,
                   "n_pred": len(pr), "n_gold": int((gold.page_id == pid).sum()),
                   "unaligned": int(pr.m_start.isna().sum()),
                   "not_located": int(pr.status.isin(["not_found", "invalid_evidence"]).sum())}
            for level, (tp, fp, fn) in counts.items():
                row |= {f"{level}_tp": tp, f"{level}_fp": fp, f"{level}_fn": fn}
            rows.append(row)
    by_page = pd.DataFrame(rows)

    rng = np.random.default_rng(20261118)
    summary = []
    for (book, version, condition), d in by_page.groupby(["book", "version", "condition"]):
        rec = {"book": book, "version": version, "condition": condition, "pages": len(d),
               "gold": int(d.n_gold.sum()), "pred": int(d.n_pred.sum()),
               "unaligned": int(d.unaligned.sum()), "not_located": int(d.not_located.sum())}
        for level in ("exact", "lenient", "value"):
            p, r, f = prf(*(d[f"{level}_{k}"].sum() for k in ("tp", "fp", "fn")))
            lo, hi = bootstrap_f1(d, level, rng)
            rec |= {f"{level}_P": round(p, 3), f"{level}_R": round(r, 3), f"{level}_F1": round(f, 3),
                    f"{level}_F1_lo": round(lo, 3), f"{level}_F1_hi": round(hi, 3)}
        summary.append(rec)
    return pd.DataFrame(summary), by_page


def entity_span_cer(gold_path, split: str) -> pd.DataFrame:
    """CER of every gold mention as it appears in each OCR version."""
    gold = load_gold(gold_path)
    ids = set(pd.read_csv(DATA / "sample_split.csv").query("split == @split").PageID)
    rows = []
    for g in gold[gold.page_id.isin(ids)].itertuples():
        expert = page_text("expert", g.page_id)
        for v in OCR_VERSIONS:
            ocr = page_text(v, g.page_id)
            span = map_span(char_map(expert, ocr), g.start, g.end)
            ocr_text = ocr[span[0]:span[1]] if span else ""
            a, b = norm_value(ocr_text), norm_value(g.text)
            rows.append({"page_id": g.page_id, "field": g.field, "version": v, "gold_text": g.text,
                         "ocr_text": ocr_text, "aligned": span is not None,
                         "span_cer": round(Levenshtein.distance(a, b) / max(len(b), 1), 4),
                         "preserved": a == b})
    return pd.DataFrame(rows)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True, nargs="+")
    ap.add_argument("--gold", required=True)
    ap.add_argument("--split", choices=["dev", "test"], default="dev")
    a = ap.parse_args()
    for run_id in a.run:
        summary, by_page = score_run(run_id, a.gold, a.split)
        summary.to_csv(RESULTS / run_id / f"scores_{a.split}.csv", index=False)
        by_page.to_csv(RESULTS / run_id / f"scores_{a.split}_by_page.csv", index=False)
        cols = ["book", "version", "condition", "gold", "pred", "unaligned",
                "lenient_F1", "lenient_F1_lo", "lenient_F1_hi", "value_F1", "exact_F1"]
        print(run_id)
        print(summary[cols].to_string(index=False))
    esc = entity_span_cer(a.gold, a.split)
    esc.to_csv(RESULTS / f"entity_span_cer_{a.split}.csv", index=False)
    print(esc.groupby(["version", "field"]).agg(mentions=("span_cer", "size"),
                                                 mean_span_cer=("span_cer", "mean"),
                                                 preserved=("preserved", "mean")).round(3))


if __name__ == "__main__":
    main()
