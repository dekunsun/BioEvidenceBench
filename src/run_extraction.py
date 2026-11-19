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

PROVIDERS. --provider anthropic (default; key in EVAL_ANTHROPIC_API_KEY) or
--provider gemini (Google Gen AI SDK, key in GEMINI_API_KEY; see gemini_backend.py).
Both send the same system prompt, task texts, numbered page text and JSON schemas,
and write records in the same format, so sealing, locate.py and the scorer are shared.

Usage
  # 1. pilot: 5 dev pages, all versions and conditions, synchronous; prints cost per page
  python src/run_extraction.py --pages dev5 --mode sync --max-usd 5
  # 2. full run as a Message Batch (50% price); the cost cap uses the pilot's measured cost
  python src/run_extraction.py --pages all --mode batch --estimate-from <pilot_run_id> --max-usd 15
  python src/run_extraction.py --collect <run_id>        # fetch batch results when it has ended
  # anything, without calling the API:
  python src/run_extraction.py --pages all --dry-run
  # Gemini: the same steps with --provider gemini (model defaults to gemini-4-carbon), e.g.
  python src/run_extraction.py --provider gemini --pages dev5 --mode sync --max-usd 1
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

import gemini_backend as gb
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


def anthropic_params(model, max_tokens, effort, schema, user_text) -> dict:
    return {
        "model": model,
        "max_tokens": max_tokens,
        # Thinking cannot be turned off on Opus 5.5; effort controls depth.
        "output_config": {"effort": effort,
                          "format": {"type": "json_schema", "schema": schema}},
        # Identical system prompt on every call, so it can be cached.
        "system": [{"type": "text", "text": SYSTEM, "cache_control": {"type": "ephemeral"}}],
        "messages": [{"role": "user", "content": user_text}],
    }


META_KEYS = ("page_id", "split", "model", "stop_reason", "usage", "cost_usd", "error", "schema_deviation",
             "attempts")


def needs_retry(rec: dict) -> bool:
    """A failed request (PREREGISTRATION section 9): an API error, a truncated answer, or an
    answer that does not parse. A valid answer with no mentions is NOT a failure."""
    return bool(rec.get("error")) or rec.get("stop_reason") in ("max_tokens", "MAX_TOKENS") \
        or not isinstance(rec.get("parsed"), dict)


def merge_retry(first: dict, second: dict) -> dict:
    """The second attempt is final. The first one is kept inside it (raw answer included, so a
    test-page record still goes only into the sealed file) and both are paid for."""
    out = dict(second)
    out["attempts"] = 2
    out["first_attempt"] = {k: first.get(k) for k in ("error", "stop_reason", "usage", "cost_usd",
                                                         "received_at", "schema_deviation", "raw")}
    out["cost_usd"] = (first.get("cost_usd") or 0.0) + (second.get("cost_usd") or 0.0)
    return out


def meta_of(rec: dict) -> dict:
    """The small part of a record that finalize() needs (never the model's answer)."""
    return {k: rec.get(k) for k in META_KEYS}


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


def build_requests(pages: pd.DataFrame, versions, conditions, model, effort, max_tokens,
                   provider: str = "anthropic"):
    reqs = []
    for p in pages.itertuples():
        for v in versions:
            path = text_path(v, p.PageID)
            if not path.exists():
                sys.exit(f"Missing {path}. Run load_gt.py, fetch_legacy_ocr.py and fetch_modern_ocr.py first.")
            text = path.read_text(encoding="utf-8")
            for c in conditions:
                template, schema = CONDITIONS[c]
                # The same user text for both providers; only the request wrapper differs.
                user_text = template.format(numbered_text=number_lines(text))
                if provider == "gemini":
                    params = gb.build_params(SYSTEM, user_text, schema, max_tokens)
                else:
                    params = anthropic_params(model, max_tokens, effort, schema, user_text)
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


def finalize(run_dir: Path, records_meta: list[dict], model: str, batch: bool,
             extra_cost: dict | None = None) -> None:
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
    if "attempts" in by:
        cost["retried_once"] = int((by.attempts == 2).sum())   # failed first, sent once more
    if "schema_deviation" in by and by.schema_deviation.notna().any():
        # answers whose JSON shape did not follow the schema as sent (see gemini_backend.check_shape)
        cost["schema_deviations"] = by.schema_deviation.dropna().value_counts().to_dict()
    if "model" in by:   # version string(s) the API reported in its responses
        cost["model_versions_returned"] = by.model.fillna("none").value_counts().to_dict()
    cost.update(extra_cost or {})
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
            if not isinstance(rec.get("parsed"), dict):
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
    ap.add_argument("--provider", choices=["anthropic", "gemini"], default="anthropic")
    ap.add_argument("--model", help="default: claude-opus-5-5 (anthropic) or gemini-4-carbon (gemini)")
    ap.add_argument("--effort", default="medium", help="Anthropic only")
    ap.add_argument("--max-tokens", type=int,
                    help=f"default: 16000 (anthropic) or {gb.MAX_OUTPUT_TOKENS} (gemini; includes thinking)")
    ap.add_argument("--mode", choices=["sync", "batch"], default="sync")
    ap.add_argument("--max-usd", type=float, default=5.0, help="hard cost cap for this run")
    ap.add_argument("--estimate-from", help="pilot run_id whose measured cost per request sets the batch estimate")
    ap.add_argument("--run-id")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--resume", metavar="RUN_ID",
                    help="sync, DEV-only runs: continue a run that crashed part-way. Requests already in "
                         "dev_outputs.jsonl are kept and not sent again; their cost counts toward --max-usd")
    ap.add_argument("--unrecorded-usd", type=float, default=0.0,
                    help="with --resume: allowance for requests of the crashed attempt that may have been "
                         "billed but were never written to disk; counts toward --max-usd")
    ap.add_argument("--collect", metavar="RUN_ID", help="fetch results of a submitted batch")
    ap.add_argument("--no-retry", action="store_true",
                    help="with --collect: do not send failed requests once more (the default is one retry)")
    ap.add_argument("--reparse", metavar="RUN_ID",
                    help="Gemini runs: rebuild the open DEV records from their stored raw responses "
                         "(no API call; sealed test outputs are not touched)")
    a = ap.parse_args()

    if a.collect:
        return collect(a.collect, retry=not a.no_retry)
    if a.reparse:
        return reparse(a.reparse)

    old_cfg = None
    if a.resume:
        # Same settings as the crashed attempt, read from its config.json (not from the command line).
        old_cfg = json.loads((RESULTS / a.resume / "config.json").read_text())
        if old_cfg["mode"] != "sync":
            sys.exit("--resume is for sync runs; use --collect for batches.")
        a.provider, a.model, a.max_tokens = old_cfg["provider"], old_cfg["model"], old_cfg["max_tokens"]
        a.pages, a.mode, a.run_id = old_cfg["pages"], "sync", a.resume
        a.versions, a.conditions = ",".join(old_cfg["versions"]), ",".join(old_cfg["conditions"])
        a.effort = old_cfg.get("effort", a.effort)

    gem = a.provider == "gemini"
    a.model = a.model or ("gemini-4-carbon" if gem else "claude-opus-5-5")
    a.max_tokens = a.max_tokens or (gb.MAX_OUTPUT_TOKENS if gem else 16000)
    if a.model not in (gb.PRICES if gem else PRICES):
        sys.exit(f"No price for {a.model}; add it to PRICES ({'gemini_backend.py' if gem else 'run_extraction.py'}).")

    pages = select_pages(a.pages)
    reqs = build_requests(pages, a.versions.split(","), a.conditions.split(","),
                          a.model, a.effort, a.max_tokens, a.provider)
    run_id = a.run_id or f"{datetime.now(timezone.utc):%Y%m%d-%H%M}_{a.model}_{a.pages.replace(',', '-')[:20]}_{a.mode}"
    run_dir = RESULTS / run_id
    if run_dir.exists() and not a.resume:
        sys.exit(f"{run_dir} exists; choose another --run-id")
    cfg = {"run_id": run_id, "created_at": now(), "provider": a.provider, "model": a.model,
           "max_tokens": a.max_tokens, "mode": a.mode, "prompt_version": PROMPT_VERSION,
           "system_sha256": sha256_text(SYSTEM), "pages": a.pages, "page_ids": pages.PageID.tolist(),
           "versions": a.versions.split(","), "conditions": a.conditions.split(","),
           "max_usd": a.max_usd, "n_requests": len(reqs), "dry_run": a.dry_run}
    if gem:
        cfg.update(gb.config_for_log(a.model, a.max_tokens, batch=a.mode == "batch"))
    else:
        import anthropic
        cfg.update({"effort": a.effort, "prices_usd_per_mtok": PRICES.get(a.model),
                    "anthropic_sdk": anthropic.__version__})
    print(f"{len(reqs)} requests ({len(pages)} pages x versions x conditions); run {run_id}")

    if a.dry_run:
        print(json.dumps({k: v for k, v in reqs[0].items() if k != "params"}, indent=2))
        msg = reqs[0]["params"]["contents"][0]["parts"][0]["text"] if gem else reqs[0]["params"]["messages"][0]["content"]
        print(msg[:600])
        return

    if a.mode == "batch":
        if not a.estimate_from:
            sys.exit("Batch mode needs --estimate-from <pilot run_id> to check the cost cap.")
        pilot = json.loads((RESULTS / a.estimate_from / "cost.json").read_text())
        if pilot.get("model") != a.model:
            sys.exit(f"Pilot {a.estimate_from} used {pilot.get('model')}, not {a.model}.")
        per_req = pilot["usd_per_request"] * (0.5 if not pilot["batch"] else 1.0)
        est = per_req * len(reqs)
        print(f"Estimated batch cost: ${est:.2f} ({len(reqs)} x ${per_req:.4f}); cap ${a.max_usd:.2f}")
        if est > a.max_usd:
            sys.exit("Estimate exceeds the cap. Not submitted.")
        cfg["estimate"] = {"from": a.estimate_from, "usd": round(est, 4)}

    if gem:
        key = os.environ.get("GEMINI_API_KEY")
        if not key:
            sys.exit("Set GEMINI_API_KEY (environment settings), then start a new session.")
        client = gb.make_client(key)
        # What the API itself says about this model id (version string, token limits).
        cfg["model_info_from_api"] = gb.model_info(client, a.model)
    else:
        import anthropic
        key = os.environ.get("EVAL_ANTHROPIC_API_KEY")
        if not key:
            sys.exit("Set EVAL_ANTHROPIC_API_KEY (environment settings), then start a new session.")
        client = anthropic.Anthropic(api_key=key, max_retries=4)
    prior = []   # records of an earlier, crashed attempt of this run (--resume)
    if a.resume:
        # Refuse unless prompt, model settings and every input text are exactly those of the first attempt.
        if any(r["split"] != "dev" for r in reqs):
            sys.exit("--resume handles DEV-only runs (sealed test outputs are never read back).")
        if old_cfg["system_sha256"] != cfg["system_sha256"] or old_cfg["prompt_version"] != PROMPT_VERSION:
            sys.exit("Prompt changed since the first attempt; not resumed.")
        if gem and old_cfg.get("generation_config") != cfg.get("generation_config"):
            sys.exit("Generation settings changed since the first attempt; not resumed.")
        old_in = pd.read_csv(run_dir / "inputs.csv").set_index("custom_id").input_sha256.to_dict()
        if old_in != {r["custom_id"]: r["input_sha256"] for r in reqs}:
            sys.exit("Requests or input hashes differ from the first attempt; not resumed.")
        prior = [json.loads(line) for line in open(run_dir / "dev_outputs.jsonl", encoding="utf-8")]
        done = {r["custom_id"] for r in prior}
        reqs = [r for r in reqs if r["custom_id"] not in done]
        old_cfg.setdefault("resumed", []).append(
            {"at": now(), "already_done": len(done), "to_send": len(reqs), "max_usd": a.max_usd,
             "unrecorded_usd_allowance": a.unrecorded_usd, "workers": a.workers,
             "model_info_from_api": cfg.get("model_info_from_api")})
        (run_dir / "config.json").write_text(json.dumps(old_cfg, indent=2), encoding="utf-8")
        print(f"Resuming {run_id}: {len(done)} done, {len(reqs)} to send.")
    else:
        run_dir.mkdir(parents=True)
        write_run_files(run_dir, cfg, reqs)

    if a.mode == "batch":
        if gem:
            batch_id = gb.submit_batch(client, a.model, reqs, display_name=run_id).name
        else:
            from anthropic.types.message_create_params import MessageCreateParamsNonStreaming
            from anthropic.types.messages.batch_create_params import Request
            batch_id = client.messages.batches.create(requests=[
                Request(custom_id=r["custom_id"], params=MessageCreateParamsNonStreaming(**r["params"]))
                for r in reqs]).id
        (run_dir / "batch.json").write_text(json.dumps({"batch_id": batch_id, "submitted_at": now()}, indent=2))
        print(f"Submitted batch {batch_id}. Collect with: python src/run_extraction.py --collect {run_id}")
        return

    # Synchronous: stop starting new requests once the cap is reached.
    sink, meta = Sink(run_dir), [meta_of(r) for r in prior]
    spent = [sum(r["cost_usd"] for r in prior) + a.unrecorded_usd]
    n_prior, n_new, dropped = len(prior), len(reqs), [0]
    api_errors = gb.api_errors() if gem else (anthropic.APIError,)

    def call(r):
        if gem:
            return gb.record_from_response(r, gb.generate(client, a.model, r["params"]), a.model, batch=False)
        return record_from_message(r, client.messages.create(**r["params"]), a.model, batch=False)

    def attempt(r):
        rec = None
        for _ in range(3):
            try:
                rec = call(r)
                break
            except api_errors as e:   # the API answered with an error: recorded (one() retries once)
                rec = gb.error_record(r, a.model, f"{type(e).__name__}: {e}")   # same shape for both providers
                break
            except Exception as e:    # connection dropped (e.g. httpx ReadError): the answer is lost
                # The provider may still bill a request whose answer never arrived, so count
                # this run's mean cost per answered request toward the cap before trying again.
                dropped[0] += 1
                done = [m["cost_usd"] for m in meta if m["cost_usd"]]
                spent[0] += sum(done) / len(done) if done else 0.0
                rec = gb.error_record(r, a.model, f"connection dropped 3 times; last: {type(e).__name__}: {e}")
                if spent[0] >= a.max_usd:
                    break
        spent[0] += rec["cost_usd"]
        return rec

    def one(r):
        if spent[0] >= a.max_usd:
            return None
        rec = attempt(r)
        # A failed request is sent once more with identical settings; the second answer is final.
        if needs_retry(rec) and spent[0] < a.max_usd:
            rec = merge_retry(rec, attempt(r))
        return rec

    with ThreadPoolExecutor(a.workers) as pool:
        for rec in pool.map(one, reqs):
            if rec is None:
                continue
            sink.write(rec)
            meta.append(meta_of(rec))
    sink.close()
    if spent[0] >= a.max_usd:
        print(f"STOPPED at the cost cap (${spent[0]:.2f} >= ${a.max_usd:.2f}); "
              f"{len(meta) - n_prior}/{n_new} done.")
    extra = dict(gb.cost_notes(a.model)) if gem else {}
    if a.resume or dropped[0]:
        # usd_total covers answers on disk only; this says what else may have been billed.
        extra["not_in_usd_total"] = {
            "unrecorded_usd_allowance_first_attempt": a.unrecorded_usd,
            "connections_dropped_and_retried": dropped[0],
            "usd_counted_toward_cap": round(spent[0], 4)}
    finalize(run_dir, meta, a.model, batch=False, extra_cost=extra or None)


def retry_failed_sync(cfg: dict, recs: list[dict]) -> list[dict]:
    """After a batch: send every failed request once more, synchronously, with the request
    rebuilt from the same prompt and the same input text (hash checked); the second answer is
    final. Billed at the sync price."""
    failed = [i for i, r in enumerate(recs) if needs_retry(r)]
    if not failed:
        return recs
    gem = cfg.get("provider") == "gemini"
    if cfg["prompt_version"] != PROMPT_VERSION or cfg["system_sha256"] != sha256_text(SYSTEM):
        print(f"{len(failed)} failed requests NOT retried: the prompt changed since this run was made.")
        return recs
    pages = pd.read_csv(DATA / "sample_split.csv").query("PageID in @cfg['page_ids']")
    rebuilt = {r["custom_id"]: r for r in build_requests(
        pages, cfg["versions"], cfg["conditions"], cfg["model"], cfg.get("effort", "medium"),
        cfg["max_tokens"], cfg.get("provider", "anthropic"))}
    if gem:
        client = gb.make_client(os.environ["GEMINI_API_KEY"])
    else:
        import anthropic
        client = anthropic.Anthropic(api_key=os.environ["EVAL_ANTHROPIC_API_KEY"], max_retries=4)
    inputs = pd.read_csv(RESULTS / cfg["run_id"] / "inputs.csv").set_index("custom_id").input_sha256
    for i in failed:
        req = rebuilt[recs[i]["custom_id"]]
        if req["input_sha256"] != inputs[req["custom_id"]]:
            print(f"{req['custom_id']}: input text changed since the batch; not retried.")
            continue
        try:
            second = (gb.record_from_response(req, gb.generate(client, cfg["model"], req["params"]),
                                              cfg["model"], batch=False) if gem else
                      record_from_message(req, client.messages.create(**req["params"]), cfg["model"],
                                          batch=False))
        except Exception as e:
            second = gb.error_record(req, cfg["model"], f"retry failed: {type(e).__name__}: {e}")
        recs[i] = merge_retry(recs[i], second)
    print(f"Retried {len(failed)} failed requests once; still failed: "
          f"{sum(needs_retry(recs[i]) for i in failed)}.")
    return recs


def collect(run_id: str, retry: bool = True) -> None:
    run_dir = RESULTS / run_id
    cfg = json.loads((run_dir / "config.json").read_text())
    batch_id = json.loads((run_dir / "batch.json").read_text())["batch_id"]
    reqs = pd.read_csv(run_dir / "inputs.csv").set_index("custom_id")
    gem = cfg.get("provider") == "gemini"

    def req_of(cid):
        row = reqs.loc[cid]
        return {"custom_id": cid, "page_id": int(row.page_id), "split": row.split,
                "version": row.version, "condition": row.condition}

    recs = []
    if gem:
        client = gb.make_client(os.environ["GEMINI_API_KEY"])
        job = client.batches.get(name=batch_id)
        state = gb.batch_state(job)
        if state not in gb.TERMINAL:
            print(f"Batch {batch_id}: {state}. Try again later.")
            return
        if state != "JOB_STATE_SUCCEEDED":
            print(f"Batch {batch_id} ended as {state}: {job.error}. Nothing collected.")
            return
        seen = set()
        for cid, resp, err in gb.iter_batch_results(job, list(reqs.index)):
            seen.add(cid)
            recs.append(gb.error_record(req_of(cid), cfg["model"], err) if err or resp is None
                        else gb.record_from_response(req_of(cid), resp, cfg["model"], batch=True))
        for cid in [c for c in reqs.index if c not in seen]:   # a request with no response at all
            recs.append(gb.error_record(req_of(cid), cfg["model"], "no response in batch output"))
    else:
        import anthropic
        client = anthropic.Anthropic(api_key=os.environ["EVAL_ANTHROPIC_API_KEY"])
        b = client.messages.batches.retrieve(batch_id)
        if b.processing_status != "ended":
            print(f"Batch {batch_id}: {b.processing_status}; counts {b.request_counts}. Try again later.")
            return
        for res in client.messages.batches.results(batch_id):
            req = req_of(res.custom_id)
            if res.result.type == "succeeded":
                recs.append(record_from_message(req, res.result.message, cfg["model"], batch=True))
            else:
                recs.append(gb.error_record(req, cfg["model"], res.result.type))
    if retry:
        recs = retry_failed_sync(cfg, recs)
    # Records go straight to the sink (test pages into the sealed gzip); nothing is printed.
    sink, meta = Sink(run_dir), []
    for rec in recs:
        sink.write(rec)
        meta.append(meta_of(rec))
    sink.close()
    finalize(run_dir, meta, cfg["model"], batch=True, extra_cost=gb.cost_notes(cfg["model"]) if gem else None)


def reparse(run_id: str) -> None:
    """Re-derive parsed / usage / cost of the DEV records of a Gemini run from the raw
    responses already on disk, e.g. after gemini_backend.check_shape changed. No API call.
    Raw responses and received_at are kept. Refuses runs that have sealed test outputs:
    those are re-derived only through unseal.py, after the gold set is final."""
    run_dir = RESULTS / run_id
    cfg = json.loads((run_dir / "config.json").read_text())
    if cfg.get("provider") != "gemini":
        sys.exit("--reparse is for Gemini runs only.")
    if (run_dir / "sealed").exists():
        sys.exit("This run has sealed test outputs; not reparsed.")
    path = run_dir / "dev_outputs.jsonl"
    old = [json.loads(line) for line in open(path, encoding="utf-8")]
    batch = cfg["mode"] == "batch"
    new = []
    for o in old:
        if o.get("raw") is None:            # an API error has nothing to reparse
            new.append({**o, "schema_deviation": None})
            continue
        rec = gb.record_from_response(o, o["raw"], cfg["model"], batch=batch)
        rec["received_at"] = o["received_at"]
        new.append(rec)
    with open(path, "w", encoding="utf-8") as f:
        for rec in new:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    finalize(run_dir, [meta_of(r) for r in new], cfg["model"], batch=batch,
             extra_cost={**gb.cost_notes(cfg["model"]), "reparsed_at": now()})


if __name__ == "__main__":
    main()
