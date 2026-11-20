"""Does the Gemini Batch API enforce response_json_schema? A small, reproducible check.

    python src/gemini_batch_schema_check.py            # submit, wait, compare, write the report

Background (gemini_backend.py, 2026-11-19): in run ..._gemini-4-carbon_dev_p4_r1 the Batch API
answered 44 of 48 requests with a bare JSON array instead of {"mentions": [...]}, while the same
requests sent synchronously always followed the schema. This script sends IDENTICAL requests
(frozen G1 prompt p4-guide-v0.6, expert text of 3 dev pages) once synchronously and once as an
inline batch, and checks every answer against the schema in code (gemini_backend.check_shape).
It also records the prompt token count of each answer: if the batch count is lower by about the
size of the schema, the schema was probably not passed to the model.

Dev pages only. Writes results/gemini_batch_schema_check/<stamp>/ (requests, raw answers, REPORT.md).
Cost: about $0.15 (prices in gemini_backend.PRICES).
"""
from __future__ import annotations

import json
import os
import time
from datetime import datetime, timezone

import pandas as pd

import gemini_backend as gb
from common import DATA, ROOT
from prompts import CONDITIONS, SYSTEM, number_lines
from run_extraction import text_path

MODEL = "gemini-4-carbon"
PAGES = 3
OUT = ROOT / "results" / "gemini_batch_schema_check"


def main() -> None:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M")
    out = OUT / stamp
    out.mkdir(parents=True)
    task, schema = CONDITIONS["G1"]
    pages = pd.read_csv(DATA / "sample_split.csv").query("split == 'dev'").head(PAGES)
    reqs = []
    for p in pages.itertuples():
        text = text_path("expert", int(p.PageID)).read_text(encoding="utf-8")
        reqs.append({"custom_id": f"{p.PageID}__expert__G1", "page_id": int(p.PageID), "split": "dev",
                     "version": "expert", "condition": "G1",
                     "params": gb.build_params(SYSTEM, task.format(numbered_text=number_lines(text)), schema)})
    (out / "requests.json").write_text(json.dumps(reqs, indent=1, ensure_ascii=False), encoding="utf-8")
    client = gb.make_client(os.environ["GEMINI_API_KEY"])
    info = gb.model_info(client, MODEL)

    rows = []
    for r in reqs:                                                     # synchronous
        rec = gb.record_from_response(r, gb.generate(client, MODEL, r["params"]), MODEL, batch=False)
        rows.append(("sync", rec))
    job = gb.submit_batch(client, MODEL, reqs, f"schema-check-{stamp}")
    submitted = gb.now()
    while gb.batch_state(job) not in gb.TERMINAL:                      # batch
        time.sleep(30)
        job = client.batches.get(name=job.name)
    by_id = {r["custom_id"]: r for r in reqs}
    for cid, resp, err in gb.iter_batch_results(job, [r["custom_id"] for r in reqs]):
        rec = gb.error_record(by_id[cid], MODEL, err) if err or resp is None else \
            gb.record_from_response(by_id[cid], resp, MODEL, batch=True)
        rows.append(("batch", rec))

    with (out / "answers.jsonl").open("w", encoding="utf-8") as f:
        for mode, rec in rows:
            f.write(json.dumps({"mode": mode} | rec, ensure_ascii=False, default=str) + "\n")
    table = pd.DataFrame([{
        "mode": mode, "page_id": rec["page_id"], "finish": rec["stop_reason"],
        "follows_schema": rec["parsed"] is not None and rec["schema_deviation"] is None,
        "deviation": rec["schema_deviation"] or ("" if rec["parsed"] is not None else "unparsed"),
        "top_level_type": type(json.loads(gb._answer_text(rec["raw"]))).__name__
        if isinstance(rec["raw"], dict) and gb._answer_text(rec["raw"]) else "",
        "prompt_tokens": rec["usage"].get("prompt_token_count"),
        "thought_tokens": rec["usage"].get("thoughts_token_count"),
        "usd": round(rec["cost_usd"], 4)} for mode, rec in rows])
    table.to_csv(out / "summary.csv", index=False)
    lines = ["# Gemini Batch API: is response_json_schema enforced?", "",
             f"Run {stamp}. Model `{MODEL}` (API reports version `{info.get('version')}`), SDK google-genai "
             f"{gb.sdk_version()}, endpoint {gb.API_BASE} {gb.API_VERSION}. Batch submitted {submitted}, "
             f"final state {gb.batch_state(job)}.",
             "Identical requests (frozen G1 prompt, expert text, dev pages; `requests.json`) sent synchronously "
             "and as one inline batch. Every answer is checked against the schema in code.", "",
             table.to_markdown(index=False), "",
             f"Total cost (computed from token counts): ${table.usd.sum():.3f}."]
    (out / "REPORT.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
