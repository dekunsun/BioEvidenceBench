"""Run LLM extraction over the sample pages and save a reproducible run folder.

    results/<run_id>/
      config.json            model, effort, max_tokens, prompt version, prices, SDK version, pages ...
      prompts/               the exact system prompt, both task templates and both JSON schemas
      inputs.csv             one row per request: custom_id, page, split, version, condition,
                             SHA-256 of the page text sent, source file
      dev_outputs.jsonl      full API responses for DEV pages (open)
      dev_mentions.csv       DEV mentions located in the source text (see locate.py)
      sealed/test_outputs.jsonl.gz   full API responses for TEST pages (sealed, see below)
      SEALED.md              SHA-256 of the sealed file, count, time, and how to unseal
      cost.json              tokens and dollars actually spent

SEALING. Gloria labels the test pages before anyone sees model output on them
(CLAUDE.md rule 1). Test-page responses therefore never touch disk as plain
text: they are written straight into a gzip file, and this script never prints
their content. `python src/unseal.py <run_id>` opens them only once the gold
labels for every test page exist and pass `check_gold.py`. The SHA-256 in
SEALED.md (committed to git) proves the file was not changed after the run.

API KEY. Read from the environment variable EVAL_ANTHROPIC_API_KEY.

Usage
  # 1. pilot: 5 dev pages, all versions and conditions, synchronous; prints cost per page
  python src/run_extraction.py --pages dev5 --mode sync --max-usd 5
  # 2. full run as a Message Batch (50% price); the cost cap uses the pilot's measured cost
  python src/run_extraction.py --pages all --mode batch --estimate-from <pilot_run_id> --max-usd 15
  python src/run_extraction.py --collect <run_id>        # fetch batch results when it has ended
  # anything, without calling the API:
  python src/run_extraction.py --pages all --dry-run
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from common import DATA, ROOT, TEXT, sha256_text
from locate import locate_all
from prompts import CONDITIONS, PROMPT_VERSION, SYSTEM, number_lines

RESULTS = ROOT / "results"
# modern_dots-mocr_plain = the same OCR text with Markdown marks deleted (formatting ablation)
VERSIONS = ["expert", "legacy", "modern_dots-mocr", "modern_dots-mocr_plain"]
# $ per million tokens: input, output, cache write (5 min), cache read. From the
# Claude API pricing table (2026-11). Batch requests cost 50% of these.
PRICES = {
    "claude-opus-5-5": (4.00, 20.00, 5.00, 0.20),
    "claude-sonnet-5-5": (2.00, 10.00, 2.50, 0.10),
    "claude-haiku-5-5": (0.10, 0.50, 0.125, 0.01),
}


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def text_path(version: str, page_id: int) -> Path:
    committed = DATA / "sample" / version / f"{page_id}.txt"   # committed copy of the sample pages
    if version == "expert" or committed.exists():
        return committed
    return TEXT / version / f"{page_id}.txt"


def select_pages(which: str) -> pd.DataFrame:
    s = pd.read_csv(DATA / "sample_split.csv")
    if which == "dev5":
        return s[s.split == "dev"].sort_values(["book", "PageID"]).head(5)
    if which in ("dev", "test"):
        return s[s.split == which]
    if which == "all":
        return s
    ids = {int(x) for x in which.split(",")}
    return s[s.PageID.isin(ids)]


def build_requests(pages: pd.DataFrame, versions, conditions, model, effort, max_tokens):
    reqs = []
    for p in pages.itertuples():
        for v in versions:
            path = text_path(v, p.PageID)
            if not path.exists():
                sys.exit(f"Missing {path}. Run load_gt.py, fetch_legacy_ocr.py and fetch_modern_ocr.py first.")
            text = path.read_text(encoding="utf-8")
            for c in conditions:
                template, schema = CONDITIONS[c]
                params = {
                    "model": model,
                    "max_tokens": max_tokens,
                    # Thinking cannot be turned off on Opus 5.5; effort controls depth.
                    "output_config": {"effort": effort,
                                      "format": {"type": "json_schema", "schema": schema}},
                    # Identical system prompt on every call, so it can be cached.
                    "system": [{"type": "text", "text": SYSTEM, "cache_control": {"type": "ephemeral"}}],
                    "messages": [{"role": "user", "content": template.format(numbered_text=number_lines(text))}],
                }
                reqs.append({"custom_id": f"{p.PageID}__{v}__{c}", "page_id": int(p.PageID),
                             "split": p.split, "book": p.book, "version": v, "condition": c,
                             "input_sha256": sha256_text(text), "source": str(path.relative_to(ROOT)),
                             "params": params})
    return reqs


def cost_of(usage: dict, model: str, batch: bool) -> float:
    pi, po, pcw, pcr = PRICES[model]
    c = (usage.get("input_tokens", 0) * pi + usage.get("output_tokens", 0) * po
         + (usage.get("cache_creation_input_tokens") or 0) * pcw
         + (usage.get("cache_read_input_tokens") or 0) * pcr) / 1e6
    return c * (0.5 if batch else 1.0)


def write_run_files(run_dir: Path, cfg: dict, reqs: list[dict]) -> None:
    (run_dir / "prompts").mkdir(parents=True, exist_ok=True)
    (run_dir / "prompts" / "system.txt").write_text(SYSTEM, encoding="utf-8")
    for c, (template, schema) in CONDITIONS.items():
        (run_dir / "prompts" / f"task_{c}.txt").write_text(template, encoding="utf-8")
        (run_dir / "prompts" / f"schema_{c}.json").write_text(json.dumps(schema, indent=2), encoding="utf-8")
    (run_dir / "config.json").write_text(json.dumps(cfg, indent=2), encoding="utf-8")
    pd.DataFrame([{k: r[k] for k in ("custom_id", "page_id", "split", "book", "version",
                                     "condition", "input_sha256", "source")} for r in reqs]
                 ).to_csv(run_dir / "inputs.csv", index=False)


def record_from_message(req: dict, msg, model: str, batch: bool) -> dict:
    d = msg.to_dict()
    text = next((b["text"] for b in d.get("content", []) if b.get("type") == "text"), "")
    try:
        parsed = json.loads(text) if text else None
    except json.JSONDecodeError:
        parsed = None
    usage = d.get("usage", {})
    return {"custom_id": req["custom_id"], "page_id": req["page_id"], "split": req["split"],
            "version": req["version"], "condition": req["condition"], "model": d.get("model"),
            "stop_reason": d.get("stop_reason"), "usage": usage, "cost_usd": cost_of(usage, model, batch),
            "parsed": parsed, "raw": d, "error": None, "received_at": now()}


class Sink:
    """Writes dev records as plain JSONL and test records into the sealed gzip."""

    def __init__(self, run_dir: Path):
        self.run_dir = run_dir
        (run_dir / "sealed").mkdir(parents=True, exist_ok=True)
        self.dev = open(run_dir / "dev_outputs.jsonl", "a", encoding="utf-8")
        self.test = gzip.open(run_dir / "sealed" / "test_outputs.jsonl.gz", "at", encoding="utf-8")
        self.n = {"dev": 0, "test": 0}

    def write(self, rec: dict) -> None:
        f = self.dev if rec["split"] == "dev" else self.test
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        f.flush()
        self.n[rec["split"]] += 1

    def close(self) -> None:
        self.dev.close()
        self.test.close()


def finalize(run_dir: Path, records_meta: list[dict], model: str, batch: bool) -> None:
    """Cost summary, SEALED.md, and located mentions for DEV pages only."""
    spent = sum(r["cost_usd"] for r in records_meta)
    pages = len({r["page_id"] for r in records_meta})
    by = pd.DataFrame(records_meta)
    cost = {"model": model, "batch": batch, "requests": len(records_meta), "pages": pages,
            "usd_total": round(spent, 4), "usd_per_page_all_conditions": round(spent / max(pages, 1), 4),
            "usd_per_request": round(spent / max(len(records_meta), 1), 5),
            "tokens": {k: int(by["usage"].map(lambda u: (u or {}).get(k) or 0).sum())
                       for k in ("input_tokens", "output_tokens", "cache_creation_input_tokens",
                                 "cache_read_input_tokens")},
            "stop_reasons": by.stop_reason.fillna("error").value_counts().to_dict(),
            "errors": int(by.error.notna().sum())}
    (run_dir / "cost.json").write_text(json.dumps(cost, indent=2), encoding="utf-8")

    sealed = run_dir / "sealed" / "test_outputs.jsonl.gz"
    n_test = sum(r["split"] == "test" for r in records_meta)
    if n_test:
        digest = hashlib.sha256(sealed.read_bytes()).hexdigest()
        (run_dir / "SEALED.md").write_text(
            f"# Sealed test outputs\n\n"
            f"- File: `sealed/test_outputs.jsonl.gz`\n- SHA-256: `{digest}`\n"
            f"- Responses: {n_test} (test pages only)\n- Sealed at: {now()}\n\n"
            "Do not open this file before the gold labels for every test page are final.\n"
            "Unseal with `python src/unseal.py " + run_dir.name + " --labeller <name>`; it checks the\n"
            "gold file first and verifies this hash.\n", encoding="utf-8")
    elif sealed.exists():
        sealed.unlink()
        sealed.parent.rmdir()

    # Locate DEV mentions in the source text (test pages wait for unseal.py).
    rows = []
    with open(run_dir / "dev_outputs.jsonl", encoding="utf-8") as f:
        for line in f:
            rec = json.loads(line)
            if not rec.get("parsed"):
                continue
            src = (ROOT / pd.read_csv(run_dir / "inputs.csv").set_index("custom_id").loc[rec["custom_id"], "source"]
                   ).read_text(encoding="utf-8")
            for i, m in enumerate(locate_all(src, rec["condition"], rec["parsed"].get("mentions", []))):
                rows.append({"page_id": rec["page_id"], "version": rec["version"],
                             "condition": rec["condition"], "i": i, **m})
    if rows:
        pd.DataFrame(rows).to_csv(run_dir / "dev_mentions.csv", index=False)
    print(json.dumps(cost, indent=2))
    print(f"Dev responses: open in {run_dir/'dev_outputs.jsonl'}; test responses sealed: {n_test}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pages", default="dev5", help="dev5 | dev | test | all | comma-separated PageIDs")
    ap.add_argument("--versions", default=",".join(VERSIONS))
    ap.add_argument("--conditions", default="G0,G1")
    ap.add_argument("--model", default="claude-opus-5-5")
    ap.add_argument("--effort", default="medium")
    ap.add_argument("--max-tokens", type=int, default=16000)
    ap.add_argument("--mode", choices=["sync", "batch"], default="sync")
    ap.add_argument("--max-usd", type=float, default=5.0, help="hard cost cap for this run")
    ap.add_argument("--estimate-from", help="pilot run_id whose measured cost per request sets the batch estimate")
    ap.add_argument("--run-id")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--collect", metavar="RUN_ID", help="fetch results of a submitted batch")
    a = ap.parse_args()

    if a.collect:
        return collect(a.collect)

    pages = select_pages(a.pages)
    reqs = build_requests(pages, a.versions.split(","), a.conditions.split(","),
                          a.model, a.effort, a.max_tokens)
    run_id = a.run_id or f"{datetime.now(timezone.utc):%Y%m%d-%H%M}_{a.model}_{a.pages.replace(',', '-')[:20]}_{a.mode}"
    run_dir = RESULTS / run_id
    if run_dir.exists():
        sys.exit(f"{run_dir} exists; choose another --run-id")
    import anthropic
    cfg = {"run_id": run_id, "created_at": now(), "model": a.model, "effort": a.effort,
           "max_tokens": a.max_tokens, "mode": a.mode, "prompt_version": PROMPT_VERSION,
           "system_sha256": sha256_text(SYSTEM), "pages": a.pages, "page_ids": pages.PageID.tolist(),
           "versions": a.versions.split(","), "conditions": a.conditions.split(","),
           "prices_usd_per_mtok": PRICES.get(a.model), "anthropic_sdk": anthropic.__version__,
           "max_usd": a.max_usd, "n_requests": len(reqs), "dry_run": a.dry_run}
    print(f"{len(reqs)} requests ({len(pages)} pages x versions x conditions); run {run_id}")

    if a.dry_run:
        print(json.dumps({k: v for k, v in reqs[0].items() if k != "params"}, indent=2))
        print(reqs[0]["params"]["messages"][0]["content"][:600])
        return

    if a.mode == "batch":
        if not a.estimate_from:
            sys.exit("Batch mode needs --estimate-from <pilot run_id> to check the cost cap.")
        pilot = json.loads((RESULTS / a.estimate_from / "cost.json").read_text())
        per_req = pilot["usd_per_request"] * (0.5 if not pilot["batch"] else 1.0)
        est = per_req * len(reqs)
        print(f"Estimated batch cost: ${est:.2f} ({len(reqs)} x ${per_req:.4f}); cap ${a.max_usd:.2f}")
        if est > a.max_usd:
            sys.exit("Estimate exceeds the cap. Not submitted.")

    key = os.environ.get("EVAL_ANTHROPIC_API_KEY")
    if not key:
        sys.exit("Set EVAL_ANTHROPIC_API_KEY (environment settings), then start a new session.")
    client = anthropic.Anthropic(api_key=key, max_retries=4)
    run_dir.mkdir(parents=True)
    write_run_files(run_dir, cfg, reqs)

    if a.mode == "batch":
        from anthropic.types.message_create_params import MessageCreateParamsNonStreaming
        from anthropic.types.messages.batch_create_params import Request
        batch = client.messages.batches.create(requests=[
            Request(custom_id=r["custom_id"], params=MessageCreateParamsNonStreaming(**r["params"]))
            for r in reqs])
        (run_dir / "batch.json").write_text(json.dumps({"batch_id": batch.id, "submitted_at": now()}, indent=2))
        print(f"Submitted batch {batch.id}. Collect with: python src/run_extraction.py --collect {run_id}")
        return

    # Synchronous: stop starting new requests once the cap is reached.
    sink, meta, spent = Sink(run_dir), [], [0.0]

    def one(r):
        if spent[0] >= a.max_usd:
            return None
        try:
            msg = client.messages.create(**r["params"])
            rec = record_from_message(r, msg, a.model, batch=False)
        except anthropic.APIError as e:
            rec = {"custom_id": r["custom_id"], "page_id": r["page_id"], "split": r["split"],
                   "version": r["version"], "condition": r["condition"], "model": a.model,
                   "stop_reason": None, "usage": {}, "cost_usd": 0.0, "parsed": None, "raw": None,
                   "error": f"{type(e).__name__}: {str(e)[:300]}", "received_at": now()}
        spent[0] += rec["cost_usd"]
        return rec

    with ThreadPoolExecutor(a.workers) as pool:
        for rec in pool.map(one, reqs):
            if rec is None:
                continue
            sink.write(rec)
            meta.append({k: rec[k] for k in ("page_id", "split", "stop_reason", "usage", "cost_usd", "error")})
    sink.close()
    if spent[0] >= a.max_usd:
        print(f"STOPPED at the cost cap (${spent[0]:.2f} >= ${a.max_usd:.2f}); {len(meta)}/{len(reqs)} done.")
    finalize(run_dir, meta, a.model, batch=False)


def collect(run_id: str) -> None:
    import anthropic
    run_dir = RESULTS / run_id
    cfg = json.loads((run_dir / "config.json").read_text())
    batch_id = json.loads((run_dir / "batch.json").read_text())["batch_id"]
    client = anthropic.Anthropic(api_key=os.environ["EVAL_ANTHROPIC_API_KEY"])
    b = client.messages.batches.retrieve(batch_id)
    if b.processing_status != "ended":
        print(f"Batch {batch_id}: {b.processing_status}; counts {b.request_counts}. Try again later.")
        return
    reqs = pd.read_csv(run_dir / "inputs.csv").set_index("custom_id")
    sink, meta = Sink(run_dir), []
    for res in client.messages.batches.results(batch_id):
        row = reqs.loc[res.custom_id]
        req = {"custom_id": res.custom_id, "page_id": int(row.page_id), "split": row.split,
               "version": row.version, "condition": row.condition}
        if res.result.type == "succeeded":
            rec = record_from_message(req, res.result.message, cfg["model"], batch=True)
        else:
            rec = {**req, "model": cfg["model"], "stop_reason": None, "usage": {}, "cost_usd": 0.0,
                   "parsed": None, "raw": None, "error": res.result.type, "received_at": now()}
        sink.write(rec)
        meta.append({k: rec[k] for k in ("page_id", "split", "stop_reason", "usage", "cost_usd", "error")})
    sink.close()
    finalize(run_dir, meta, cfg["model"], batch=True)


if __name__ == "__main__":
    main()
