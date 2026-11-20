"""Exploratory conditions on the 16 test pages, decided after unsealing (DEVIATIONS.md).

    python src/run_exploratory.py --cond G2 --versions legacy,modern_tesseract,... [--max-usd N]
    python src/run_exploratory.py --cond V1
    python src/run_exploratory.py --cond V2 --versions legacy,modern_dots-mocr
    python src/run_exploratory.py --score

Three questions the frozen design cannot answer, each a new condition. The field definitions
are the frozen prompt's (prompts.SYSTEM, p4-guide-v0.6) word for word; only its opening
paragraph, which forbids any correction, is replaced. prompts.py and the scorer are not changed.
  G2  repair   numbered OCR text in; per mention the model returns line + VERBATIM quote (as G1,
               checked against the line) and, separately, `reading`: what the printed page most
               likely says there, with OCR misreadings put right. Scored on `reading`. Question:
               can an LLM's repair stand in for re-OCR? (On the expert text it measures harm:
               changes to text that was already right.)
  V1  vision   the page image only, no text. Values are transcribed from the image. Question:
               is a separate OCR step needed at all?
  V2  both     page image + numbered OCR text, G2's output; `reading` follows the image.
               Question: does the image put OCR errors right?
Scoring (--score): `positions` (G2, V2) through score.py exactly like the frozen runs, with the
reading as value; and `bag` (all conditions, and the frozen G1 runs for comparison): per page and
field, the multiset of normalised values against the gold texts, because V1 has no positions.
Outputs: results/<stamp>_explore_<cond>/ with config, prompts, raw answers, mentions; and
results/exploratory_conditions/REPORT.md.
"""
from __future__ import annotations

import argparse
import base64
import io
import json
import os
import sys
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

import pandas as pd

from common import DATA, ROOT
from locate import locate_all
from prompts import FIELDS, PROMPT_VERSION, SCHEMA_G1, SYSTEM, TASK_G1, number_lines
from run_extraction import text_path
from score import load_gold, norm_value, score_run_detail

MODEL = "claude-opus-5-5"
# $ per million tokens (input, output), Claude API pricing 2026-11
PRICES = {"claude-opus-5-5": (4.0, 20.0), "claude-sonnet-5-5": (2.0, 10.0), "claude-haiku-5-5": (0.10, 0.50),
          "claude-fable-5-2": (8.0, 40.0),
          "gemini-4-carbon": (2.0, 10.0)}   # sync, promo price to 2026-11-30 (gemini_backend.PRICES)
RESULTS = ROOT / "results"
IMAGES = ROOT / "data" / "cache" / "images"
_OPENING = SYSTEM.split("\n\n", 1)[0]
_DEFS = SYSTEM.split("\n\n", 1)[1]
assert _OPENING.startswith("You extract") and "Never correct" in _OPENING

OPEN_REPAIR = ("You extract biodiversity occurrence information from one page of a historical natural-history "
               "book (19th or early 20th century). The page is given as numbered lines of raw OCR or a "
               "transcription, which may contain recognition errors, odd spacing, broken words and stray "
               "characters. For every mention you give two things. QUOTE: the mention copied character for "
               "character from its line, errors included, never corrected. READING: what the printed page most "
               "likely says at that place, with OCR recognition errors put right (misread or missing letters, "
               "split or joined words, stray characters). Do nothing else to the reading: keep the book's own "
               "spelling, capitals, ligatures (æ, œ) and abbreviations; never modernise, expand or translate. "
               "When the text is already right, the reading equals the quote.")
OPEN_REPAIR_IMG = OPEN_REPAIR.replace(
    "what the printed page most likely says at that place",
    "what the page image shows at that place (read it from the image)")
OPEN_VISION = ("You extract biodiversity occurrence information from one page of a historical natural-history "
               "book (19th or early 20th century), given as an image of the printed page. Read the page and "
               "report every mention transcribed exactly as printed: keep the book's own spelling, capitals, "
               "small capitals as capitals, ligatures (æ, œ), abbreviations and punctuation inside the mention. "
               "Never correct, normalise, expand or modernise anything.")

TASK_REPAIR = """Extract all mentions from the page below. For each mention give its field, the number of the line where it appears, the quote (an exact copy from that line, as in a citation that is checked automatically; a mention broken across two lines is quoted whole, the line break written as one space and a printed hyphen kept) and the reading. Never include the line labels (such as "L07|") in a quote or a reading.

<page>
{numbered_text}
</page>"""
TASK_REPAIR_IMG = TASK_REPAIR.replace("Extract all mentions from the page below.",
                                      "The image shows the printed page; the text below is an OCR of it. Extract all mentions.")
TASK_VISION = "Extract all mentions from the page in the image, in reading order. For each mention give its field and its value as printed."

_F = {"type": "string", "enum": FIELDS}
SCHEMA_REPAIR = {"type": "object", "additionalProperties": False, "required": ["mentions"],
                 "properties": {"mentions": {"type": "array", "items": {
                     "type": "object", "additionalProperties": False,
                     "required": ["field", "line", "quote", "reading"],
                     "properties": {"field": _F, "line": {"type": "integer"}, "quote": {"type": "string"},
                                    "reading": {"type": "string"}}}}}}
SCHEMA_VISION = {"type": "object", "additionalProperties": False, "required": ["mentions"],
                 "properties": {"mentions": {"type": "array", "items": {
                     "type": "object", "additionalProperties": False, "required": ["field", "value"],
                     "properties": {"field": _F, "value": {"type": "string"}}}}}}

# V3: as V1, plus where each mention is on the page image (Level 3 grounding without any OCR).
TASK_BOX = ("Extract all mentions from the page in the image, in reading order. For each mention give its field, "
            "its value as printed, and the box around it on the image as [x0, y0, x1, y1] on a 0-1000 scale "
            "(0,0 = top left corner of the image, 1000,1000 = bottom right). If a mention runs over two lines, "
            "give the box around its first line.")
SCHEMA_BOX = {"type": "object", "additionalProperties": False, "required": ["mentions"],
              "properties": {"mentions": {"type": "array", "items": {
                  "type": "object", "additionalProperties": False, "required": ["field", "value", "box"],
                  "properties": {"field": _F, "value": {"type": "string"},
                                 "box": {"type": "array", "items": {"type": "integer"}}}}}}}

CONDS = {"G1F": (_OPENING, TASK_G1, SCHEMA_G1, False, True),   # the frozen G1 prompt, word for word
         "V3": (OPEN_VISION, TASK_BOX, SCHEMA_BOX, True, False),
         "G2": (OPEN_REPAIR, TASK_REPAIR, SCHEMA_REPAIR, False, True),
         "V1": (OPEN_VISION, TASK_VISION, SCHEMA_VISION, True, False),
         "V2": (OPEN_REPAIR_IMG, TASK_REPAIR_IMG, SCHEMA_REPAIR, True, True)}


def image_block(page_id: int) -> dict:
    """The page scan as JPEG, long side 2000 px (the API scales larger images down anyway)."""
    from PIL import Image
    im = Image.open(next(IMAGES.glob(f"{page_id}.*"))).convert("RGB")
    im.thumbnail((2000, 2000))
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=90)
    return {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg",
                                         "data": base64.b64encode(buf.getvalue()).decode()}}


def load_pages(which: str) -> pd.DataFrame:
    """test = the 16 locked test pages; pcas = the 8 PCAS botany pages (external case, reported
    separately; text version `pcas_legacy` = data/pcas/legacy copied to data/text/pcas_legacy)."""
    if which == "pcas":
        return pd.read_csv(DATA / "pcas" / "pcas_pages.csv").rename(columns={"page_id": "PageID"}).assign(book="PCAS")
    return pd.read_csv(DATA / "sample_split.csv").query("split == 'test'")


def run(cond: str, versions: list[str], max_usd: float, model: str = MODEL, which: str = "test",
        limit_pages: int = 0, page_ids: list[int] | None = None) -> None:
    opening, task, schema, use_img, use_text = CONDS[cond]
    system = opening + "\n\n" + _DEFS
    pages = load_pages(which)
    if limit_pages:                     # pilot: the first N pages of each book, in sample order
        pages = pages.groupby("book", group_keys=False).head((limit_pages + 1) // 2).head(limit_pages)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M")
    short = "" if model == MODEL else "_" + model.removeprefix("claude-")
    if limit_pages:
        short += f"_pilot{limit_pages}"
    if page_ids:                        # diagnostic resend of named pages; never scored
        pages = pages[pages.PageID.isin(page_ids)]
        short += "_diag"
    run_id = f"{stamp}_explore_{cond}{short}" + ("_pcas" if which == "pcas" else "")
    out = RESULTS / run_id
    (out / "prompts").mkdir(parents=True)
    (out / "prompts" / "system.txt").write_text(system, encoding="utf-8")
    (out / "prompts" / "task.txt").write_text(task, encoding="utf-8")
    (out / "prompts" / "schema.json").write_text(json.dumps(schema, indent=2), encoding="utf-8")
    versions = versions if use_text else ["image"]
    jobs = [(int(p.PageID), p.book, v) for p in pages.itertuples() for v in versions]
    gemini = model.startswith("gemini")
    if gemini:
        import gemini_backend as gb
        client = gb.make_client(os.environ["GEMINI_API_KEY"])
    else:
        import anthropic
        client = anthropic.Anthropic(api_key=os.environ["EVAL_ANTHROPIC_API_KEY"], max_retries=4)
    spent = []

    def one_gemini(job):
        """Same prompt text, image and schema as the Claude path; sync generateContent with the JSON
        schema enforced (the Batch API did not enforce it, gemini_backend.py). Thinking: model default."""
        from google.genai import types
        pid, book, v = job
        if sum(spent) > max_usd:
            return {"page_id": pid, "version": v, "error": "cap reached, not sent"}
        parts = []
        if use_img:
            b = base64.b64decode(image_block(pid)["source"]["data"])
            parts.append(types.Part.from_bytes(data=b, mime_type="image/jpeg"))
        text = text_path(v, pid).read_text(encoding="utf-8") if use_text else ""
        parts.append(types.Part.from_text(text=task.format(numbered_text=number_lines(text)) if use_text else task))
        rec = {"page_id": pid, "book": book, "version": v, "condition": cond, "model": model,
               "sent_at": datetime.now(timezone.utc).isoformat(timespec="seconds")}
        cfg = types.GenerateContentConfig(system_instruction=system, response_mime_type="application/json",
                                          response_json_schema=schema, max_output_tokens=gb.MAX_OUTPUT_TOKENS)
        for attempt in (1, 2):
            try:
                resp = client.models.generate_content(model=model, contents=[types.Content(role="user", parts=parts)],
                                                      config=cfg)
                d = resp.model_dump(mode="json", exclude_none=True)
                usage = gb.usage_from(d.get("usage_metadata"))
                usd = gb.cost_of(usage, model, batch=False)
                spent.append(usd)
                cands = d.get("candidates") or []
                raw = gb._answer_text(d)
                rec |= {"raw": raw, "stop_reason": cands[0].get("finish_reason") if cands else None,
                        "usd": round(usd, 5), "attempts": attempt, "usage": usage,
                        "model_version": d.get("model_version")}
                rec.pop("error", None)
                parsed, dev = gb.check_shape(json.loads(raw), schema)
                rec["schema_deviation"] = dev
                if parsed is None:
                    raise ValueError(dev)
                rec["parsed"] = parsed
                return rec
            except Exception as e:                     # one retry, as in the frozen runs
                rec["error"] = repr(e)[:500]
        return rec

    def one(job):
        pid, book, v = job
        if sum(spent) > max_usd:
            return {"page_id": pid, "version": v, "error": "cap reached, not sent"}
        content = []
        if use_img:
            content.append(image_block(pid))
        text = text_path(v, pid).read_text(encoding="utf-8") if use_text else ""
        content.append({"type": "text", "text": task.format(numbered_text=number_lines(text)) if use_text else task})
        rec = {"page_id": pid, "book": book, "version": v, "condition": cond, "model": model,
               "sent_at": datetime.now(timezone.utc).isoformat(timespec="seconds")}
        for attempt in (1, 2):
            try:
                m = client.messages.create(model=model, max_tokens=16000, system=system,
                                           messages=[{"role": "user", "content": content}],
                                           output_config={"effort": "medium",
                                                          "format": {"type": "json_schema", "schema": schema}})
                raw = "".join(b.text for b in m.content if b.type == "text")
                usd = (m.usage.input_tokens * PRICES[model][0] + m.usage.output_tokens * PRICES[model][1]) / 1e6
                spent.append(usd)
                rec |= {"raw": raw, "stop_reason": m.stop_reason, "usd": round(usd, 5), "attempts": attempt,
                        "usage": {"input_tokens": m.usage.input_tokens, "output_tokens": m.usage.output_tokens}}
                rec["parsed"] = json.loads(raw)
                return rec
            except Exception as e:                     # one retry, as in the frozen runs
                rec["error"] = repr(e)[:500]
        return rec

    with ThreadPoolExecutor(4) as ex:
        recs = list(ex.map(one_gemini if gemini else one, jobs))
    with (out / "outputs.jsonl").open("w", encoding="utf-8") as f:
        for r in recs:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    cfg = {"run_id": run_id, "condition": cond, "model": model,
           "effort": None if gemini else "medium", "max_tokens": None if gemini else 16000,
           "versions": versions, "pages": which, "limit_pages": limit_pages, "page_ids": page_ids,
           "base_prompt_version": PROMPT_VERSION,
           "api": ("Gemini generateContent, sync, response_json_schema enforced, thinking = model default, "
                   "max_output_tokens 32768" if gemini else "Anthropic Messages, sync, effort medium"),
           "exploratory": True, "requests": len(jobs), "usd_total": round(sum(spent), 4),
           "errors": sum(1 for r in recs if r.get("error") and not r.get("parsed")),
           "stop_reasons": dict(Counter(r.get("stop_reason") for r in recs))}
    (out / "config.json").write_text(json.dumps(cfg, indent=2), encoding="utf-8")
    write_mentions(out, recs, cond)
    print(json.dumps(cfg, indent=2))


def write_mentions(out, recs, cond) -> None:
    """test_mentions.csv in the frozen runs' format. G2/V2: the quote is located by locate.py like a
    G1 quote, then the value is replaced by the model's reading. V1: values only, no positions."""
    rows = []
    for r in recs:
        ms = (r.get("parsed") or {}).get("mentions", [])
        if cond == "G1F":                       # frozen G1: values sliced from the source
            src = text_path(r["version"], r["page_id"]).read_text(encoding="utf-8")
            rows += [{"page_id": r["page_id"], "version": r["version"], "condition": cond, "i": i, **loc}
                     for i, loc in enumerate(locate_all(src, "G1", ms))]
            continue
        if cond in ("V1", "V3"):
            rows += [{"page_id": r["page_id"], "version": "image", "condition": cond, "i": i, "field": m["field"],
                      "value": m["value"], "status": "no_position", "start": None, "end": None,
                      "box": json.dumps(m.get("box")) if m.get("box") is not None else ""}
                     for i, m in enumerate(ms)]
            continue
        src = text_path(r["version"], r["page_id"]).read_text(encoding="utf-8")
        located = locate_all(src, "G1", [{"field": m["field"], "line": m["line"], "quote": m["quote"]} for m in ms])
        for i, (m, loc) in enumerate(zip(ms, located)):
            rows.append({"page_id": r["page_id"], "version": r["version"], "condition": cond, "i": i, **loc,
                         "quote_value": loc.get("value"), "value": m["reading"],
                         "repaired": norm_value(m["reading"]) != norm_value(m["quote"])})
    pd.DataFrame(rows).to_csv(out / "test_mentions.csv", index=False)


# ---------------------------------------------------------------- scoring
PRIMARY = ["taxon", "person", "locality", "institution", "date"]


def bag_scores(pred: pd.DataFrame, gold: pd.DataFrame, label: str) -> list[dict]:
    """Per book, ALL_PRIMARY: multiset of normalised values per page and field against the gold texts
    (a gold mention also accepts its scan_text). Ambiguous gold rows are optional."""
    out = []
    for book, gb in gold.groupby("book"):
        tp = fp = fn = 0
        for (pid, field), gg in gb[gb.field.isin(PRIMARY)].groupby(["page_id", "field"]):
            pv = Counter(norm_value(str(v)) for v in pred[(pred.page_id == pid) & (pred.field == field)].value)
            for g in gg.itertuples():
                acc = [norm_value(g.text)] + ([norm_value(g.scan_text)] if str(g.scan_text).strip() else [])
                hit = next((a for a in acc if pv[a] > 0), None)
                if hit:
                    pv[hit] -= 1
                    tp += g.adjudication != "ambiguous"
                elif g.adjudication != "ambiguous":
                    fn += 1
            fp += sum(c for c in pv.values() if c > 0)
        # predictions on pages/fields with no gold at all
        bp = pred[pred.page_id.isin(set(gb.page_id)) & pred.field.isin(PRIMARY)]
        have = set(map(tuple, gb[gb.field.isin(PRIMARY)][["page_id", "field"]].drop_duplicates().values))
        fp += sum(1 for r in bp.itertuples() if (r.page_id, r.field) not in have)
        p_, r_ = tp / (tp + fp) if tp + fp else 0, tp / (tp + fn) if tp + fn else 0
        out.append({"condition": label, "book": book, "tp": tp, "fp": fp, "fn": fn, "bag_P": round(p_, 3),
                    "bag_R": round(r_, 3), "bag_F1": round(2 * p_ * r_ / (p_ + r_), 3) if p_ + r_ else 0})
    return out


def score_all() -> None:
    gold = load_gold(ROOT / "gold" / "gold_mentions_gloria_test.csv")
    split = pd.read_csv(DATA / "sample_split.csv")
    if "book" not in gold.columns:
        gold = gold.merge(split[["PageID", "book"]].rename(columns={"PageID": "page_id"}), on="page_id", how="left")
    if "scan_text" not in gold.columns:
        gold["scan_text"] = ""
    gold["scan_text"] = gold.scan_text.fillna("")
    rows, pos = [], []
    frozen = pd.read_csv(RESULTS / "20261119-2052_claude-opus-5-5_test_batch" / "test_mentions.csv")
    ladder = pd.read_csv(RESULTS / "20261120-ocrladder_claude-opus-5-5_test_G1" / "test_mentions.csv")
    base = pd.concat([frozen, ladder])
    for v in ("expert", "modern_dots-mocr", "legacy", "modern_tesseract", "modern_deepseek-ocr2"):
        rows += bag_scores(base[(base.version == v) & (base.condition == "G1")], gold, f"G1 · {v}")
    for d in sorted(RESULTS.glob("*_explore_*")):
        cfg = json.loads((d / "config.json").read_text())
        if cfg.get("pages", "test") != "test" or cfg.get("limit_pages") or cfg.get("page_ids"):  # PCAS: score_pcas.py; pilots, diagnostics skipped
            continue
        m = pd.read_csv(d / "test_mentions.csv")
        cond = cfg["condition"] + ("" if cfg["model"] == MODEL else f" [{cfg['model'].removeprefix('claude-')}]")
        for v, mv in m.groupby("version"):
            rows += bag_scores(mv, gold, f"{cond} · {v}")
            if not cond.startswith(("V1", "V3")):
                pos.append((d.name, cond, v, mv))
    bag = pd.DataFrame(rows)
    out = RESULTS / "exploratory_conditions"
    out.mkdir(exist_ok=True)
    bag.to_csv(out / "bag_scores.csv", index=False)
    pos_rows = []
    for run_id, cond, v, mv in pos:
        s = score_run_detail(run_id, ROOT / "gold" / "gold_mentions_gloria_test.csv", "test")["summary"]
        s = s[(s.version == v) & (s.field == "ALL_PRIMARY")]
        for r in s.itertuples():
            pos_rows.append({"condition": f"{cond} · {v}", "book": r.book, "value_F1": r.value_F1,
                             "value_F1_lo": r.value_F1_lo, "value_F1_hi": r.value_F1_hi,
                             "repaired_share": round(mv.repaired.mean(), 3)})
    posd = pd.DataFrame(pos_rows)
    posd.to_csv(out / "position_scores.csv", index=False)
    lines = ["# Exploratory conditions: LLM repair, vision only, vision + OCR (test pages)", "",
             "Decided after unsealing (DEVIATIONS.md); Claude Opus 5.5 (effort medium) unless another model is named in brackets (Gemini: sync, schema enforced, thinking at the model default); frozen field definitions. "
             "`bag` = per page and field, multiset of normalised values against the gold texts (works without "
             "positions, so the image-only condition can be compared); ALL_PRIMARY.", "",
             bag.pivot_table(index="condition", columns="book", values="bag_F1").to_markdown(), "",
             "Scored with positions by score.py (value F1, reading as value) for the conditions that quote the text:", "",
             posd.to_markdown(index=False) if len(posd) else "(none yet)", ""]
    (out / "REPORT.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cond", choices=list(CONDS))
    ap.add_argument("--versions", default="legacy")
    ap.add_argument("--max-usd", type=float, default=5.0)
    ap.add_argument("--score", action="store_true")
    ap.add_argument("--model", default=MODEL, choices=list(PRICES))
    ap.add_argument("--pages", default="test", choices=["test", "pcas"])
    ap.add_argument("--limit-pages", type=int, default=0, help="pilot on the first N pages (half per book)")
    ap.add_argument("--page-ids", default="", help="diagnostic: resend only these page ids (comma-separated); not scored")
    a = ap.parse_args()
    if a.score:
        score_all()
    elif a.cond:
        run(a.cond, a.versions.split(","), a.max_usd, a.model, a.pages, a.limit_pages,
            [int(x) for x in a.page_ids.split(",") if x] or None)
    else:
        sys.exit("--cond or --score")


if __name__ == "__main__":
    main()
