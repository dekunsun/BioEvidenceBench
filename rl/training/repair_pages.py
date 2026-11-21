"""Repair the legacy OCR lines of the 22 sample pages with the released checkpoint. Runs on the GPU pod.

    python rl/training/repair_pages.py --out <dir>

Downloads `sft_s2.tar` from the public release `rl-sft-ocr-repair-v1`, checks its SHA-256, and answers every
line marked `repair` in `rl/training/data/legacy_sample_lines.jsonl` (built by `src/sft_repair_pipeline.py build`)
with prompt `repair_v3`, thinking off, greedy decoding, at most 128 new tokens. The answer goes through the fixed
clean-up; if it is empty or outside 0.5-1.5x the OCR line's length, the OCR line is kept (`fallback`). Lines not
marked `repair` are kept as they are. Writes repaired_lines.jsonl and repair_summary.json to --out.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import tarfile
import time
from pathlib import Path

import requests

import common_7b as C

URL = "https://github.com/dekunsun/BioEvidenceBench/releases/download/rl-sft-ocr-repair-v1/sft_s2.tar"
SHA = "bfeb5657e7e078d25b1c47c64a8afd2c63c80d5e8bb0594f285d0fafdea16e8c"
LINES = C.ROOT / "rl" / "training" / "data" / "legacy_sample_lines.jsonl"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    out = Path(ap.parse_args().out)
    out.mkdir(parents=True, exist_ok=True)
    tar, sha = Path("/workspace/sft_s2.tar"), hashlib.sha256()
    with requests.get(URL, stream=True, timeout=3600) as r:
        r.raise_for_status()
        with tar.open("wb") as f:
            for chunk in r.iter_content(1 << 22):
                f.write(chunk)
                sha.update(chunk)
    assert sha.hexdigest() == SHA, "downloaded file is not the released checkpoint"
    with tarfile.open(tar) as tf:
        tf.extractall("/workspace", filter="data")

    from transformers import AutoTokenizer
    from vllm import LLM, SamplingParams
    items = [json.loads(line) for line in LINES.open(encoding="utf-8")]
    todo = [it for it in items if it["repair"]]
    tok = AutoTokenizer.from_pretrained(C.MODEL_ID)
    llm = LLM(model="/workspace/sft_s2", dtype="bfloat16", seed=20261121, gpu_memory_utilization=0.85,
              max_model_len=2048, enforce_eager=True)
    t0 = time.time()
    gens = llm.generate([C.render_prompt(tok, it) for it in todo],
                        SamplingParams(n=1, temperature=0.0, max_tokens=128))
    secs = time.time() - t0
    answers = {it["item_id"]: g.outputs[0] for it, g in zip(todo, gens)}
    n_fb = 0
    with (out / "repaired_lines.jsonl").open("w", encoding="utf-8") as f:
        for it in items:
            row = dict(it, raw=None, cleaned=None, fallback=False, final=it["input"], truncated=False)
            if it["repair"]:
                o = answers[it["item_id"]]
                cleaned = C.T.format_cleanup(o.text).strip()
                ok = bool(cleaned) and 0.5 <= len(cleaned) / max(1, len(it["input"])) <= 1.5
                row.update(raw=o.text, cleaned=cleaned, truncated=o.finish_reason == "length",
                           fallback=not ok, final=cleaned if ok else it["input"])
                n_fb += not ok
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    summary = {"checkpoint_sha256": SHA, "lines": len(items), "repaired_lines": len(todo), "fallback": n_fb,
               "generation_seconds": round(secs, 1), "decoding": "greedy, max 128 tokens, prompt " + C.PROMPT_VERSION}
    (out / "repair_summary.json").write_text(json.dumps(summary, indent=1))
    print(summary)


if __name__ == "__main__":
    main()
