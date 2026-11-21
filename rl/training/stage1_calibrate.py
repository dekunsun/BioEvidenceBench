"""Module 7b, stage 1: small-model calibration (METRICS.md section 6). Runs on the GPU pod.

    python rl/training/stage1_calibrate.py --out <dir>             # vLLM, Qwen/Qwen3-0.6B
    python rl/training/stage1_calibrate.py --out <dir> --dry-run   # CPU: fake answers, checks the pipeline

The 182 dev items of the step 5 API trial (same lines, current data rules, fixed context;
`rl/training/data/stage1_dev200.jsonl`), K = 8 answers each from Qwen3-0.6B with thinking off, at
two temperatures: 1.0 (the planned rollout setting) and the model card's non-thinking setting
(0.7, top-p 0.8, top-k 20). Reported: the rendered prompt (template check), format failures and their
kinds, `<think>` share, truncation, raw and post-processed scores, the share of items whose 8
rewards are not all equal (`has_signal` = 1 - frac_reward_zero_std), throughput and tokens.
Gate: at least 20% of items with unequal rewards at the rollout temperature (provisional).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import time
from pathlib import Path

import common_7b as C

SETTINGS = {"rollout_T1.0": dict(temperature=1.0, top_p=1.0, top_k=-1),
            "card_nonthinking": dict(temperature=0.7, top_p=0.8, top_k=20)}
K, MAX_TOKENS, SEED, GATE = 8, 128, 20261121, 0.20


def generate_vllm(prompts, setting):
    from vllm import LLM, SamplingParams
    global _LLM
    if "_LLM" not in globals():
        _LLM = LLM(model=C.MODEL_ID, dtype="bfloat16", seed=SEED, gpu_memory_utilization=0.85, max_model_len=2048)
    sp = SamplingParams(n=K, max_tokens=MAX_TOKENS, seed=SEED, min_p=0.0, **setting)
    outs = _LLM.generate(prompts, sp)
    return [[(c.text, c.finish_reason == "length", len(c.token_ids)) for c in o.outputs] for o in outs]


def generate_fake(items, setting):
    """CPU check of everything after generation: copy, repair, wrap, think or ramble at random."""
    rng = random.Random(SEED)
    kinds = [lambda it: it["input"], lambda it: it["target"], lambda it: "Corrected line: " + it["target"],
             lambda it: "<think>\n\n</think>\n" + it["target"], lambda it: it["target"] + "\nNote: fixed."]
    return [[(rng.choice(kinds)(it), False, 30) for _ in range(K)] for it in items]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--items", default=str(C.ROOT / "rl" / "training" / "data" / "stage1_dev200.jsonl"))
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    items = C.load_items(Path(args.items))
    assert all(it["split"] == "dev" for it in items), "stage 1 reads dev items only"

    if args.dry_run:
        prompts, template = [it["input"] for it in items], "(dry run: no tokenizer)"
    else:
        from transformers import AutoTokenizer
        tok = AutoTokenizer.from_pretrained(C.MODEL_ID)
        prompts = [C.render_prompt(tok, it) for it in items]
        template = prompts[0]
    config = {"model": C.MODEL_ID, "k": K, "max_tokens": MAX_TOKENS, "seed": SEED, "settings": SETTINGS,
              "n_items": len(items), "items_sha256": hashlib.sha256(Path(args.items).read_bytes()).hexdigest(),
              "prompt_file_sha256": hashlib.sha256(C.PROMPT_FILE.read_bytes()).hexdigest(),
              "rendered_prompt_0": template,
              "rendered_prompt_0_sha256": hashlib.sha256(template.encode()).hexdigest(),
              "dry_run": args.dry_run}
    (out / "config.json").write_text(json.dumps(config, indent=2, ensure_ascii=False), encoding="utf-8")

    summary, rows = {}, []
    for name, setting in SETTINGS.items():
        t0 = time.time()
        gens = generate_fake(items, setting) if args.dry_run else generate_vllm(prompts, setting)
        secs = time.time() - t0
        n_signal = 0
        for it, answers in zip(items, gens):
            scores = []
            for k, (text, truncated, ntok) in enumerate(answers):
                s = C.score_answer(it, text)
                scores.append(s["reward"])
                rows.append({"setting": name, "item_id": it["item_id"], "book": it["book"], "sample": k,
                             "damage_class": it["damage_class"], "truncated": truncated, "out_tokens": ntok,
                             "answer": text, **s})
            n_signal += len(set(scores)) > 1
        sub = [r for r in rows if r["setting"] == name]
        kinds = {}
        for r in sub:
            if not r["format_valid"]:
                kinds[r["format_reason"]] = kinds.get(r["format_reason"], 0) + 1
        summary[name] = {
            "items_with_signal": round(n_signal / len(items), 3),
            "mean_reward_raw": round(sum(r["reward"] for r in sub) / len(sub), 4),
            "mean_reward_post": round(sum(r["reward_post"] for r in sub) / len(sub), 4),
            "pass_rate_raw": round(sum(r["reward"] == 1.0 for r in sub) / len(sub), 4),
            "pass_rate_post": round(sum(r["reward_post"] == 1.0 for r in sub) / len(sub), 4),
            "format_invalid_share": round(sum(not r["format_valid"] for r in sub) / len(sub), 4),
            "format_failure_kinds": kinds,
            "think_share": round(sum(r["has_think"] for r in sub) / len(sub), 4),
            "truncated_share": round(sum(r["truncated"] for r in sub) / len(sub), 4),
            "generation_seconds": round(secs, 1),
            "out_tokens_total": sum(r["out_tokens"] for r in sub),
        }
    summary["gate"] = {"rule": f"items_with_signal at rollout_T1.0 >= {GATE}",
                       "passed": summary["rollout_T1.0"]["items_with_signal"] >= GATE}
    with (out / "answers.jsonl").open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    (out / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
