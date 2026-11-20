"""Whole-book run: the frozen G1 extraction on every text page of Butler and Reeve (exploratory,
DEVIATIONS.md). A product question, not a scored result: what does it cost, how fast is it, how
often do the automatic checks fire, and where should a person look?

    python src/run_book.py --model claude-opus-5-5 --submit --max-usd 15     # Message Batches API
    python src/run_book.py --collect <run id>                                # when the batch has ended

Input: FineBooks' dots.mocr output (`markdown` field, as published) for the 989 pages of the two
books; pages with fewer than 20 characters (blank pages, plates) are skipped. Same system prompt,
G1 task and schema, effort and max_tokens as the frozen runs (run_extraction.py), batch mode.
The 22 sample pages are included (their gold is final and frozen, so their outputs need no seal);
dev and test pages are marked in `split` so they can be left out or used as a calibration check.
Values are sliced from the source by locate.locate_all, as in every G1 run (the model never
rewrites text). Writes results/<stamp>_book_<model>/: config.json, prompts/, inputs.csv,
batch.json, outputs.jsonl, mentions.csv, cost.json.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone

import pandas as pd

import run_extraction as rx
from common import DATA, ROOT, TEXT, sha256_text
from locate import locate_all
from prompts import CONDITIONS, PROMPT_VERSION, SYSTEM, number_lines

rx.PRICES.setdefault("claude-fable-5-2", (8.00, 40.00, 10.00, 0.20))
RESULTS = ROOT / "results"
VERSION = "modern_dots-mocr"
MIN_CHARS = 20


def book_pages() -> pd.DataFrame:
    gt = pd.read_parquet(DATA / "cache" / "gt_english.parquet",
                         columns=["PageID", "BarCode", "SequenceOrder", "PageTypeName"])
    d = pd.read_parquet(DATA / "cache" / "bucket" / "dots-mocr_normalized.parquet", columns=["PageID", "markdown"])
    d["PageID"] = d.PageID.astype(int)
    p = gt.merge(d, on="PageID", how="left")
    p["markdown"] = p.markdown.fillna("")
    p["book"] = p.BarCode.map(lambda b: "Butler" if "butl" in b else "Reeve")
    split = pd.read_csv(DATA / "sample_split.csv").set_index("PageID").split
    p["split"] = p.PageID.map(split).fillna("book")
    return p[p.markdown.str.strip().str.len() >= MIN_CHARS].sort_values(["book", "SequenceOrder"])


def submit(a) -> None:
    import anthropic
    from anthropic.types.message_create_params import MessageCreateParamsNonStreaming
    from anthropic.types.messages.batch_create_params import Request

    pages = book_pages()
    template, schema = CONDITIONS["G1"]
    (TEXT / VERSION).mkdir(parents=True, exist_ok=True)
    reqs = []
    for p in pages.itertuples():
        path = rx.text_path(VERSION, p.PageID)
        if not path.exists():                       # same text as fetch_modern_ocr.py writes
            path.write_text(p.markdown, encoding="utf-8")
        text = path.read_text(encoding="utf-8")
        if text != p.markdown:
            sys.exit(f"{path} differs from the bucket's markdown for page {p.PageID}")
        reqs.append({"custom_id": f"{p.PageID}__{VERSION}__G1", "page_id": int(p.PageID), "split": p.split,
                     "book": p.book, "version": VERSION, "condition": "G1", "input_sha256": sha256_text(text),
                     "source": str(path.relative_to(ROOT)),
                     "params": rx.anthropic_params(a.model, 16000, "medium", schema,
                                                   template.format(numbered_text=number_lines(text)))})
    # estimate from the sample's per-character cost of the same model, if a run exists; else Opus batch
    est_per_req = {"claude-opus-5-5": 0.0117, "claude-haiku-5-5": 0.00075, "claude-sonnet-5-5": 0.0051,
                   "claude-fable-5-2": 0.0216}[a.model]
    sample_chars = 2500
    est = sum(max(len(r["params"]["messages"][0]["content"]), 1) for r in reqs) / sample_chars * est_per_req
    print(f"{len(reqs)} pages ({pages.book.value_counts().to_dict()}); estimated ${est:.2f} in batch mode")
    if est > a.max_usd:
        sys.exit(f"Estimate ${est:.2f} is over --max-usd {a.max_usd}; nothing sent.")
    run_id = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M") + "_book_" + a.model.removeprefix("claude-")
    run_dir = RESULTS / run_id
    cfg = {"run_id": run_id, "created_at": rx.now(), "model": a.model, "max_tokens": 16000, "effort": "medium",
           "mode": "batch", "prompt_version": PROMPT_VERSION, "condition": "G1", "version": VERSION,
           "system_sha256": sha256_text(SYSTEM), "pages": len(reqs), "min_chars": MIN_CHARS,
           "max_usd": a.max_usd, "estimate_usd": round(est, 2), "exploratory": True,
           "prices_usd_per_mtok": rx.PRICES[a.model]}
    rx.write_run_files(run_dir, cfg, reqs)
    client = anthropic.Anthropic(api_key=os.environ["EVAL_ANTHROPIC_API_KEY"])
    b = client.messages.batches.create(requests=[
        Request(custom_id=r["custom_id"], params=MessageCreateParamsNonStreaming(**r["params"])) for r in reqs])
    (run_dir / "batch.json").write_text(json.dumps({"batch_id": b.id, "submitted_at": rx.now()}, indent=2))
    print(f"Submitted {b.id} as {run_id}. Collect with: python src/run_book.py --collect {run_id}")


def collect(run_id: str) -> None:
    import anthropic

    run_dir = RESULTS / run_id
    cfg = json.loads((run_dir / "config.json").read_text())
    batch = json.loads((run_dir / "batch.json").read_text())
    client = anthropic.Anthropic(api_key=os.environ["EVAL_ANTHROPIC_API_KEY"])
    b = client.messages.batches.retrieve(batch["batch_id"])
    if b.processing_status != "ended":
        print(f"{b.id}: {b.processing_status}; {b.request_counts}")
        return
    inputs = pd.read_csv(run_dir / "inputs.csv").set_index("custom_id")
    recs = []
    for res in client.messages.batches.results(b.id):
        req = {"custom_id": res.custom_id, **inputs.loc[res.custom_id].to_dict()}
        if res.result.type == "succeeded":
            recs.append(rx.record_from_message(req, res.result.message, cfg["model"], batch=True))
        else:
            recs.append({"custom_id": res.custom_id, "page_id": int(req["page_id"]), "split": req["split"],
                         "error": res.result.type, "cost_usd": 0.0, "parsed": None, "stop_reason": None,
                         "usage": {}})
    with open(run_dir / "outputs.jsonl", "w", encoding="utf-8") as f:
        for r in recs:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    rows = []
    for r in recs:
        if not isinstance(r.get("parsed"), dict):
            continue
        src = (ROOT / inputs.loc[r["custom_id"], "source"]).read_text(encoding="utf-8")
        for i, m in enumerate(locate_all(src, "G1", r["parsed"].get("mentions", []))):
            rows.append({"page_id": r["page_id"], "book": inputs.loc[r["custom_id"], "book"],
                         "split": r["split"], "i": i, **m})
    pd.DataFrame(rows).to_csv(run_dir / "mentions.csv", index=False)
    usd = sum(r["cost_usd"] for r in recs)
    ended = b.ended_at or datetime.now(timezone.utc)
    cost = {"model": cfg["model"], "batch": True, "requests": len(recs), "usd_total": round(usd, 4),
            "usd_per_page": round(usd / max(len(recs), 1), 5),
            "usd_per_1000_pages": round(1000 * usd / max(len(recs), 1), 2),
            "stop_reasons": pd.Series([r.get("stop_reason") or "error" for r in recs]).value_counts().to_dict(),
            "unparsed": sum(not isinstance(r.get("parsed"), dict) for r in recs),
            "batch_minutes": round((ended - b.created_at).total_seconds() / 60, 1),
            "mentions": len(rows)}
    (run_dir / "cost.json").write_text(json.dumps(cost, indent=2), encoding="utf-8")
    print(json.dumps(cost, indent=2))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="claude-opus-5-5", choices=list(rx.PRICES))
    ap.add_argument("--submit", action="store_true")
    ap.add_argument("--collect")
    ap.add_argument("--max-usd", type=float, default=15.0)
    a = ap.parse_args()
    if a.collect:
        collect(a.collect)
    elif a.submit:
        submit(a)
    else:
        p = book_pages()
        print(len(p), p.book.value_counts().to_dict(), p.split.value_counts().to_dict())


if __name__ == "__main__":
    main()
