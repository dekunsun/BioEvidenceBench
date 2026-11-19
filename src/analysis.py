"""The pre-registered analyses (PREREGISTRATION.md sections 3, 4, 8 and 9).

Every function here takes the outputs of score.score_run_detail (or a run's
mentions file) and returns a plain DataFrame. `analyze.py` runs them all and
writes the report. Nothing in this file reads a sealed file.

  paired_bootstrap    difference between two conditions on the SAME pages, with a
                      95% page-bootstrap interval, and a verdict against a rule
                      written in advance
  stage_loss          where each gold mention is lost: at OCR, at extraction, or at
                      the value/boundary step (the main answer of the project)
  evidence_counters   RQ3: outputs without support in the source, per condition
  type_check          deterministic check that a value looks like its field
  outcome_table       one status per request: ok / empty / api_error / parse_error /
                      truncated (an error is never counted as "nothing found")
  flag_auto_accept    RQ4: "proposed auto-accept" flag from two models' agreement
  rq4_summary         precision of flagged vs unflagged, shared errors, both-missed
  risk_coverage       RQ4: error rate as more predictions are accepted, in priority order
"""
from __future__ import annotations

import json
import re

import numpy as np
import pandas as pd

from score import FIELDS, PRIMARY_FIELDS, RESULTS, assign_pairs

N_BOOT = 1000
SEED = 20261118
ARM = ["run", "version", "condition"]


# ------------------------------------------------------------------ small helpers
def _metric(tp: float, fp: float, fn: float, metric: str) -> float:
    p = tp / (tp + fp) if tp + fp else np.nan
    r = tp / (tp + fn) if tp + fn else np.nan
    if metric == "P":
        return p
    if metric == "R":
        return r
    return 2 * p * r / (p + r) if p + r and not np.isnan(p) and not np.isnan(r) else np.nan


def arm_pages(by_page: pd.DataFrame, run: str, version: str, condition: str, book: str,
              field: str) -> pd.DataFrame:
    """Per-page counts of one arm. field = one field, or ALL_PRIMARY (the five primary fields)."""
    d = by_page[(by_page.run == run) & (by_page.version == version)
                & (by_page.condition == condition) & (by_page.book == book)]
    d = d[d.field.isin(PRIMARY_FIELDS)] if field == "ALL_PRIMARY" else d[d.field == field]
    num = [c for c in d.columns if c.endswith(("_tp", "_fp", "_fn"))]
    return d.groupby("page_id", as_index=False)[num].sum()


# ------------------------------------------------------------------ paired bootstrap
def verdict(lo: float, hi: float, rule: str | None, threshold: float | None) -> str:
    """Compare a 95% interval with a decision rule written in advance.

    at_least t     hypothesis: difference >= t
    greater_than t hypothesis: difference >  t
    less_than t    hypothesis: difference <  t
    An interval that contains the threshold is "inconclusive".
    """
    if rule is None:
        return "descriptive"
    if np.isnan(lo) or np.isnan(hi):
        return "no data"          # no gold mentions (or no predictions) in one of the arms
    if rule == "at_least":
        return "supports" if lo >= threshold else "against" if hi < threshold else "inconclusive"
    if rule == "greater_than":
        return "supports" if lo > threshold else "against" if hi <= threshold else "inconclusive"
    if rule == "less_than":
        return "supports" if hi < threshold else "against" if lo >= threshold else "inconclusive"
    raise ValueError(rule)


def paired_bootstrap(a: pd.DataFrame, b: pd.DataFrame, level: str = "value", metric: str = "F1",
                     n_boot: int = N_BOOT, seed: int = SEED) -> dict:
    """Difference metric(A) - metric(B) with a paired page-bootstrap 95% interval.

    a, b: per-page counts of the two arms (arm_pages). Only pages present in
    both are used, and each resample draws the SAME pages for both arms, so
    page difficulty cancels out.
    """
    m = a.merge(b, on="page_id", suffixes=("_a", "_b"))
    cols = [f"{level}_{k}" for k in ("tp", "fp", "fn")]
    A = m[[c + "_a" for c in cols]].to_numpy(float)
    B = m[[c + "_b" for c in cols]].to_numpy(float)
    n = len(m)
    va, vb = _metric(*A.sum(0), metric), _metric(*B.sum(0), metric)
    out = {"pages": n, "a": va, "b": vb, "diff": va - vb, "lo": np.nan, "hi": np.nan}
    if n >= 2:
        rng = np.random.default_rng(seed)
        diffs = []
        for _ in range(n_boot):
            idx = rng.integers(0, n, n)
            diffs.append(_metric(*A[idx].sum(0), metric) - _metric(*B[idx].sum(0), metric))
        if not np.isnan(out["diff"]) and not np.all(np.isnan(diffs)):
            out["lo"], out["hi"] = np.nanpercentile(diffs, [2.5, 97.5])
    return {k: (round(v, 3) if isinstance(v, float) else v) for k, v in out.items()}


def planned_comparisons(by_page: pd.DataFrame, llm_run: str, rule_run: str | None) -> pd.DataFrame:
    """The comparisons listed in PREREGISTRATION section 3 (RQ1-RQ3), per book and field.

    A is always the arm the hypothesis expects to be better. `preregistered` marks the
    rows whose decision rule was written in advance; the others are descriptive.
    """
    specs = []   # (rq, name, armA, armB, level, metric, rule, threshold, prereg_books, prereg_fields)
    L = llm_run
    specs += [
        ("RQ1", "modern OCR vs legacy OCR", (L, "modern_dots-mocr", "G1"), (L, "legacy", "G1"),
         "value", "F1", "at_least", 0.10, {"Reeve"}, {"ALL_PRIMARY"}),
        ("RQ1", "expert vs modern OCR", (L, "expert", "G1"), (L, "modern_dots-mocr", "G1"),
         "value", "F1", "less_than", 0.05, {"Reeve"}, {"ALL_PRIMARY"}),
        ("RQ1", "expert vs modern OCR plain (formatting removed)", (L, "expert", "G1"),
         (L, "modern_dots-mocr_plain", "G1"), "value", "F1", None, None, set(), set()),
        ("RQ1", "modern OCR Markdown vs plain (formatting ablation)", (L, "modern_dots-mocr", "G1"),
         (L, "modern_dots-mocr_plain", "G1"), "value", "F1", None, None, set(), set()),
    ]
    versions = sorted(by_page[by_page.run == L].version.unique())
    for v in versions:
        specs.append(("RQ3", f"recall with evidence (G1) vs without (G0), {v}", (L, v, "G1"), (L, v, "G0"),
                      "lenient", "R", "greater_than", -0.05, {"Butler", "Reeve"}, {"ALL_PRIMARY"}))
        if rule_run:
            specs.append(("RQ2", f"LLM (G1) vs rule baseline, recall, {v}", (L, v, "G1"), (rule_run, v, "RULE"),
                          "lenient", "R", "greater_than", 0.0, {"Butler", "Reeve"}, set(PRIMARY_FIELDS)))
            specs.append(("RQ2", f"LLM (G1) vs rule baseline, value F1, {v}", (L, v, "G1"), (rule_run, v, "RULE"),
                          "value", "F1", "greater_than", 0.0,
                          {"Butler", "Reeve"} if v == "expert" else set(), {"taxon"} if v == "expert" else set()))
    rows = []
    for rq, name, A, B, level, metric, rule, thr, pbooks, pfields in specs:
        for book in sorted(by_page.book.unique()):
            for field in ["ALL_PRIMARY"] + FIELDS:
                a = arm_pages(by_page, *A, book, field)
                b = arm_pages(by_page, *B, book, field)
                if a.empty or b.empty:
                    continue
                r = paired_bootstrap(a, b, level, metric)
                prereg = rule is not None and book in pbooks and field in pfields
                rows.append({"rq": rq, "comparison": name, "book": book, "field": field,
                             "metric": f"{level} {metric}", **r,
                             "rule": f"{rule} {thr}" if prereg else "",
                             "verdict": verdict(r["lo"], r["hi"], rule, thr) if prereg else "descriptive",
                             "preregistered": prereg})
    return pd.DataFrame(rows)


# ------------------------------------------------------------------ where mentions are lost
def stage_loss(gold_outcomes: pd.DataFrame, span_cer: pd.DataFrame) -> pd.DataFrame:
    """For each strict gold mention, the stage at which it is lost (mutually exclusive):

      lost_at_ocr          the OCR text of the span differs from the gold text, so no extractor
                           that copies the source can return the right value
                           (of_which_still_found: the model located the misread entity anyway)
      lost_at_extraction   the text survived OCR, but the model did not extract it
      lost_at_value        survived and extracted, but the returned text is not the gold text
                           (span boundary too wide or too narrow)
      kept                 survived, extracted, value correct

    For the expert version every mention counts as surviving OCR.
    """
    g = gold_outcomes[gold_outcomes.adjudication != "ambiguous"].copy()
    pres = span_cer[["page_id", "field", "version", "gold_start", "preserved"]].rename(
        columns={"gold_start": "start"})
    g = g.merge(pres, on=["page_id", "field", "version", "start"], how="left")
    g["preserved"] = g.preserved.where(g.version != "expert", True).fillna(False).astype(bool)
    g["stage"] = np.select(
        [~g.preserved, ~g.lenient, ~g.value_ok],
        ["lost_at_ocr", "lost_at_extraction", "lost_at_value"], "kept")
    g["still_found"] = (~g.preserved) & g.lenient
    prim = g[g.field.isin(PRIMARY_FIELDS)].assign(field="ALL_PRIMARY")
    g = pd.concat([g, prim], ignore_index=True)
    keys = ["run", "book", "version", "condition", "field"]
    t = (g.groupby(keys + ["stage"]).size().unstack("stage", fill_value=0)
         .reindex(columns=["lost_at_ocr", "lost_at_extraction", "lost_at_value", "kept"], fill_value=0))
    t["gold"] = t.sum(axis=1)
    t["of_which_still_found"] = g.groupby(keys).still_found.sum()
    for c in ("lost_at_ocr", "lost_at_extraction", "lost_at_value", "kept"):
        t[c + "_share"] = (t[c] / t.gold).round(3)
    return t.reset_index()


# ------------------------------------------------------------------ RQ3 evidence counters
_YEAR = re.compile(r"\b1[5-9]\d\d\b")
_MONTH = re.compile(r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)", re.I)


def type_check(field: str, value: str) -> tuple[bool, str]:
    """Deterministic check that a sliced value can be of its field's type.

    Deliberately loose: it catches outputs that cannot be right (empty, no letters, a
    'date' with neither a year nor a month, a whole sentence), not subtle mistakes.
    """
    v = (value or "").strip()
    if not v:
        return False, "empty"
    if len(v) > 100:
        return False, "longer than 100 characters"
    if field == "date":
        return (True, "") if _YEAR.search(v) or _MONTH.search(v) else (False, "no year or month")
    if not re.search(r"[A-Za-zÀ-ɏ]", v):
        return False, "no letters"
    if field in ("taxon", "person", "locality", "institution") and not re.search(r"[A-ZÀ-Þ]", v):
        return False, "no capital letter"
    if field in ("taxon", "vernacular") and re.search(r"\d", v):
        return False, "contains a digit"
    return True, ""


UNSUPPORTED = {"G0": {"not_found", "fuzzy"}, "G1": {"invalid_evidence", "silent_correction"}}


def evidence_counters(mentions: pd.DataFrame, pages: pd.DataFrame) -> pd.DataFrame:
    """RQ3, per book x version x condition. Needs no gold labels.

    unsupported        G0: not_found + fuzzy; G1: invalid_evidence + silent_correction
                       (the definitions fixed in PREREGISTRATION section 3)
    wrong_line         G1 only: quote exists on the page, but not on the cited line
    type_check_failed  located value fails type_check (unsupported claim, section 8 rule 7)
    """
    m = mentions.copy()
    m["page_id"] = m.page_id.astype(int)
    m = m.merge(pages.rename(columns={"PageID": "page_id"})[["page_id", "book"]], on="page_id")
    m["unsupported"] = [s in UNSUPPORTED.get(c, set()) for s, c in zip(m.status, m.condition)]
    m["wrong_line"] = m.status == "wrong_line"
    m["type_fail"] = [(v != "") and not type_check(f, v)[0] for f, v in zip(m.field, m.value)]
    m["line_label"] = m.had_line_label.astype(str) == "True"
    t = m.groupby(["book", "version", "condition"]).agg(
        outputs=("status", "size"), unsupported=("unsupported", "sum"), wrong_line=("wrong_line", "sum"),
        type_check_failed=("type_fail", "sum"), copied_line_label=("line_label", "sum")).reset_index()
    t["unsupported_rate"] = (t.unsupported / t.outputs).round(4)
    status = pd.crosstab([m.book, m.version, m.condition], m.status).add_prefix("status_").reset_index()
    return t.merge(status, on=["book", "version", "condition"])


# ------------------------------------------------------------------ request outcomes
def outcome_table(run_id: str, split: str) -> pd.DataFrame:
    """One status per request. `empty` is a valid response with no mentions; an API error,
    an unparseable response or a truncated one is its own status, never 'nothing found'."""
    run_dir = RESULTS / run_id
    path = run_dir / f"{split}_outputs.jsonl"
    if not path.exists():
        return pd.DataFrame()
    rows = []
    for line in open(path, encoding="utf-8"):
        r = json.loads(line)
        if r.get("error"):
            st = "api_error"
        elif r.get("stop_reason") in ("max_tokens", "MAX_TOKENS"):
            st = "truncated"
        elif r.get("parsed") is None:
            st = "parse_error"
        elif not r["parsed"].get("mentions"):
            st = "empty"
        else:
            st = "ok"
        rows.append({"run": run_id, "custom_id": r["custom_id"], "page_id": r["page_id"],
                     "version": r["version"], "condition": r["condition"], "outcome": st,
                     "attempts": r.get("attempts", 1)})
    return pd.DataFrame(rows)


# ------------------------------------------------------------------ RQ4 shadow evaluation
CLEAN = {"exact", "cross_line"}


MIN_UNFLAGGED = 10   # fewer unflagged predictions than this: no verdict (PREREGISTRATION section 9)


def flag_auto_accept(pred_a: pd.DataFrame, pred_b: pd.DataFrame,
                     b_answered: set | None = None) -> pd.DataFrame:
    """Mark model A's predictions as "proposed auto-accept" (never actually accepted in V1).

    A prediction is flagged when (1) model B extracted the same thing: same page, text version
    and field, with overlapping character ranges in the text both models read (one-to-one);
    (2) its evidence was located cleanly (status exact or cross_line); and (3) the value passes
    type_check. Returns pred_a with: agree, clean, type_ok, flagged, tier.
      tier 0  agree + clean + type ok   (flagged)
      tier 1  agree, but not clean or type check failed
      tier 2  no agreement, clean and type ok
      tier 3  no agreement and not clean
    Reviewers would work from tier 3 upwards; tier 0 is what a later version might skip.

    b_answered: (page_id, version) pairs for which model B gave a valid answer. A prediction
    on a page model B did not answer gets b_answered = False: it is not "disagreement", and
    rq4_summary / risk_coverage leave it out (and count it). None means B answered everywhere.
    """
    a = pred_a[~pred_a.outcome.str.startswith("set_aside")].copy().reset_index(drop=True)
    a["agree"] = False
    keys = ["page_id", "version", "field"]
    b_groups = {k: d for k, d in pred_b.groupby(keys)}
    for k, da in a.groupby(keys):
        db = b_groups.get(k)
        if db is None:
            continue
        P = [{"m_start": r.src_start, "m_end": r.src_end, "value": r.value} for r in da.itertuples()]
        G = [{"start": r.src_start, "end": r.src_end, "text": r.value, "adjudication": ""}
             for r in db.itertuples() if r.src_start is not None and not pd.isna(r.src_start)]
        for i, _ in assign_pairs(G, P, "lenient"):
            a.loc[da.index[i], "agree"] = True
    a["clean"] = a.status.isin(CLEAN)
    a["type_ok"] = [type_check(f, v)[0] for f, v in zip(a.field, a.value.fillna(""))]
    a["flagged"] = a.agree & a.clean & a.type_ok
    a["tier"] = np.select([a.flagged, a.agree, a.clean & a.type_ok], [0, 1, 2], 3)
    a["b_answered"] = True if b_answered is None else [
        (int(p), v) in b_answered for p, v in zip(a.page_id, a.version)]
    return a


def answered_pairs(outcomes: pd.DataFrame, run_id: str, condition: str = "G1") -> set:
    """(page_id, version) pairs where a run gave a valid answer (ok or empty) for a condition."""
    o = outcomes[(outcomes.run == run_id) & (outcomes.condition == condition)
                 & outcomes.outcome.isin(["ok", "empty"])]
    return {(int(p), v) for p, v in zip(o.page_id, o.version)}


def rq4_summary(flags: pd.DataFrame, gold_a: pd.DataFrame, gold_b: pd.DataFrame) -> pd.DataFrame:
    """Per book x version (primary fields): share flagged, precision of flagged and unflagged
    predictions (value level), their paired page-bootstrap difference, errors inside the flagged
    set (errors both models made together), and gold mentions both models missed."""
    f = flags[flags.field.isin(PRIMARY_FIELDS)]
    if "b_answered" not in f:
        f = f.assign(b_answered=True)
    rows = []
    for (book, version), d_all in f.groupby(["book", "version"]):
        d = d_all[d_all.b_answered]
        if d.empty:
            continue
        answered_pages = set(d.page_id)
        per = d.groupby("page_id").apply(lambda x: pd.Series({
            "f_tp": int((x.flagged & x.value_ok).sum()), "f_fp": int((x.flagged & ~x.value_ok).sum()),
            "u_tp": int((~x.flagged & x.value_ok).sum()), "u_fp": int((~x.flagged & ~x.value_ok).sum())}),
            include_groups=False).reset_index()
        A = per.rename(columns={"f_tp": "value_tp", "f_fp": "value_fp"}).assign(value_fn=0)
        B = per.rename(columns={"u_tp": "value_tp", "u_fp": "value_fp"}).assign(value_fn=0)
        diff = paired_bootstrap(A[["page_id", "value_tp", "value_fp", "value_fn"]],
                                B[["page_id", "value_tp", "value_fp", "value_fn"]], "value", "P")
        ga = gold_a[(gold_a.book == book) & (gold_a.version == version)
                    & gold_a.field.isin(PRIMARY_FIELDS) & (gold_a.adjudication != "ambiguous")
                    & gold_a.page_id.isin(answered_pages)]
        gb = gold_b[(gold_b.book == book) & (gold_b.version == version)
                    & gold_b.field.isin(PRIMARY_FIELDS) & (gold_b.adjudication != "ambiguous")
                    & gold_b.page_id.isin(answered_pages)]
        n_unflagged = int((~d.flagged).sum())
        both = ga.merge(gb, on=["page_id", "field", "start", "end"], suffixes=("_a", "_b"))
        rows.append({"book": book, "version": version, "predictions": len(d),
                     "flagged": int(d.flagged.sum()), "flagged_share": round(d.flagged.mean(), 3),
                     "precision_flagged": diff["a"], "precision_unflagged": diff["b"],
                     "diff": diff["diff"], "diff_lo": diff["lo"], "diff_hi": diff["hi"],
                     "unflagged": n_unflagged,
                     "verdict": (verdict(diff["lo"], diff["hi"], "at_least", 0.10)
                                 if n_unflagged >= MIN_UNFLAGGED else "too few to compare"),
                     "excluded_no_answer_from_b": int((~d_all.b_answered).sum()),
                     "errors_in_flagged_set": int((d.flagged & ~d.value_ok).sum()),
                     "gold": len(ga), "missed_by_model_a": int((~ga.lenient).sum()),
                     "missed_by_both": int((~both.lenient_a & ~both.lenient_b).sum())})
    return pd.DataFrame(rows)


def risk_coverage(flags: pd.DataFrame) -> pd.DataFrame:
    """Accept predictions tier by tier (most trusted first) and report, at each step, the share
    of predictions accepted (coverage) and the share of accepted ones that are wrong (risk).
    The review workload at that point is 1 - coverage."""
    f = flags[flags.field.isin(PRIMARY_FIELDS)]
    if "b_answered" in f:
        f = f[f.b_answered]   # a page model B did not answer says nothing about agreement
    rows = []
    for (book, version), d in f.groupby(["book", "version"]):
        for tier in sorted(d.tier.unique()):
            acc = d[d.tier <= tier]
            rows.append({"book": book, "version": version, "accept_up_to_tier": int(tier),
                         "accepted": len(acc), "coverage": round(len(acc) / len(d), 3),
                         "errors_accepted": int((~acc.value_ok).sum()),
                         "risk": round(float((~acc.value_ok).mean()), 3),
                         "left_for_review": len(d) - len(acc)})
    return pd.DataFrame(rows)


def read_mentions(run_id: str, split: str) -> pd.DataFrame:
    return pd.read_csv(RESULTS / run_id / f"{split}_mentions.csv", dtype=str, keep_default_na=False)


def sha256_file(path) -> str:
    import hashlib
    return hashlib.sha256(open(path, "rb").read()).hexdigest()
