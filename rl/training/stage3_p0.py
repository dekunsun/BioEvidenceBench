"""Module 7b, stage 3: P0 primary runs for one seed, checkpoints chosen on dev. Runs on the GPU pod.

    python rl/training/stage3_p0.py all --seed 1 --out <dir> --price 0.89

One pod per seed. In order, each step in its own Python process (so GPU memory is freed between
steps and a crash in one step leaves the earlier results on disk):

1. Base (A) answers on the dev sets.
2. B, SFT from the base model on `data/p0_train.jsonl` (one pass, 300 steps of 16 lines, lr 1e-5),
   a checkpoint every 50 steps; every checkpoint answers the dev sets; one is chosen (rule below).
3. C, GRPO from the base model on the same file (300 steps of 16 prompts x 8 answers, Reward v1.3,
   the stage-2 settings), checkpoints, dev answers, choice.
4. D, GRPO from B's chosen checkpoint, same settings as C.
5. The chosen checkpoints of B, C and D are saved in bf16 and uploaded as assets of a draft GitHub
   release (they are too large for git), for the locked test in stage 4. No test line is read here.

Dev answers: `p0_dev_eval.jsonl` (500 lines, 100 per book) and `p0_dev_names.jsonl` (85 lines with a
damaged name), the evaluation decoding of METRICS.md 2a (T 0.7, top-p 0.8, top-k 20), 4 answers per
line, the same sampling seed for every model.

**Checkpoint rule, fixed before the runs** (dev, `p0_dev_eval` only): the checkpoint with the highest
post-processed damaged-word repair rate among those whose post-processed preservation is at least
Base's minus 0.01; ties go to the earlier step; if none qualifies, the one with the highest
preservation, flagged `no_checkpoint_qualified`. Step 0 is not a candidate.

Development settings (logged in rl/LOG.md): master weights in float32 with bf16 autocast (pure bf16
weights would round away most updates at lr 1e-6); GRPO reads the training blocks in a seed-specific
block order (`shuffle_dataset=False`, so every step keeps the 8 / 3 / 5 mix), because TRL gives
vLLM the same sampling seed in every run and identical data order would make two seeds nearly
the same run. Every GRPO completion is logged with its step and reward (`*_completions.jsonl.gz`).
"""
from __future__ import annotations

import argparse
import gzip
import json
import os
import random
import shutil
import subprocess
import sys
import tarfile
import time
from pathlib import Path

import common_7b as C

DATA = C.ROOT / "rl" / "training" / "data"
DEV_SETS = ("p0_dev_eval", "p0_dev_names")
EVAL = dict(temperature=0.7, top_p=0.8, top_k=20, min_p=0.0)
EVAL_K, EVAL_SEED, MAX_TOKENS = 4, 20261121, 128
STEPS, SAVE_EVERY, BLOCK = 300, 50, 16
REPO = "dekunsun/BioEvidenceBench"
PY = sys.executable


def log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


# ---------------------------------------------------------------- evaluation (one model, one process)
def cmd_eval(args) -> None:
    from transformers import AutoTokenizer
    from vllm import LLM, SamplingParams
    tok = AutoTokenizer.from_pretrained(C.MODEL_ID)            # the one renderer and template, always the base's
    llm = LLM(model=args.model, dtype="bfloat16", seed=EVAL_SEED, gpu_memory_utilization=0.85,
              max_model_len=2048, enforce_eager=True)
    sp = SamplingParams(n=EVAL_K, max_tokens=MAX_TOKENS, seed=EVAL_SEED, **EVAL)
    out = Path(args.out)
    result = {"model": args.model, "label": args.label, "decoding": EVAL, "k": EVAL_K, "seed": EVAL_SEED}
    for name in DEV_SETS:
        items = C.load_items(DATA / f"{name}.jsonl")
        assert all(it["split"] == "dev" for it in items)
        t0 = time.time()
        gens = llm.generate([C.render_prompt(tok, it) for it in items], sp)
        rows = []
        for it, g in zip(items, gens):
            for k, c in enumerate(g.outputs):
                rows.append({"item_id": it["item_id"], "book": it["book"], "sample": k, "answer": c.text,
                             "truncated": c.finish_reason == "length", "out_tokens": len(c.token_ids),
                             "run_on": C.run_on(it, c.text), **C.score_answer(it, c.text)})
        m = C.primary_metrics(items, rows)
        m["seconds"] = round(time.time() - t0, 1)
        m["truncated_share"] = round(sum(r["truncated"] for r in rows) / len(rows), 4)
        m["run_on_share"] = round(sum(r["run_on"] != "within" for r in rows) / len(rows), 4)
        m["think_share"] = round(sum(r["has_think"] for r in rows) / len(rows), 4)
        m["per_book"] = {b: C.primary_metrics(items, [r for r in rows if r["book"] == b])
                         for b in sorted({r["book"] for r in rows})}
        result[name] = m
        with gzip.open(out.parent / f"{out.name}_{name}_answers.jsonl.gz", "wt", encoding="utf-8") as f:
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
    out.with_suffix(".json").write_text(json.dumps(result, indent=1, ensure_ascii=False))


# ---------------------------------------------------------------- training
def train_items(seed: int) -> list[dict]:
    """The P0 file in a seed-specific order of its 16-line blocks (each block = one GRPO step)."""
    items = C.load_items(DATA / "p0_train.jsonl")
    assert all(it["split"] == "train" for it in items) and len(items) == STEPS * BLOCK
    blocks = [items[i:i + BLOCK] for i in range(0, len(items), BLOCK)]
    random.Random(1000 + seed).shuffle(blocks)
    return [it for b in blocks for it in b]


def common_args(out: Path, seed: int, steps: int = STEPS) -> dict:
    import torch
    return dict(output_dir=str(out), report_to="none", save_strategy="steps", save_steps=SAVE_EVERY,
                save_only_model=True, logging_steps=5, bf16=True, seed=seed, gradient_checkpointing=True,
                max_steps=steps, model_init_kwargs={"dtype": torch.float32})


def cmd_sft(args) -> None:
    from datasets import Dataset
    from transformers import AutoTokenizer
    from trl import SFTConfig, SFTTrainer
    tok = AutoTokenizer.from_pretrained(C.MODEL_ID)
    items = train_items(args.seed)
    ds = Dataset.from_list([{"prompt": C.render_prompt(tok, it), "completion": it["target"] + tok.eos_token}
                            for it in items])
    cfg = SFTConfig(per_device_train_batch_size=16, learning_rate=1e-5, max_length=512, completion_only_loss=True,
                    **common_args(Path(args.ckpt), args.seed, args.steps))
    tr = SFTTrainer(model=args.init, args=cfg, train_dataset=ds, processing_class=tok)
    t0 = time.time()
    tr.train()
    Path(args.out).write_text(json.dumps({"seconds": round(time.time() - t0, 1), "log_history": tr.state.log_history,
                                          "rendered_prompt_0": ds[0]["prompt"]}, indent=1))


def cmd_grpo(args) -> None:
    from datasets import Dataset
    from transformers import AutoTokenizer
    from trl import GRPOConfig, GRPOTrainer
    tok = AutoTokenizer.from_pretrained(C.MODEL_ID)
    items = train_items(args.seed)
    keep = ("item_id", "target", "input", "n_words", "n_damaged", "n_case_only", "name_word_flags")
    ds = Dataset.from_list([{"prompt": C.render_prompt(tok, it), **{k: it[k] for k in keep}} for it in items])
    clog = gzip.open(args.completions, "wt", encoding="utf-8")

    def reward_v13(prompts, completions, trainer_state=None, **kw):
        out = []
        for i, c in enumerate(completions):
            it = {k: kw[k][i] for k in keep}
            s = C.score_answer(it, c)
            out.append(s["reward"])
            clog.write(json.dumps({"step": trainer_state.global_step if trainer_state else None,
                                   "item_id": it["item_id"], "completion": c, "reward": s["reward"],
                                   "format_reason": s["format_reason"], "repaired": s["repaired"],
                                   "broken": s["broken"], "copy": c.strip() == it["input"].strip()},
                                  ensure_ascii=False) + "\n")
        clog.flush()
        return out

    cfg = GRPOConfig(num_generations=8, per_device_train_batch_size=args.per_device,
                     gradient_accumulation_steps=128 // args.per_device, max_completion_length=MAX_TOKENS,
                     temperature=1.0, top_p=1.0, top_k=0, beta=0.0, loss_type="dapo", scale_rewards="group",
                     learning_rate=1e-6, use_vllm=True, vllm_mode="colocate",
                     vllm_gpu_memory_utilization=args.vllm_util, shuffle_dataset=False, log_completions=False,
                     **common_args(Path(args.ckpt), args.seed))
    tr = GRPOTrainer(model=args.init, reward_funcs=reward_v13, args=cfg, train_dataset=ds, processing_class=tok)
    t0 = time.time()
    tr.train()
    clog.close()
    Path(args.out).write_text(json.dumps({"seconds": round(time.time() - t0, 1), "log_history": tr.state.log_history,
                                          "per_device": args.per_device, "vllm_util": args.vllm_util,
                                          "rendered_prompt_0": ds[0]["prompt"]}, indent=1))


# ---------------------------------------------------------------- driver
def run(cmd: list[str], logfile: Path) -> int:
    log("run: " + " ".join(cmd[1:]))
    with logfile.open("a") as f:
        return subprocess.run(cmd, stdout=f, stderr=subprocess.STDOUT).returncode


def to_bf16(src: Path, dst: Path) -> Path:
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    AutoModelForCausalLM.from_pretrained(src, dtype=torch.bfloat16).save_pretrained(dst)
    AutoTokenizer.from_pretrained(C.MODEL_ID).save_pretrained(dst)
    return dst


def choose(evals: dict[int, dict], base: dict) -> dict:
    floor = base["p0_dev_eval"]["preservation_post"] - 0.01
    cands = [(s, e["p0_dev_eval"]) for s, e in sorted(evals.items())]
    ok = [(s, m) for s, m in cands if m["preservation_post"] >= floor]
    if ok:
        step = max(ok, key=lambda x: (x[1]["repair_rate_post"], -x[0]))[0]
        return {"step": step, "flag": "", "preservation_floor": round(floor, 4)}
    step = max(cands, key=lambda x: (x[1]["preservation_post"], -x[0]))[0]
    return {"step": step, "flag": "no_checkpoint_qualified", "preservation_floor": round(floor, 4)}


def gh_headers() -> dict:
    return {"Authorization": f"Bearer {os.environ['GITHUB_TOKEN']}", "Accept": "application/vnd.github+json"}


def create_release(run_id: str, body: str) -> int | None:
    import requests
    r = requests.post(f"https://api.github.com/repos/{REPO}/releases", headers=gh_headers(), timeout=60,
                      json={"tag_name": f"rl-ckpt-{run_id}", "name": f"rl 7b checkpoints {run_id}", "draft": True,
                            "body": body})
    log(f"create draft release: HTTP {r.status_code}")
    return r.json()["id"] if r.status_code == 201 else None


def upload_assets(release_id: int, files: list[Path]) -> dict:
    import requests
    done = {"ok": True, "release_id": release_id, "assets": []}
    for f in files:
        size = f.stat().st_size
        for attempt in range(3):
            try:
                with f.open("rb") as fh:
                    a = requests.post(f"https://uploads.github.com/repos/{REPO}/releases/{release_id}/assets",
                                      params={"name": f.name}, data=fh, timeout=3600,
                                      headers={**gh_headers(), "Content-Type": "application/octet-stream"})
                if a.status_code == 201 and a.json().get("size") == size:
                    done["assets"].append({"name": f.name, "size": size, "id": a.json()["id"]})
                    break
                log(f"upload {f.name}: HTTP {a.status_code} (attempt {attempt + 1})")
            except Exception as e:  # noqa: BLE001 (network errors; the message has no secret)
                log(f"upload {f.name}: {type(e).__name__} (attempt {attempt + 1})")
        else:
            done["ok"] = False
    return done


def cmd_all(args) -> None:
    out, ck = Path(args.out), Path(args.ckpt_root)
    out.mkdir(parents=True, exist_ok=True)
    ck.mkdir(parents=True, exist_ok=True)
    s = args.seed
    joblog = out / f"steps_s{s}.log"
    summary = {"seed": s, "model": C.MODEL_ID, "prompt_version": C.PROMPT_VERSION, "price_usd_per_hour": args.price,
               "steps": STEPS, "save_every": SAVE_EVERY, "eval": {"decoding": EVAL, "k": EVAL_K, "seed": EVAL_SEED},
               "conditions": {}}

    def save():
        (out / f"summary_s{s}.json").write_text(json.dumps(summary, indent=1, ensure_ascii=False))

    def evaluate(model: str, label: str) -> dict | None:
        t0 = time.time()
        code = run([PY, __file__, "eval", "--model", model, "--label", label, "--out", str(out / label)], joblog)
        f = (out / label).with_suffix(".json")
        if code != 0 or not f.exists():
            log(f"eval {label} failed ({code})")
            return None
        e = json.loads(f.read_text())
        e["wall_seconds"] = round(time.time() - t0, 1)
        return e

    def train_and_choose(cond: str, kind: str, init: str, base: dict, steps: int = STEPS) -> Path | None:
        cdir = ck / f"{cond}_s{s}"
        t0 = time.time()
        cmd = [PY, __file__, kind, "--seed", str(s), "--init", init, "--ckpt", str(cdir),
               "--out", str(out / f"{cond}_s{s}_train.json")]
        if kind == "sft":
            cmd += ["--steps", str(steps)]
        if kind == "grpo":
            cmd += ["--completions", str(out / f"{cond}_s{s}_completions.jsonl.gz")]
            code = run(cmd + ["--per-device", "16", "--vllm-util", "0.3"], joblog)
            if code != 0 and "out of memory" in joblog.read_text()[-20000:].lower():
                log(f"{cond}: out of memory, retrying with 8 per device and vLLM at 0.25")
                shutil.rmtree(cdir, ignore_errors=True)
                code = run(cmd + ["--per-device", "8", "--vllm-util", "0.25"], joblog)
        else:
            code = run(cmd, joblog)
        info = {"kind": kind, "init": init, "steps": steps, "train_exit": code,
                "train_wall_seconds": round(time.time() - t0, 1)}
        summary["conditions"][cond] = info
        save()
        if code != 0:
            log(f"{cond} training failed ({code})")
            return None
        evals = {}
        for step in range(SAVE_EVERY, steps + 1, SAVE_EVERY):
            e = evaluate(str(cdir / f"checkpoint-{step}"), f"{cond}_s{s}_step{step}")
            if e:
                evals[step] = e
        info["dev"] = {st: {n: {k: v for k, v in e[n].items() if k != "per_book"} for n in DEV_SETS}
                       for st, e in evals.items()}
        if not evals:
            save()
            return None
        info["chosen"] = choose(evals, base)
        chosen = cdir / f"checkpoint-{info['chosen']['step']}"
        best = to_bf16(chosen, ck / f"{cond}_s{s}_chosen_bf16")
        for st in range(SAVE_EVERY, steps + 1, SAVE_EVERY):          # free the disk
            if st != info["chosen"]["step"]:
                shutil.rmtree(cdir / f"checkpoint-{st}", ignore_errors=True)
        log(f"{cond}: chose step {info['chosen']}")
        save()
        return best

    # The checkpoints can only be kept through a release: check that before any training (a failure
    # costs the set-up only, not a run whose checkpoints would be lost when the pod is deleted).
    run_id = os.environ.get("RUN_ID", out.name)
    body = (f"Module 7b stage 3 (P0), seed {s}, run {run_id}: dev-chosen checkpoints in bf16, for the locked "
            "test in stage 4. Not evaluated on any test line. Qwen3-0.6B (Apache 2.0) fine-tuned on public BHL / "
            "IMPACT text (CC-BY 3.0).")
    rel = create_release(run_id, body) if os.environ.get("GITHUB_TOKEN") else None
    probe = out / "release_probe.txt"
    probe.write_text(f"upload check for {run_id}\n")
    summary["release_check"] = upload_assets(rel, [probe]) if rel else {"ok": False}
    save()
    if not summary["release_check"]["ok"]:
        sys.exit("cannot upload to a GitHub release: stopping before training")

    base = evaluate(C.MODEL_ID, f"base_s{s}")
    summary["base"] = {n: {k: v for k, v in base[n].items() if k != "per_book"} for n in DEV_SETS} if base else None
    save()
    if not base:
        sys.exit("base evaluation failed")
    chosen = {}
    conds = args.conditions.split(",")
    summary["sft_steps"] = args.sft_steps
    summary["conditions_run"] = conds
    sft = train_and_choose("sft", "sft", C.MODEL_ID, base, args.sft_steps)
    chosen["sft"] = sft
    if "grpo" in conds:
        chosen["grpo"] = train_and_choose("grpo", "grpo", C.MODEL_ID, base)
    if sft is not None and "sft_grpo" in conds:
        chosen["sft_grpo"] = train_and_choose("sft_grpo", "grpo", str(sft), base)

    tars = []
    for cond, path in chosen.items():
        if path is None:
            continue
        t = ck / f"{cond}_s{s}.tar"
        with tarfile.open(t, "w") as tf:
            tf.add(path, arcname=f"{cond}_s{s}")
        tars.append(t)
    summary["checkpoint_upload"] = upload_assets(rel, tars) if tars else {"ok": False, "error": "no checkpoints"}
    save()
    log(f"done: {json.dumps(summary['checkpoint_upload'])}")
    failed = [c for c in conds if chosen.get(c) is None]
    if failed or not summary["checkpoint_upload"]["ok"]:
        sys.exit(f"incomplete: failed {failed}, upload ok {summary['checkpoint_upload']['ok']}")


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("all")
    a.add_argument("--seed", type=int, required=True)
    a.add_argument("--out", required=True)
    a.add_argument("--ckpt-root", default="/workspace/ckpt")
    a.add_argument("--price", type=float, default=0.89)
    a.add_argument("--sft-steps", type=int, default=STEPS)
    a.add_argument("--conditions", default="sft,grpo,sft_grpo", help="sft is always run (D starts from it)")
    e = sub.add_parser("eval")
    e.add_argument("--model", required=True)
    e.add_argument("--label", required=True)
    e.add_argument("--out", required=True)
    for name in ("sft", "grpo"):
        t = sub.add_parser(name)
        t.add_argument("--seed", type=int, required=True)
        t.add_argument("--init", required=True)
        t.add_argument("--ckpt", required=True)
        t.add_argument("--out", required=True)
        if name == "sft":
            t.add_argument("--steps", type=int, default=STEPS)
        if name == "grpo":
            t.add_argument("--completions", required=True)
            t.add_argument("--per-device", type=int, default=16)
            t.add_argument("--vllm-util", type=float, default=0.3)
    args = ap.parse_args()
    {"all": cmd_all, "eval": cmd_eval, "sft": cmd_sft, "grpo": cmd_grpo}[args.cmd](args)


if __name__ == "__main__":
    main()
