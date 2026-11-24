"""本草綱目 pilot: Claude extracts mentions from the six scan-verified half-leaves, scored against the
author's labels (exploratory, dev: the guide and these labels came from the same pages).

    python src/bencao_extract.py run   --model claude-opus-5-5 --max-usd 1   # paid; approved by the author, 2026-11-24 ("跑吧")
    python src/bencao_extract.py run   --text paddleocr                      # same, on an OCR level (2026-11-24, "继续做吧")
    python src/bencao_extract.py relocate <run folder>   # re-locate saved answers, no API call
    python src/bencao_extract.py score <run folder>
    python src/bencao_extract.py summary <run folder> ...   # one table across text versions

Design as in the English books' G1 condition: the input lines are numbered; for each mention the model
returns the field, the line number and a verbatim quote; code finds the quote in that line (or across the
break into the next line, for a name split by a column break) and slices the value from the reference
text. The model never writes a value itself. Quotes that are not in the line are counted as invalid evidence.

Input: `data/bencao/verified_plain/<half-leaf>.txt` (Kanripo text corrected against the scan by the
author), one manuscript column per line. Prompt examples come only from half-leaves 036-1a and 036-2a,
which are not among the six. Gold: `gold/gold_mentions_bencao_gloria.csv` (rows with
`adjudication = expert_pending` are optional: neither required nor counted as false positives).

Run folder results/<stamp>_bencao_extract_<model>/: config.json (model, prompt, schema, input hashes,
decoding), outputs.jsonl (raw answers, usage, cost), mentions.csv (located spans), and after `score`:
scores.csv (exact and overlap P/R/F1 per field and for the primary fields), errors.csv.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "bencao"
PAGES = ["036-1b", "036-5a", "036-7b", "036-12b", "036-13a", "036-30a"]
FIELDS = ["taxon", "person", "locality", "cited_work", "substance"]
PRIMARY = ["taxon", "person", "locality", "cited_work"]           # substance is scored separately
PRICES = {"claude-opus-5-5": (4.0, 20.0), "claude-sonnet-5-5": (2.0, 10.0), "claude-haiku-5-5": (0.10, 0.50)}
PROMPT_VERSION = "bencao-p2-guide-v0.4"   # p1 (guide v0.3) runs: results/20261124-08*_bencao_extract_*

SYSTEM = ("You extract named entities from the 本草綱目 (Siku quanshu manuscript copy). You never rewrite the text: "
          "for every mention you give the line number and copy the characters exactly as they appear on that line.")
RULES = """Find every mention of these fields in the numbered text below (one manuscript column per line; small
two-column notes are already joined, right sub-column first).

Fields
- taxon: the name of a drug, plant or animal, and any name used for a drug: entry headings, alternative names
  listed under 釋名 (set alias = true for these), every drug in a prescription, organisms named in comparisons
  (槐 in 甘草枝葉悉如槐), and regional drug names made of a place plus a drug name (one span; the place inside it
  is not labelled again).
- person: a named person, including short forms such as 𢎞景, 權, 頌, 時珍.
- locality: a place. A chain of places written together from wide to narrow (region, then county, mountain or
  district) is split: each named place is its own locality (江南宣州 → 江南, 宣州). A generic word written
  directly after a name stays in its span (name + 川谷, 山谷 or 山 is one span); a generic word joined by 之 does
  not (X之山 → X). Generic words alone are not labelled. The name of a people used for its land is a locality.
- cited_work: a book cited as a source, including the source tags in small notes (別録 after an alternative name)
  and a book plus one of its sections written together as one span. Generic references are not labelled.
- substance: minerals, water, earth and other non-organic drugs.

Rules
- Copy characters exactly, including variant and taboo forms (宻, 𢎞, 䖅); never normalise or correct.
- Every occurrence is its own mention, in reading order.
- A name split by a line break: give the line where it starts and quote the whole name without the break.
- Running heads (欽定四庫全書, the volume title) are not mentions.

Example (from half-leaf 036-1a, not part of this task):
  line 6: 釋名宻甘别録宻草别録美草别録 → taxon 宻甘 (alias), cited_work 别録, taxon 宻草 (alias), cited_work 别録, taxon 美草 (alias), cited_work 别録
  line 7: 别録𢎞景曰此草最為衆藥之主 → cited_work 别録, person 𢎞景
"""
SCHEMA = {"type": "object", "properties": {"mentions": {"type": "array", "items": {
    "type": "object", "properties": {"field": {"type": "string", "enum": FIELDS}, "line": {"type": "integer"},
                                     "quote": {"type": "string"}, "alias": {"type": "boolean"}},
    "required": ["field", "line", "quote", "alias"], "additionalProperties": False}}},
    "required": ["mentions"], "additionalProperties": False}


TEXTS = ["verified_plain", "claude_opus", "claude_haiku", "paddleocr"]   # scan-verified reference, then OCR levels


def ref_lines(pb: str, text: str = "verified_plain") -> list[str]:
    return (DATA / text / f"{pb}.txt").read_text(encoding="utf-8").splitlines()


def numbered(lines: list[str]) -> str:
    return "\n".join(f"{i:>2} | {l}" for i, l in enumerate(lines, 1))


def locate(lines: list[str], mentions: list[dict]) -> list[dict]:
    """Slice each quote from its line: next free occurrence in reading order; if absent, try the quote split
    across the break into the next line. Unfound quotes are kept with status `invalid_evidence`."""
    starts = [sum(len(x) + 1 for x in lines[:k]) for k in range(len(lines))]
    taken: set[tuple[int, int]] = set()
    last: dict[int, int] = {}                     # line -> offset of the previous mention found on it
    out = []

    def free(line: str, ln: int, q: str, pos: int) -> int:
        while True:
            k = line.find(q, pos)
            if k < 0 or (starts[ln - 1] + k, len(q)) not in taken:
                return k
            pos = k + 1

    for m in mentions:
        ln, q = m["line"], m["quote"]
        rec = {**m, "status": "invalid_evidence", "start": None, "end": None, "value": None}
        if 1 <= ln <= len(lines) and q:
            line = lines[ln - 1]
            # Mentions come in reading order, so look after the previous one on this line first
            # (added 2026-11-24 after the first run placed a later 乾薑 at an earlier, unlabelled 乾薑湯).
            k = free(line, ln, q, last.get(ln, 0))
            if k < 0:
                k = free(line, ln, q, 0)
            if k >= 0:
                s, e = starts[ln - 1] + k, starts[ln - 1] + k + len(q)
                rec.update(status="ok", start=s, end=e, value=q)
            elif ln < len(lines):
                for cut in range(1, len(q)):
                    if line.endswith(q[:cut]) and lines[ln].startswith(q[cut:]):
                        s = starts[ln - 1] + len(line) - cut
                        rec.update(status="ok_cross_line", start=s, end=s + len(q) + 1, value=q[:cut] + "\n" + q[cut:])
                        break
            if rec["start"] is not None:
                taken.add((rec["start"], len(q)))
                if rec["status"] == "ok":
                    last[ln] = rec["start"] - starts[ln - 1]
        out.append(rec)
    return out


def run(model: str, max_usd: float, text: str = "verified_plain") -> None:
    import anthropic
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M")
    tag = "" if text == "verified_plain" else f"_{text}"
    out = ROOT / "results" / f"{stamp}_bencao_extract_{model}{tag}"
    out.mkdir(parents=True)
    client = anthropic.Anthropic(api_key=os.environ["EVAL_ANTHROPIC_API_KEY"], max_retries=4)
    spent, recs, rows, hashes = 0.0, [], [], {}
    for pb in PAGES:
        lines = ref_lines(pb, text)
        numtext = numbered(lines)
        hashes[pb] = hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest()
        if spent > max_usd:
            recs.append({"half_leaf": pb, "error": "cap reached, not sent"})
            continue
        user = RULES + "\nText (half-leaf " + pb + "):\n" + numtext
        msg = client.messages.create(model=model, max_tokens=8000, system=SYSTEM,
                                     messages=[{"role": "user", "content": user}],
                                     output_config={"effort": "medium", "format": {"type": "json_schema", "schema": SCHEMA}})
        raw = "".join(b.text for b in msg.content if b.type == "text")
        usd = (msg.usage.input_tokens * PRICES[model][0] + msg.usage.output_tokens * PRICES[model][1]) / 1e6
        spent += usd
        ments = json.loads(raw)["mentions"]
        for r in locate(lines, ments):
            rows.append({"page_id": pb, **r})
        recs.append({"half_leaf": pb, "raw": raw, "stop_reason": msg.stop_reason, "usd": round(usd, 5),
                     "usage": {"input_tokens": msg.usage.input_tokens, "output_tokens": msg.usage.output_tokens}})
        print(pb, len(ments), "mentions", f"${usd:.4f}")
    (out / "outputs.jsonl").write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in recs) + "\n", encoding="utf-8")
    pd.DataFrame(rows).to_csv(out / "mentions.csv", index=False)
    (out / "config.json").write_text(json.dumps({
        "run_id": out.name, "model": model, "prompt_version": PROMPT_VERSION, "effort": "medium", "max_tokens": 8000,
        "temperature": "provider default", "system": SYSTEM, "rules": RULES, "schema": SCHEMA,
        "text": text, "input": f"data/bencao/{text}/<half-leaf>.txt, numbered lines", "input_sha256": hashes,
        "max_usd": max_usd, "usd_total": round(spent, 4), "exploratory": True, "dev": True,
        "approved": "author, 2026-11-24 (\"跑吧\")"}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{out.name}: ${spent:.4f}")


def prf(tp: int, fp: int, fn: int) -> tuple[float, float, float]:
    p = tp / (tp + fp) if tp + fp else 0.0
    r = tp / (tp + fn) if tp + fn else 0.0
    return round(p, 3), round(r, 3), round(2 * p * r / (p + r), 3) if p + r else 0.0


def relocate(run_dir: str) -> None:
    """Re-run the locator on the saved raw answers (no API call)."""
    run = Path(run_dir)
    text = json.loads((run / "config.json").read_text(encoding="utf-8")).get("text", "verified_plain")
    rows = []
    for line in (run / "outputs.jsonl").read_text(encoding="utf-8").splitlines():
        r = json.loads(line)
        if "raw" in r:
            for x in locate(ref_lines(r["half_leaf"], text), json.loads(r["raw"])["mentions"]):
                rows.append({"page_id": r["half_leaf"], **x})
    pd.DataFrame(rows).to_csv(run / "mentions.csv", index=False)


def to_reference(hyp: str, ref: str) -> list[int | None]:
    """For each character offset in an OCR text, its offset in the reference (character alignment by
    Levenshtein opcodes); None for OCR characters with no counterpart (inserted by the OCR)."""
    import rapidfuzz.distance.Levenshtein as Lev
    m: list[int | None] = [None] * (len(hyp) + 1)
    for op in Lev.opcodes(hyp, ref):
        if op.tag in ("equal", "replace"):
            for k in range(op.src_end - op.src_start):
                m[op.src_start + k] = op.dest_start + min(k, op.dest_end - op.dest_start - 1)
    m[len(hyp)] = len(ref)
    return m


def aligned(pred: pd.DataFrame, text: str) -> pd.DataFrame:
    """Move predicted spans from OCR offsets to reference offsets. Spans with no aligned character are
    dropped from span scoring and counted as `unaligned` (they still count in value scoring)."""
    if text == "verified_plain":
        pred["aligned"] = True
        return pred
    rows = []
    for pb, g in pred.groupby("page_id"):
        hyp = "\n".join(ref_lines(pb, text))
        ref = "\n".join(ref_lines(pb))
        m = to_reference(hyp, ref)
        for r in g.itertuples(index=False):
            pos = [m[k] for k in range(r.start, r.end) if m[k] is not None]
            d = r._asdict()
            d.update(aligned=bool(pos), start=min(pos) if pos else -1, end=max(pos) + 1 if pos else -1)
            rows.append(d)
    return pd.DataFrame(rows)


def value_scores(pred: pd.DataFrame, gold: pd.DataFrame, folded: bool = False) -> list[dict]:
    """Value-level P/R/F1: per half-leaf and field, the multiset of extracted strings against the gold
    strings (line breaks removed). Comparable across text versions without alignment, as in the English
    books' value F1. Optional (expert_pending) gold values neither count nor penalise."""
    from collections import Counter
    from bencao_variants import fold
    norm = (lambda t: fold(t.replace("\n", ""))) if folded else (lambda t: t.replace("\n", ""))
    out = []
    for name, fields in [(f, [f]) for f in FIELDS] + [("ALL_PRIMARY", PRIMARY)]:
        tp = fp = fn = 0
        for pb in PAGES:
            for f in fields:
                g = gold[(gold.page_id == pb) & (gold.field == f)]
                req = Counter(norm(t) for t in g[g.adjudication != "expert_pending"].text)
                opt = Counter(norm(t) for t in g[g.adjudication == "expert_pending"].text)
                p = Counter(norm(str(v)) for v in pred[(pred.page_id == pb) & (pred.field == f)].value)
                hit = req & p
                rest = p - hit
                fp += sum((rest - opt).values())
                tp += sum(hit.values())
                fn += sum((req - hit).values())
        P, R, F = prf(tp, fp, fn)
        out.append({"field": name, "match": "value_folded" if folded else "value", "tp": tp, "fp": fp, "fn": fn, "precision": P, "recall": R, "f1": F})
    return out


def preservation(text: str) -> dict:
    """Share of required primary gold values whose exact string survives in a text version (line breaks
    removed from both; a value counts as many times as it occurs, capped by the number of gold rows)."""
    from collections import Counter
    gold = pd.read_csv(ROOT / "gold" / "gold_mentions_bencao_gloria.csv", keep_default_na=False)
    gold = gold[gold.field.isin(PRIMARY) & (gold.adjudication != "expert_pending")]
    from bencao_variants import fold
    kept = kept_f = total = 0
    for pb in PAGES:
        flat = "".join(ref_lines(pb, text))
        for v, n in Counter(t.replace("\n", "") for t in gold[gold.page_id == pb].text).items():
            kept += min(n, flat.count(v)); kept_f += min(n, fold(flat).count(fold(v))); total += n
    return {"text": text, "gold_values": total, "preserved": kept, "share": round(kept / total, 3),
            "share_folded": round(kept_f / total, 3)}   # folded: glyph variants and missing-stroke forms only


def score(run_dir: str) -> None:
    run = Path(run_dir)
    text = json.loads((run / "config.json").read_text(encoding="utf-8")).get("text", "verified_plain")
    pred = pd.read_csv(run / "mentions.csv", keep_default_na=False)
    pred = pred[pred.status.str.startswith("ok")].copy()
    pred["start"], pred["end"] = pred.start.astype(float).astype(int), pred.end.astype(float).astype(int)
    vals = pred.copy()
    pred = aligned(pred, text)
    unaligned = int((~pred.aligned).sum())
    pred = pred[pred.aligned]
    gold = pd.read_csv(ROOT / "gold" / "gold_mentions_bencao_gloria.csv", keep_default_na=False)
    rows, errs = [], []
    for name, fields in [(f, [f]) for f in FIELDS] + [("ALL_PRIMARY", PRIMARY)]:
        for mode in ("exact", "overlap"):
            tp = fp = fn = 0
            for pb in PAGES:
                g = gold[(gold.page_id == pb) & gold.field.isin(fields)]
                req = g[g.adjudication != "expert_pending"]
                opt = g[g.adjudication == "expert_pending"]
                p = pred[(pred.page_id == pb) & pred.field.isin(fields)]
                used = set()
                hit = lambda a, b: (a.start == b.start and a.end == b.end) if mode == "exact" else (a.start < b.end and b.start < a.end)
                for pr in p.itertuples():
                    match = next((gr for gr in req.itertuples() if gr.field == pr.field and gr.Index not in used and hit(pr, gr)), None)
                    if match is not None:
                        used.add(match.Index); tp += 1
                    elif any(gr.field == pr.field and hit(pr, gr) for gr in opt.itertuples()):
                        continue                                   # optional gold row: not counted
                    else:
                        fp += 1
                        if mode == "exact" and name == "ALL_PRIMARY":
                            errs.append({"page_id": pb, "kind": "extra", "field": pr.field, "line": pr.line, "text": pr.value})
                missed = req[~req.index.isin(used)]
                fn += len(missed)
                if mode == "exact" and name == "ALL_PRIMARY":
                    errs += [{"page_id": pb, "kind": "missed", "field": m.field, "line": m.line, "text": m.text} for m in missed.itertuples()]
            P, R, F = prf(tp, fp, fn)
            rows.append({"field": name, "match": mode, "tp": tp, "fp": fp, "fn": fn, "precision": P, "recall": R, "f1": F})
    gold_all = gold
    rows += value_scores(vals, gold_all) + value_scores(vals, gold_all, folded=True)
    s = pd.DataFrame(rows)
    s.insert(0, "text", text)
    s.to_csv(run / "scores.csv", index=False)
    pd.DataFrame(errs).to_csv(run / "errors.csv", index=False)
    allp = pd.read_csv(run / "mentions.csv", keep_default_na=False)
    print(s.to_string(index=False))
    print("invalid evidence:", (allp.status == "invalid_evidence").sum(), "of", len(allp), "| unaligned:", unaligned)


def summary(run_dirs: list[str]) -> None:
    """One table across text versions: name preservation and value F1 per field (results/bencao_pilot/)."""
    rows = []
    for d in run_dirs:
        sc = pd.read_csv(Path(d) / "scores.csv")
        text = sc.text.iloc[0]
        row = {"text": text, "run": Path(d).name, **{k: v for k, v in preservation(text).items() if k != "text"}}
        for _, r in sc[sc.match.isin(["value", "value_folded", "exact"])].iterrows():
            row[f"{r.field}_{r.match}_f1"] = r.f1
        rows.append(row)
    pv = json.loads((Path(run_dirs[0]) / "config.json").read_text(encoding="utf-8"))["prompt_version"]
    name = "ocr_to_extraction.csv" if pv.startswith("bencao-p1") else f"ocr_to_extraction_{pv.split('-')[1]}.csv"
    out = ROOT / "results" / "bencao_pilot" / name
    pd.DataFrame(rows).to_csv(out, index=False)
    print(pd.DataFrame(rows)[["text", "share", "share_folded", "ALL_PRIMARY_value_f1", "ALL_PRIMARY_value_folded_f1",
                              "taxon_value_f1", "person_value_f1", "locality_value_f1", "cited_work_value_f1"]].to_string(index=False))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["run", "relocate", "score", "summary"])
    ap.add_argument("run_dir", nargs="*")
    ap.add_argument("--model", default="claude-opus-5-5", choices=list(PRICES))
    ap.add_argument("--max-usd", type=float, default=1.0)
    ap.add_argument("--text", default="verified_plain", choices=TEXTS)
    a = ap.parse_args()
    if a.cmd == "run":
        run(a.model, a.max_usd, a.text)
    elif a.cmd == "relocate":
        relocate(a.run_dir[0])
    elif a.cmd == "summary":
        summary(a.run_dir)
    else:
        score(a.run_dir[0])
