"""Module 7b, stage 2: GPU smoke test (METRICS.md section 6). Measures, does not compare.

    python rl/training/stage2_smoke.py --out <dir> --price 0.89            # GPU pod
    python rl/training/stage2_smoke.py --out <dir> --dry-run              # CPU: tiny model, a few steps

Two short runs from the same starting checkpoint (Qwen/Qwen3-0.6B, thinking off, prompts rendered
once by `common_7b.render_prompt`), on 2,000 training lines (half with a damaged name;
`rl/training/data/stage2_train_sample.jsonl`):

- SFT: prompt -> expert line + end-of-turn token, loss on the completion only.
- GRPO: Reward v1.3 on the raw answer (`common_7b.score_answer`), 8 answers per prompt, 16 prompts
  per optimizer step, TRL defaults otherwise (loss "dapo", std scaling per group, beta 0, vLLM
  colocated), rollout temperature 1.0, answers up to 128 tokens.

Reported: seconds per step, tokens, peak GPU memory, cost per 100 steps at --price, TRL's logged
metrics per step (reward, frac_reward_zero_std, completion length, clip ratios). No checkpoint is
kept: the point is throughput and whether the loop runs, not a model.
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import common_7b as C

TINY = "trl-internal-testing/tiny-Qwen3ForCausalLM"     # CPU dry run only


def item_from_columns(kw: dict, i: int) -> dict:
    keys = ("target", "input", "n_words", "n_damaged", "n_case_only", "name_word_flags")
    return {k: kw[k][i] for k in keys}


def reward_v13(prompts, completions, **kw):
    """TRL reward function: Reward v1.3 on each raw answer (format gate included)."""
    return [C.score_answer(item_from_columns(kw, i), c)["reward"] for i, c in enumerate(completions)]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--price", type=float, default=0.89)
    ap.add_argument("--sft-steps", type=int, default=60)
    ap.add_argument("--grpo-steps", type=int, default=60)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    import torch
    from datasets import Dataset
    from transformers import AutoTokenizer
    from trl import GRPOConfig, GRPOTrainer, SFTConfig, SFTTrainer

    gpu = torch.cuda.is_available() and not args.dry_run
    model_id = C.MODEL_ID if not args.dry_run else TINY
    tok = AutoTokenizer.from_pretrained(C.MODEL_ID)            # the real template, even in the dry run
    items = C.load_items(C.ROOT / "rl" / "training" / "data" / "stage2_train_sample.jsonl")
    assert all(it["split"] == "train" for it in items), "stage 2 trains on training lines only"
    if args.dry_run:
        items = items[:16]
    prompts = [C.render_prompt(tok, it) for it in items]
    summary = {"model": model_id, "price_usd_per_hour": args.price, "gpu": torch.cuda.get_device_name(0) if gpu else "cpu",
               "n_items": len(items), "rendered_prompt_0": prompts[0]}

    def timed(trainer, steps, name):
        if gpu:
            torch.cuda.reset_peak_memory_stats()
        t0 = time.time()
        trainer.train()
        secs = time.time() - t0
        summary[name] = {"steps": steps, "seconds": round(secs, 1), "seconds_per_step": round(secs / steps, 2),
                         "usd_per_100_steps": round(secs / steps * 100 / 3600 * args.price, 3),
                         "peak_gpu_gb": round(torch.cuda.max_memory_allocated() / 1e9, 2) if gpu else None}
        (out / f"{name}_log_history.json").write_text(json.dumps(trainer.state.log_history, indent=1))
        print(name, summary[name], flush=True)

    common = dict(output_dir=str(out / "tmp"), report_to="none", save_strategy="no", logging_steps=5,
                  bf16=gpu, seed=20261121, gradient_checkpointing=gpu)

    # --- SFT: completion = the expert line and the end-of-turn token; loss on the completion only
    sft_ds = Dataset.from_list([{"prompt": p, "completion": it["target"] + tok.eos_token}
                                for p, it in zip(prompts, items)])
    sft_args = SFTConfig(max_steps=args.sft_steps if not args.dry_run else 2, per_device_train_batch_size=16 if gpu else 4,
                         learning_rate=1e-5, max_length=512, completion_only_loss=True, **common)
    sft = SFTTrainer(model=model_id, args=sft_args, train_dataset=sft_ds, processing_class=tok)
    timed(sft, sft_args.max_steps, "sft")
    del sft
    if gpu:
        torch.cuda.empty_cache()

    # --- GRPO: 16 prompts x 8 answers = 128 completions per optimizer step
    keep = ("target", "input", "n_words", "n_damaged", "n_case_only", "name_word_flags")
    grpo_ds = Dataset.from_list([{"prompt": p, **{k: it[k] for k in keep}} for p, it in zip(prompts, items)])
    grpo_args = GRPOConfig(
        max_steps=args.grpo_steps if not args.dry_run else 2,
        num_generations=8 if gpu else 4,
        per_device_train_batch_size=32 if gpu else 4,
        gradient_accumulation_steps=4 if gpu else 1,
        max_completion_length=128 if gpu else 16,
        temperature=1.0, top_p=1.0, top_k=0, beta=0.0, loss_type="dapo", scale_rewards="group",
        learning_rate=1e-6, use_vllm=gpu, vllm_mode="colocate", vllm_gpu_memory_utilization=0.3,
        log_completions=False, **common)
    grpo = GRPOTrainer(model=model_id, reward_funcs=reward_v13, args=grpo_args, train_dataset=grpo_ds,
                       processing_class=tok)
    timed(grpo, grpo_args.max_steps, "grpo")

    hist = json.loads((out / "grpo_log_history.json").read_text())
    keys = [k for k in (hist[0] if hist else {}) if any(s in k for s in ("reward", "zero_std", "length", "clip", "kl"))]
    summary["grpo_logged_keys"] = keys
    summary["grpo_last_log"] = {k: v for k, v in (hist[-2] if len(hist) > 1 else hist[0] if hist else {}).items()}
    (out / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False))
    print(json.dumps({k: v for k, v in summary.items() if k != "rendered_prompt_0"}, indent=2, default=str))


if __name__ == "__main__":
    main()
