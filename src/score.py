"""Score located mentions against Gloria's gold labels.

Gold mentions point into the EXPERT transcription. A run's mentions point into
whatever text version the extractor read (expert, legacy OCR, modern OCR). So
each predicted span is first mapped to expert-text offsets through a character
alignment of the two texts (case-insensitive edit-distance alignment). A
predicted span that falls entirely inside text the expert version does not
have (or that the alignment cannot place, e.g. re-ordered paragraphs) is
counted as UNALIGNED: it is a false positive, and it is also reported on its
own.

Scores are written per field and for ALL_PRIMARY (taxon, person, locality,
institution, date). `vernacular` is scored separately and never enters
ALL_PRIMARY. Gold rows marked adjudication = ambiguous are optional (no
credit, no penalty).

Three matching levels, per field, strictly one-to-one with an optimal
assignment (see match_page): a gold mention is matched by at most one
prediction and a prediction matches at most one gold mention.
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
import json
import re
import unicodedata
from functools import lru_cache

import numpy as np
import pandas as pd
from rapidfuzz.distance import Levenshtein
from scipy.optimize import linear_sum_assignment

from common import DATA, ROOT, TEXT

RESULTS = ROOT / "results"
PRIMARY_FIELDS = ["taxon", "person", "locality", "institution", "date"]
SEPARATE_FIELDS = ["vernacular"]   # scored, but never part of the primary all-fields number
FIELDS = PRIMARY_FIELDS + SEPARATE_FIELDS
LEVELS = ("exact", "lenient", "value")
OCR_VERSIONS = ["legacy", "modern_dots-mocr", "modern_dots-mocr_plain"]
N_BOOT = 1000


# ---------------------------------------------------------------- text helpers
def lower_same_length(s: str) -> str:
    """Lower-case without changing the string length (offsets must survive)."""
    return "".join(c.lower() if len(c.lower()) == 1 else c for c in s)


_HYPH = re.compile(r"[-‐­]\s*\n\s*")


_MD = re.compile(r"[*_]+|^#+\s*", re.M)


_TYPO = str.maketrans({"\u2010": "-", "\u2011": "-", "\u2019": "'", "\u2018": "'",
                       "\u201c": '"', "\u201d": '"'})


def norm_value(s: str) -> str:
    """For value comparison only: NFKC, Markdown emphasis and heading marks
    (modern OCR output is Markdown), line-end hyphenation, whitespace, case, and
    the two ways of typing a hyphen or a quotation mark (the transcribers typed
    U+2010 and curly quotes where an OCR engine writes "-" and "'"; a reader
    sees the same character). Letters are never changed: "œ" is not "æ"."""
    s = unicodedata.normalize("NFKC", s or "").translate(_TYPO)
    s = _MD.sub("", s)
    s = _HYPH.sub("", s)
    return re.sub(r"\s+", " ", s).strip(" .,;:()[]").casefold()


def page_text(version: str, page_id: int) -> str:
    p = DATA / "sample" / version / f"{page_id}.txt"
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
def _ok(level: str, pr: dict, gr: dict) -> bool:
    same = pr["m_start"] == gr["start"] and pr["m_end"] == gr["end"]
    overlap = pr["m_start"] < gr["end"] and gr["start"] < pr["m_end"]
    if level == "exact":
        return same
    if level == "lenient":
        return overlap
    return overlap and norm_value(pr["value"]) == norm_value(gr["text"])


def _placed(pr: dict) -> bool:
    return pr["m_start"] is not None and not pd.isna(pr["m_start"])


def assign_pairs(g: list[dict], p: list[dict], level: str) -> list[tuple[int, int]]:
    """Optimal one-to-one assignment between predictions p and gold mentions g of ONE field.

    Returns (prediction index, gold index) pairs. A gold mention appears in at
    most one pair and so does a prediction. The assignment (scipy's
    linear_sum_assignment) first maximises the number of matches with strict
    gold rows, then matches with ambiguous rows, then total character overlap,
    so it does not depend on row order.
    """
    placed = [i for i, pr in enumerate(p) if _placed(pr)]
    w = np.zeros((len(placed), len(g)))
    for a_, i in enumerate(placed):
        for j, gr in enumerate(g):
            if _ok(level, p[i], gr):
                overlap = min(p[i]["m_end"], gr["end"]) - max(p[i]["m_start"], gr["start"])
                strict = gr.get("adjudication", "") != "ambiguous"
                w[a_, j] = (1e9 if strict else 1e5) + overlap
    pairs = []
    if w.size:
        rows_, cols_ = linear_sum_assignment(w, maximize=True)
        pairs = [(placed[a_], j) for a_, j in zip(rows_, cols_) if w[a_, j] > 0]
    return pairs


def match_page(gold: pd.DataFrame, pred: pd.DataFrame) -> dict:
    """One-to-one matching per field. Returns {field: {level: (tp, fp, fn, on_ambiguous)}}.

    One-to-one means: a gold mention is matched by at most one prediction and
    a prediction matches at most one gold mention (see assign_pairs). Two
    predictions on the same gold mention give one true positive and one false
    positive.

    Gold rows with adjudication == "ambiguous" are left out of strict scoring
    (ANNOTATION_GUIDE section 4): a prediction matched to one is neither a
    true nor a false positive (counted in on_ambiguous), and an unmatched
    ambiguous row is not a false negative.
    """
    out = {}
    for field in FIELDS:
        g = gold[gold.field == field].to_dict("records")
        p = pred[pred.field == field].to_dict("records")
        out[field] = {}
        for level in LEVELS:
            pairs = assign_pairs(g, p, level)
            amb = sum(1 for _, j in pairs if g[j].get("adjudication", "") == "ambiguous")
            tp = len(pairs) - amb
            matched = {j for _, j in pairs}
            fp = len(p) - tp - amb          # unplaced predictions are false positives too
            fn = sum(1 for j, gr in enumerate(g)
                     if j not in matched and gr.get("adjudication", "") != "ambiguous")
            out[field][level] = (tp, fp, fn, amb)
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
    if np.all(np.isnan(f1s)):          # no gold mentions and no predictions in this group
        return float("nan"), float("nan")
    return tuple(np.nanpercentile(f1s, [2.5, 97.5]))


# ---------------------------------------------------------------- main scoring
def _version(v: str) -> tuple:
    """'v0.7' -> (0, 7); anything unreadable sorts first."""
    nums = re.findall(r"\d+", v or "")
    return tuple(int(n) for n in nums) if nums else (0,)


def load_gold(path, optional_after: str | None = None) -> pd.DataFrame:
    """optional_after: a guide version such as 'v0.6' (the one the prompt was written
    from). Gold rows decided under a later guide version are then treated like
    `ambiguous` rows: no credit, no penalty. Used for the second, sensitivity report:
    a model was never told a rule that was found while labelling test pages."""
    g = pd.read_csv(path, dtype=str, keep_default_na=False)
    g["page_id"] = g.page_id.astype(int)
    g = g[g.field != "none"].copy()
    unresolved = g[g.notes.str.contains("UNCLEAR") & (g.get("adjudication", "") == "")] \
        if "adjudication" in g else g[g.notes.str.contains("UNCLEAR")]
    if len(unresolved):
        raise SystemExit(f"{len(unresolved)} UNCLEAR gold rows have no adjudication value "
                         "(ANNOTATION_GUIDE section 4). Resolve them before scoring.")
    if "adjudication" not in g:
        g["adjudication"] = ""
    g["start"], g["end"] = g.start.astype(float).astype(int), g.end.astype(float).astype(int)
    if optional_after and "guide_version" in g:
        later = g.guide_version.map(_version) > _version(optional_after)
        g.loc[later, "adjudication"] = "ambiguous"
    return g


def load_issues(path) -> dict:
    """Regions the labeller could not label as one clean span (ANNOTATION_GUIDE 2.0.3).
    Returns {page_id: [(start, end), ...]} in expert-text offsets."""
    regions: dict = {}
    if not path:
        return regions
    d = pd.read_csv(path, dtype=str, keep_default_na=False)
    for r in d.itertuples():
        for a_, b_ in ((r.frag1_start, r.frag1_end), (r.frag2_start, r.frag2_end)):
            if str(a_).strip() and str(b_).strip():
                regions.setdefault(int(r.page_id), []).append((int(float(a_)), int(float(b_))))
    return regions


def _to_int(x):
    """Offsets arrive as '353', '353.0' or '' (not located)."""
    return None if str(x).strip() == "" else int(float(x))


def score_run(run_id: str, gold_path, split: str, issues_path=None,
              optional_after: str | None = None) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Summary and per-page counts (see score_run_detail for the per-mention rows)."""
    d = score_run_detail(run_id, gold_path, split, issues_path, optional_after)
    return d["summary"], d["by_page"]


def score_run_detail(run_id: str, gold_path, split: str, issues_path=None,
                     optional_after: str | None = None) -> dict:
    """Score one run. Returns a dict of DataFrames:
      summary        one row per book x version x condition x field (+ ALL_PRIMARY)
      by_page        the same counts per page (input of every bootstrap)
      gold_outcomes  one row per gold mention x version x condition: was it matched
                     at each level, and by which predicted value
      pred_outcomes  one row per prediction: true positive / false positive / set aside
    """
    run_dir = RESULTS / run_id
    mentions = pd.read_csv(run_dir / f"{split}_mentions.csv", dtype=str, keep_default_na=False)
    mentions["page_id"] = mentions.page_id.astype(int)
    cfg_path = run_dir / "config.json"
    cfg = json.loads(cfg_path.read_text()) if cfg_path.exists() else {}
    gold = load_gold(gold_path, optional_after)
    issues = load_issues(issues_path)
    pages = pd.read_csv(DATA / "sample_split.csv").query("split == @split")[["PageID", "book"]]
    missing = set(pages.PageID) - set(pd.read_csv(gold_path).page_id.astype(int))
    if missing:
        raise SystemExit(f"Gold has no rows for {split} pages {sorted(missing)}")

    rows, gold_rows, pred_rows = [], [], []
    combos = mentions[["version", "condition"]].drop_duplicates().itertuples(index=False)
    for version, condition in combos:
        for pid, book in pages.itertuples(index=False):
            cmap = char_map(page_text(version, pid), page_text("expert", pid))
            pr = mentions[(mentions.page_id == pid) & (mentions.version == version)
                          & (mentions.condition == condition)].copy()
            spans = []
            for s_, e_ in zip(pr.start, pr.end):
                a_, b_ = _to_int(s_), _to_int(e_)
                spans.append(map_span(cmap, a_, b_) if a_ is not None else None)
            pr["m_start"] = [sp[0] if sp else None for sp in spans]
            pr["m_end"] = [sp[1] if sp else None for sp in spans]
            # Predictions that touch an annotation-issue region are set aside: neither right
            # nor wrong. No gold row exists there, so nothing is counted as missed either.
            in_issue = [sp is not None and any(sp[0] < b_ and a_ < sp[1] for a_, b_ in issues.get(pid, []))
                        for sp in spans]
            pr["in_issue"] = in_issue
            set_aside = pr[pr.in_issue]
            pr = pr[~pr.in_issue]
            g_page = gold[gold.page_id == pid]
            counts = match_page(g_page, pr)
            base = {"page_id": pid, "book": book, "version": version, "condition": condition}
            for r in set_aside.itertuples():
                pred_rows.append(base | {"field": r.field, "i": r.i, "value": r.value, "status": r.status,
                                         "src_start": _to_int(r.start), "src_end": _to_int(r.end),
                                         "m_start": r.m_start, "m_end": r.m_end, "outcome": "set_aside_issue_region",
                                         "lenient": False, "exact": False, "value_ok": False, "gold_text": ""})
            for field in FIELDS:
                g = g_page[g_page.field == field].to_dict("records")
                p = pr[pr.field == field].to_dict("records")
                pairs = {lvl: assign_pairs(g, p, lvl) for lvl in LEVELS}
                by_gold = {lvl: {j: i for i, j in pairs[lvl]} for lvl in LEVELS}
                by_pred = {lvl: {i: j for i, j in pairs[lvl]} for lvl in LEVELS}
                for j, gr in enumerate(g):
                    li = by_gold["lenient"].get(j)
                    gold_rows.append(base | {
                        "field": field, "start": gr["start"], "end": gr["end"], "text": gr["text"],
                        "adjudication": gr.get("adjudication", ""),
                        "lenient": j in by_gold["lenient"], "exact": j in by_gold["exact"],
                        "value_ok": j in by_gold["value"],
                        "pred_value": p[li]["value"] if li is not None else "",
                        "pred_status": p[li]["status"] if li is not None else ""})
                for i, prd in enumerate(p):
                    lj = by_pred["lenient"].get(i)
                    on_amb = lj is not None and g[lj].get("adjudication", "") == "ambiguous"
                    if on_amb:
                        outcome = "set_aside_ambiguous_gold"
                    elif i in by_pred["value"]:
                        outcome = "tp_value"
                    elif lj is not None:
                        outcome = "fp_value_wrong"       # right place, wrong text (or boundary)
                    elif not _placed(prd):
                        outcome = "fp_unaligned"
                    else:
                        outcome = "fp_no_gold"
                    pred_rows.append(base | {
                        "field": field, "i": prd["i"], "value": prd["value"], "status": prd["status"],
                        "src_start": _to_int(prd["start"]), "src_end": _to_int(prd["end"]),
                        "m_start": prd["m_start"], "m_end": prd["m_end"], "outcome": outcome,
                        "lenient": lj is not None and not on_amb, "exact": i in by_pred["exact"],
                        "value_ok": i in by_pred["value"],
                        "gold_text": g[lj]["text"] if lj is not None else ""})
            for field in FIELDS:
                pf, gf = pr[pr.field == field], g_page[g_page.field == field]
                row = {"page_id": pid, "book": book, "version": version, "condition": condition,
                       "field": field, "n_pred": len(pf),
                       "n_gold": int((gf.adjudication != "ambiguous").sum()),
                       "n_gold_ambiguous": int((gf.adjudication == "ambiguous").sum()),
                       "pred_in_issue_region": int((set_aside.field == field).sum()),
                       "issue_regions": len(issues.get(pid, [])) if field == FIELDS[0] else 0,
                       "unaligned": int(pf.m_start.isna().sum()),
                       "not_located": int(pf.status.isin(["not_found", "invalid_evidence"]).sum())}
                for level, (tp, fp, fn, amb) in counts[field].items():
                    row |= {f"{level}_tp": tp, f"{level}_fp": fp, f"{level}_fn": fn,
                            f"{level}_pred_on_ambiguous": amb}
                rows.append(row)
    by_page = pd.DataFrame(rows)

    # One summary row per field, plus ALL_PRIMARY (the five primary fields added up per page).
    num = [c for c in by_page.columns if c not in ("page_id", "book", "version", "condition", "field")]
    prim = (by_page[by_page.field.isin(PRIMARY_FIELDS)]
            .groupby(["page_id", "book", "version", "condition"], as_index=False)[num].sum()
            .assign(field="ALL_PRIMARY"))
    long = pd.concat([by_page, prim], ignore_index=True)

    rng = np.random.default_rng(20261118)
    summary = []
    for (book, version, condition, field), d in long.groupby(["book", "version", "condition", "field"]):
        rec = {"run": run_id, "split": split, "prompt_version": cfg.get("prompt_version", ""),
               "model": cfg.get("model", ""), "book": book, "version": version, "condition": condition,
               "field": field,
               "pages": len(d), "gold": int(d.n_gold.sum()),
               "gold_ambiguous_excluded": int(d.n_gold_ambiguous.sum()),
               "pred_on_ambiguous_excluded": int(d.lenient_pred_on_ambiguous.sum()),
               "pred": int(d.n_pred.sum()),
               "pred_in_issue_region_excluded": int(d.pred_in_issue_region.sum()),
               "unaligned": int(d.unaligned.sum()),
               "not_located": int(d.not_located.sum()),
               "too_few_to_compare": bool(d.n_gold.sum() < 10)}
        for level in LEVELS:
            p, r, f = prf(*(d[f"{level}_{k}"].sum() for k in ("tp", "fp", "fn")))
            lo, hi = bootstrap_f1(d, level, rng)
            rec |= {f"{level}_P": round(p, 3), f"{level}_R": round(r, 3), f"{level}_F1": round(f, 3),
                    f"{level}_F1_lo": round(lo, 3), f"{level}_F1_hi": round(hi, 3)}
        summary.append(rec)
    return {"summary": pd.DataFrame(summary), "by_page": by_page.assign(run=run_id),
            "gold_outcomes": pd.DataFrame(gold_rows).assign(run=run_id),
            "pred_outcomes": pd.DataFrame(pred_rows).assign(run=run_id)}


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
            rows.append({"page_id": int(g.page_id), "field": g.field, "version": v,
                         "gold_start": g.start, "gold_end": g.end, "gold_text": g.text,
                         "ocr_text": ocr_text, "aligned": span is not None,
                         "span_cer": round(Levenshtein.distance(a, b) / max(len(b), 1), 4),
                         "preserved": a == b})
    return pd.DataFrame(rows)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True, nargs="+")
    ap.add_argument("--gold", required=True)
    ap.add_argument("--split", choices=["dev", "test"], default="dev")
    ap.add_argument("--issues", help="gold/annotation_issues_<labeller>.csv, if any")
    ap.add_argument("--optional-after", metavar="GUIDE_VERSION",
                    help="e.g. v0.6: gold rows decided under a later guide version become optional")
    a = ap.parse_args()
    for run_id in a.run:
        summary, by_page = score_run(run_id, a.gold, a.split, a.issues, a.optional_after)
        summary.to_csv(RESULTS / run_id / f"scores_{a.split}.csv", index=False)
        by_page.to_csv(RESULTS / run_id / f"scores_{a.split}_by_page.csv", index=False)
        cols = ["book", "version", "condition", "field", "gold", "pred", "unaligned",
                "lenient_F1", "value_F1", "value_F1_lo", "value_F1_hi", "exact_F1"]
        print(run_id)
        print(summary[summary.field == "ALL_PRIMARY"][cols].to_string(index=False))
    esc = entity_span_cer(a.gold, a.split)
    esc.to_csv(RESULTS / f"entity_span_cer_{a.split}.csv", index=False)
    print(esc.groupby(["version", "field"]).agg(mentions=("span_cer", "size"),
                                                 mean_span_cer=("span_cer", "mean"),
                                                 preserved=("preserved", "mean")).round(3))


if __name__ == "__main__":
    main()
