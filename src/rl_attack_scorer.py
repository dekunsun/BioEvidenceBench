"""Module 2A of rl/PLAN_zh.md: attack the frozen scorer with adversarial model answers.

    python src/rl_attack_scorer.py

Each case is a model answer for one test page, built from the gold mentions of that page: the
"clean" answer quotes every single-line gold mention correctly; an attack changes one target
mention (or adds outputs) in one way. The answer then goes through exactly the frozen pipeline
(locate.locate_all -> score.char_map / map_span -> score.match_page; nothing is re-implemented),
and the result is compared with what the guide says should happen.

Conditions as in the study: G1 (line + verbatim quote, value sliced from the source by code),
G0 (value only, located in the source by code), G2 (quote for location, the model's `reading`
used as the value). Values in G0/G1 are sliced from the source, so a model's own spelling only
reaches the scorer in G2; that difference is part of what is tested.

`expected` is Claude's reading of the guide (ANNOTATION_GUIDE v0.10 and score.py's documented
rules), for Gloria to review; it is not a gold label. Verdicts:
  ok              the scorer did what the guide implies
  false_positive  credit for an answer that should not get it
  false_negative  no credit for an answer that should get it
  by_design       a documented leniency (e.g. case-insensitive values), listed so it is a choice
  finding         behaviour that is not wrong by the rules but matters for use as an RL reward
Writes rl/verifier_audit/adversarial/{cases.csv,REPORT.md}. No model is called.
"""
from __future__ import annotations

import argparse
import contextlib
import json
import re
import sys

import pandas as pd

import score as S
from common import DATA, ROOT
from locate import locate_all

OUT = ROOT / "rl" / "verifier_audit" / "adversarial"
GOLD = ROOT / "gold" / "gold_mentions_gloria_test.csv"
TEST = pd.read_csv(DATA / "sample_split.csv").query("split == 'test'")
PAGES = sorted(TEST.PageID.astype(int))
PATCH = False          # --patched: rl/verifier_audit/score_patched.py rules (frozen score.py untouched)


# ---------------------------------------------------------------- pipeline (frozen code only)
def run_answer(page_id: int, version: str, condition: str, mentions: list[dict], gold: pd.DataFrame):
    """Score one answer through the frozen pipeline. Returns (pred rows, per-field value counts,
    matched gold indices at value level, located statuses)."""
    src = S.page_text(version, page_id)
    loc_cond = "G1" if condition in ("G1", "G2") else "G0"
    located = locate_all(src, loc_cond, mentions)
    cmap = S.char_map(src, S.page_text("expert", page_id))
    rows = []
    for i, (m, r) in enumerate(zip(mentions, located)):
        value = m.get("reading") if condition == "G2" else r["value"]
        if PATCH:
            from score_patched import gate_value
            model_text = m.get("quote") if condition == "G1" else m.get("value")
            value = gate_value(condition, r["status"], value, model_text)
        span = S.map_span(cmap, r["start"], r["end"]) if r["start"] is not None else None
        rows.append({"i": i, "field": m["field"], "value": value, "status": r["status"],
                     "m_start": span[0] if span else None, "m_end": span[1] if span else None})
    pred = pd.DataFrame(rows, columns=["i", "field", "value", "status", "m_start", "m_end"])
    g_page = gold[gold.page_id == page_id]
    counts = S.match_page(g_page, pred)
    matched = set()
    for field in S.FIELDS:
        g = g_page[g_page.field == field]
        p = pred[pred.field == field].to_dict("records")
        for _, j in S.assign_pairs(g.to_dict("records"), p, "value"):
            matched.add(g.index[j])
    return pred, counts, matched


def totals(counts: dict, level: str = "value", fields=None) -> tuple[int, int, int, int]:
    fields = fields or S.PRIMARY_FIELDS
    t = [0, 0, 0, 0]
    for f in fields:
        for k, v in enumerate(counts[f][level]):
            t[k] += v
    return tuple(t)


def line_of(text: str, start: int) -> int:
    return text.count("\n", 0, start) + 1


def clean_answer(page_id: int, gold: pd.DataFrame, condition: str = "G1") -> list[dict]:
    """A correct answer: every single-line gold mention, quoted verbatim (G1/G2) or as value (G0)."""
    text = S.page_text("expert", page_id)
    out = []
    for idx, g in gold[gold.page_id == page_id].iterrows():
        if "\n" in g.text:
            continue
        m = {"field": g.field, "line": line_of(text, g.start), "quote": g.text, "value": g.text,
             "reading": g.text, "_gold": idx}
        out.append(m)
    return out


# ---------------------------------------------------------------- cases
def build_cases(gold: pd.DataFrame) -> list[dict]:
    expert = {p: S.page_text("expert", p) for p in PAGES}
    single = gold[~gold.text.str.contains("\n") & gold.field.isin(S.PRIMARY_FIELDS)]
    taxa = single[(single.field == "taxon") & (single.text.str.len() >= 8)]
    cases = []

    def add(cat, cond, pid, target_idx, attack, mutate, expected, note="", version="expert", extra=None):
        ans = clean_answer(pid, gold, cond)
        if target_idx is not None:
            ans = [mutate(dict(m)) if m["_gold"] == target_idx else m for m in ans]
        if extra:
            ans = ans + extra
        cases.append({"category": cat, "condition": cond, "page_id": pid, "version": version,
                      "target": target_idx, "attack": attack, "expected": expected, "note": note,
                      "from_clean": target_idx is not None and extra is None,
                      "answer": [{k: v for k, v in m.items() if not k.startswith("_")} for m in ans]})

    def pick(df, n, seed_cols=("page_id", "start")):
        return df.sort_values(list(seed_cols)).groupby("page_id").head(1).head(n)

    # 1 whole line quoted as the mention
    for idx, g in pick(taxa, 4).iterrows():
        line = expert[g.page_id].split("\n")[line_of(expert[g.page_id], g.start) - 1]
        if line.strip() == g.text:
            continue
        add("1_whole_line", "G1", g.page_id, idx, "quote the whole line instead of the name",
            lambda m, line=line: m | {"quote": line}, "not_credited")
    # 2 scattershot: every capitalised word also output as a taxon (metric-level check)
    for pid in PAGES[:4]:
        caps = sorted(set(re.findall(r"\b[A-Z][a-z]{3,}\b", expert[pid])))
        extra = []
        for w in caps:
            ln = next(i + 1 for i, l in enumerate(expert[pid].split("\n")) if re.search(rf"\b{w}\b", l))
            extra.append({"field": "taxon", "line": ln, "quote": w, "value": w, "reading": w})
        add("2_scattershot", "G1", pid, None, f"add {len(extra)} capitalised words as taxa",
            None, "f1_drops", extra=extra)
    # 3 normalisation: punctuation, case, quotes, Markdown on the value (G2: the model's own value)
    for idx, g in pick(taxa, 3).iterrows():
        for how, f in [("trailing period", lambda s: s + "."), ("upper case", str.upper),
                       ("curly quotes", lambda s: f"“{s}”"), ("Markdown italics", lambda s: f"*{s}*")]:
            add("3_normalisation", "G2", g.page_id, idx, f"reading with {how}",
                lambda m, f=f: m | {"reading": f(m["reading"])},
                "by_design" if how != "upper case" else "by_design_case",
                "norm_value strips edge punctuation, Markdown, curly quotes; casefolds")
    # 4 transcription fidelity: ligatures written out (G2 reading; G0 value; G1 quote)
    lig = single[single.text.str.contains("æ|œ")]
    for idx, g in pick(lig, 3).iterrows():
        mod = g.text.replace("æ", "ae").replace("œ", "oe")
        add("4_ligature", "G2", g.page_id, idx, f"reading `{mod}` for `{g.text}`",
            lambda m, mod=mod: m | {"reading": mod}, "not_credited", "guide: keep the book's spelling")
        add("4_ligature", "G0", g.page_id, idx, f"value `{mod}` for `{g.text}`",
            lambda m, mod=mod: m | {"value": mod}, "not_credited",
            "G0 locates the value in the source by fuzzy match, then slices the source")
        add("4_ligature", "G1", g.page_id, idx, f"quote `{mod}` for `{g.text}`",
            lambda m, mod=mod: m | {"quote": mod}, "not_credited",
            "G1 logs a silent correction, then slices the source")
    # 5 near-miss spelling (one letter changed)
    def one_letter(s):
        i = len(s) // 2
        return s[:i] + ("x" if s[i] != "x" else "z") + s[i + 1:]
    for idx, g in pick(taxa, 3).iterrows():
        bad = one_letter(g.text)
        for cond, key in [("G2", "reading"), ("G0", "value"), ("G1", "quote")]:
            add("5_near_miss", cond, g.page_id, idx, f"{key} `{bad}` for `{g.text}`",
                lambda m, key=key, bad=bad: m | {key: bad}, "not_credited")
    # 6 field mismatch
    for idx, g in pick(taxa, 3).iterrows():
        add("6_field", "G1", g.page_id, idx, "correct quote, field = locality",
            lambda m: m | {"field": "locality"}, "not_credited")
    # 7 position mismatch: a gold text printed more than once on the page, quoted at a line with no gold row
    for idx, g in single.sort_values(["page_id", "start"]).iterrows():
        t = expert[g.page_id]
        gold_lines = {line_of(t, s) for s in gold[(gold.page_id == g.page_id) & (gold.text == g.text)].start}
        other = [i + 1 for i, l in enumerate(t.split("\n")) if g.text in l and i + 1 not in gold_lines]
        if other:
            add("7_position", "G1", g.page_id, idx, f"quote placed on line {other[0]} (not a gold occurrence)",
                lambda m, ln=other[0]: m | {"line": ln}, "not_credited")
        if sum(c["category"] == "7_position" for c in cases) >= 3:
            break
    # 8 empty answer
    for pid in PAGES[:3]:
        cases.append({"category": "8_empty", "condition": "G1", "page_id": pid, "version": "expert",
                      "target": None, "attack": "answer {\"mentions\": []}", "expected": "zero_and_flagged",
                      "note": "", "answer": []})
    # 10 optional rows (sensitivity mode): output only later-rule rows
    later = gold[gold.get("later_rule", "").astype(str).str.len() > 0] if "later_rule" in gold else gold.iloc[0:0]
    for pid in sorted(later.page_id.unique())[:3]:
        t = expert[pid]
        ans = [{"field": g.field, "line": line_of(t, g.start), "quote": g.text, "value": g.text, "reading": g.text}
               for g in later[later.page_id == pid].itertuples() if "\n" not in g.text]
        cases.append({"category": "10_optional_rows", "condition": "G1", "page_id": pid, "version": "expert",
                      "target": None, "attack": f"output only the {len(ans)} later-rule rows",
                      "expected": "no_gain_sensitivity", "note": "scored with optional_after v0.6", "answer": ans})
    # 11 cross-line names: quote only the first line / quote whole with a space
    ml = gold[gold.text.str.contains("\n") & gold.field.isin(S.PRIMARY_FIELDS)]
    for idx, g in ml.sort_values(["page_id", "start"]).head(3).iterrows():
        t = expert[g.page_id]
        first = g.text.split("\n")[0].rstrip("-‐ ")
        ln = line_of(t, g.start)
        whole = re.sub(r"\s*\n\s*", " ", g.text)
        cases.append({"category": "11_cross_line", "condition": "G1", "page_id": g.page_id, "version": "expert",
                      "target": idx, "attack": f"quote only `{first}`", "expected": "not_credited", "note": "",
                      "answer": [{"field": g.field, "line": ln, "quote": first}]})
        cases.append({"category": "11_cross_line", "condition": "G1", "page_id": g.page_id, "version": "expert",
                      "target": idx, "attack": f"quote whole name `{whole}` on one line", "expected": "credited",
                      "note": "guide: a name broken across lines is quoted whole", "answer":
                      [{"field": g.field, "line": ln, "quote": whole}]})
    # 12 scan_text reading (typos in the transcription)
    st = gold[gold.scan_text.astype(str).str.len() > 0]
    for idx, g in st.iterrows():
        add("12_scan_text", "G2", g.page_id, idx, f"reading `{g.scan_text}` (the scan) for `{g.text}`",
            lambda m, s=g.scan_text: m | {"reading": s}, "credited", "scan_text is accepted")
    # 13 duplicates
    for idx, g in pick(taxa, 3).iterrows():
        t = expert[g.page_id]
        dup = {"field": "taxon", "line": line_of(t, g.start), "quote": g.text, "value": g.text, "reading": g.text}
        add("13_duplicate", "G1", g.page_id, idx, "same mention output twice", lambda m: m,
            "one_tp_one_fp", extra=[dup])
    # 14 superstring value (G2)
    for idx, g in pick(taxa, 3).iterrows():
        add("14_superstring", "G2", g.page_id, idx, "reading with the author appended",
            lambda m: m | {"reading": m["reading"] + ", Linn."}, "not_credited")
    # 15 legacy OCR: model quotes the OCR text exactly (G1) vs corrects it (G2)
    leg = gold.merge(TEST[["PageID"]].rename(columns={"PageID": "page_id"}), on="page_id")
    for pid in PAGES[:2]:
        src = S.page_text("legacy", pid)
        cmap = S.char_map(S.page_text("expert", pid), src)
        for g in gold[(gold.page_id == pid) & (gold.field == "taxon")].sort_values("start").itertuples():
            sp = S.map_span(cmap, g.start, g.end)
            if not sp:
                continue
            ocr = src[sp[0]:sp[1]]
            if ocr == g.text or "\n" in ocr or "\n" in g.text:
                continue
            ln = line_of(src, sp[0])
            cases.append({"category": "15_legacy_copy", "condition": "G1", "page_id": pid, "version": "legacy",
                          "target": g.Index, "attack": f"quote the OCR `{ocr}` for `{g.text}` (faithful copy)",
                          "expected": "not_credited", "note": "value is the misread text",
                          "answer": [{"field": "taxon", "line": ln, "quote": ocr}]})
            cases.append({"category": "15_legacy_copy", "condition": "G1", "page_id": pid, "version": "legacy",
                          "target": g.Index, "attack": f"quote the corrected `{g.text}` (not in the OCR line)",
                          "expected": "not_credited", "note": "G1 must not reward correcting the quote",
                          "answer": [{"field": "taxon", "line": ln, "quote": g.text}]})
            break
    return cases


# ---------------------------------------------------------------- run
def judge(case: dict, gold: pd.DataFrame, gold_opt: pd.DataFrame) -> dict:
    pid, cond, ver = case["page_id"], case["condition"], case["version"]
    g = gold_opt if case["category"] == "10_optional_rows" else gold
    pred, counts, matched = run_answer(pid, ver, cond, case["answer"], g)
    tp, fp, fn, amb = totals(counts, "value")
    statuses = ",".join(sorted(set(pred.status))) if len(pred) else ""
    target_credited = case["target"] in matched if case["target"] is not None else None
    exp = case["expected"]
    base_tp = None
    if case.get("from_clean"):
        base_tp = totals(run_answer(pid, ver, cond, clean_answer(pid, gold), gold)[1], "value")[0]
    if exp in ("not_credited", "credited"):
        want = exp == "credited"
        if base_tp is not None:
            # Judge by the page total, not the target row: when a name is printed twice, another
            # prediction can be relocated onto the target's position without any credit gained.
            credited = tp >= base_tp
            target_credited = credited
        else:
            credited = bool(target_credited)
        verdict = "ok" if credited == want else ("false_positive" if credited else "false_negative")
        if verdict == "false_positive" and cond in ("G0", "G1") and any(s in statuses for s in
                                                                         ("fuzzy", "silent_correction", "case_variant")):
            verdict = "finding"   # the model's own text was wrong, but code sliced the correct source text
    elif exp in ("by_design", "by_design_case"):
        credited = tp >= base_tp if base_tp is not None else bool(target_credited)
        verdict = "by_design" if credited else "false_negative"
    elif exp == "f1_drops":
        base = run_answer(pid, ver, cond, clean_answer(pid, gold), gold)[1]
        bt = totals(base, "value")
        f_base, f_att = S.prf(*bt[:3])[2], S.prf(tp, fp, fn)[2]
        verdict = "ok" if f_att < f_base else "false_positive"
        case["note"] = f"value F1 {f_base:.3f} -> {f_att:.3f}"
    elif exp == "one_tp_one_fp":
        base_fp = totals(run_answer(pid, ver, cond, clean_answer(pid, gold), gold)[1], "value")[1]
        verdict = "ok" if target_credited and fp == base_fp + 1 else "false_positive"
    elif exp == "zero_and_flagged":
        verdict = "finding"   # scored 0 like any miss; the scorer itself cannot tell "empty" from "found nothing"
        case["note"] = f"tp {tp}, fn {fn}: the same as a model that finds nothing"
    elif exp == "no_gain_sensitivity":
        verdict = "ok" if tp == 0 and fp == 0 else "false_positive"
        case["note"] += f"; tp {tp}, fp {fp}, on optional rows {amb}"
    else:
        verdict = "?"
    return case | {"target_text": gold.loc[case["target"], "text"] if case["target"] is not None else "",
                   "target_credited": target_credited, "value_tp": tp, "value_fp": fp, "value_fn": fn,
                   "on_optional": amb, "statuses": statuses, "verdict": verdict}


def main() -> None:
    global PATCH
    ap = argparse.ArgumentParser()
    ap.add_argument("--patched", action="store_true")
    PATCH = ap.parse_args().patched
    ctx = contextlib.nullcontext()
    if PATCH:
        sys.path.insert(0, str(ROOT / "rl" / "verifier_audit"))
        from score_patched import patched
        ctx = patched()
    with ctx:
        _main()


def _main() -> None:
    gold = S.load_gold(GOLD)
    gold_opt = S.load_gold(GOLD, optional_after="v0.6")
    cases = build_cases(gold)
    res = [judge(c, gold, gold_opt) for c in cases]
    df = pd.DataFrame(res)
    df["answer"] = df.answer.map(lambda a: json.dumps(a, ensure_ascii=False))
    OUT.mkdir(parents=True, exist_ok=True)
    cols = ["category", "condition", "version", "page_id", "target_text", "attack", "expected", "verdict",
            "target_credited", "value_tp", "value_fp", "value_fn", "on_optional", "statuses", "note", "answer"]
    df[cols].to_csv(OUT / ("cases_patched.csv" if PATCH else "cases.csv"), index=False)
    print(df.groupby(["category", "condition", "verdict"]).size().to_string())


if __name__ == "__main__":
    main()
