"""Module 7b, stage 3 (P0): build the training mix and the dev evaluation set. CPU, run here.

    python rl/training/make_data_p0.py

Writes, with a fixed seed:
- `rl/training/data/p0_train.jsonl`: 4,800 training lines = 300 GRPO steps x 16 prompts, in blocks
  of 16 that each hold 8 lines with a damaged scientific name (names oversampled to half of every
  batch, METRICS.md section 1), 3 clean lines (19%; Gloria, 2026-11-21: "about 20%") and 5 other
  damaged lines. GRPO reads the file in order (`shuffle_dataset=False`), so every optimizer step
  has this mix; SFT reads the same lines shuffled. B, C and D use this one file.
  There are 1,280 distinct damaged-name lines in train, so each appears once or twice; clean and
  other damaged lines are drawn without repetition.
- `rl/training/data/p0_dev_eval.jsonl`: 500 dev lines, 100 per book, for choosing checkpoints
  (dev is not blind; never a reported result).
- `rl/training/data/p0_dev_names.jsonl`: every other dev line with a damaged scientific name, so that
  name recovery on dev rests on more than a handful of lines (diagnostic; not used to choose).
- `rl/training/data/P0_DATA.md`: counts and file hashes.

Context lines are the nearest line above / below on the same page with OCR text (the rule of the
stage-1 items, `rl_task_b_trial.with_context`), computed per page here for speed.
"""
from __future__ import annotations

import collections
import hashlib
import json
import random
from pathlib import Path

import pandas as pd

import common_7b as C

UNITS = C.ROOT / "data" / "cache" / "taskb" / "units"
OUT = C.ROOT / "rl" / "training" / "data"
SEED = 20261121
STEPS, BLOCK = 300, 16
PER_BLOCK = {"name": 8, "clean": 3, "other": 5}
DEV_PER_BOOK = 100


def damage_class(n: int) -> str:
    return "clean" if n == 0 else "1" if n == 1 else "2-5" if n <= 5 else ">5"


def add_context(units: list[dict], idx: pd.DataFrame) -> list[dict]:
    idx = idx[idx.input.fillna("").str.strip() != ""]
    pages = {pid: g.sort_values("line_no") for pid, g in idx.groupby("page_id")}
    out = []
    for u in units:
        pg = pages.get(u["page_id"])
        before = pg[pg.line_no < u["line_no"]].input if pg is not None else []
        after = pg[pg.line_no > u["line_no"]].input if pg is not None else []
        u = dict(u, prev=before.iloc[-1] if len(before) else "(none)",
                 next=after.iloc[0] if len(after) else "(none)",
                 item_id=f"{u['page_id']}-{u['line_no']}", damage_class=damage_class(u["n_damaged"]))
        out.append(u)
    return out


def kind(u: dict) -> str:
    return "name" if u["n_name_damaged"] > 0 else "clean" if u["n_damaged"] == 0 else "other"


def build_train(units: list[dict], rng: random.Random) -> list[dict]:
    pools = collections.defaultdict(list)
    for u in units:
        pools[kind(u)].append(u)
    need = {k: v * STEPS for k, v in PER_BLOCK.items()}
    draw = {}
    for k, pool in pools.items():
        pool = sorted(pool, key=lambda u: u["item_id"])
        rng.shuffle(pool)
        if need[k] <= len(pool):
            draw[k] = pool[:need[k]]
        else:                                    # names: every line once, then a second pass for the rest
            reps = pool + rng.sample(pool, need[k] - len(pool))
            rng.shuffle(reps)
            draw[k] = reps
    blocks = []
    for b in range(STEPS):
        block = [u for k, n in PER_BLOCK.items() for u in draw[k][b * n:(b + 1) * n]]
        rng.shuffle(block)
        blocks.append(block)
    return [u for blk in blocks for u in blk]


def build_dev(units: list[dict], rng: random.Random) -> list[dict]:
    out = []
    for book in sorted(C.BOOKS):
        us = sorted((u for u in units if u["book"] == book), key=lambda u: u["item_id"])
        out += rng.sample(us, min(DEV_PER_BOOK, len(us)))
    return sorted(out, key=lambda u: (u["book"], u["page_id"], u["line_no"]))


def describe(name: str, items: list[dict], path: Path) -> list[str]:
    df = pd.DataFrame(items)
    df["kind"] = df.apply(kind, axis=1)
    lines = [f"## {name}", "", f"`{path.relative_to(C.ROOT)}`: {len(df)} lines, {df.item_id.nunique()} distinct, "
             f"SHA-256 `{hashlib.sha256(path.read_bytes()).hexdigest()}`", "",
             pd.crosstab(df.book, df.kind, margins=True).to_markdown(), "",
             "Share by kind: " + ", ".join(f"{k} {v:.1%}" for k, v in df.kind.value_counts(normalize=True).items()), ""]
    return lines


def main() -> None:
    idx = pd.read_csv(UNITS / "all_units_index.csv")
    train = [json.loads(line) for line in (UNITS / "train.jsonl").open(encoding="utf-8")]
    dev = [json.loads(line) for line in (UNITS / "dev.jsonl").open(encoding="utf-8")]
    assert all(u["split"] == "train" for u in train) and all(u["split"] == "dev" for u in dev)
    assert all(u["valid"] and not u["set_aside"] for u in train + dev), "only usable lines"
    rng = random.Random(SEED)
    tr = build_train(add_context(train, idx), rng)
    dv = build_dev(add_context(dev, idx), rng)
    for blk in range(STEPS):                     # the batch mix holds in every block
        c = collections.Counter(kind(u) for u in tr[blk * BLOCK:(blk + 1) * BLOCK])
        assert c == collections.Counter(PER_BLOCK), (blk, c)
    chosen = {u["item_id"] for u in dv}
    dn = sorted((u for u in add_context([u for u in dev if u["n_name_damaged"] > 0], idx)
                 if u["item_id"] not in chosen), key=lambda u: (u["book"], u["page_id"], u["line_no"]))
    pt, pd_, pn = OUT / "p0_train.jsonl", OUT / "p0_dev_eval.jsonl", OUT / "p0_dev_names.jsonl"
    C.write_items(tr, pt)
    C.write_items(dv, pd_)
    C.write_items(dn, pn)
    md = ["# P0 data (module 7b, stage 3)", "",
          f"*Built by `rl/training/make_data_p0.py`, seed {SEED}. Training lines from split v2 `train`, dev lines "
          "from `dev`; set-aside lines excluded by the build. Kinds: `name` = at least one damaged scientific-name "
          "word, `clean` = no damaged word, `other` = damaged, no damaged name word.*", "",
          f"Training blocks of {BLOCK} (one GRPO optimizer step each, read in order): " +
          ", ".join(f"{v} {k}" for k, v in PER_BLOCK.items()) + ".", ""]
    md += describe("Training mix", tr, pt) + describe("Dev evaluation set", dv, pd_) + describe("Dev name lines", dn, pn)
    (OUT / "P0_DATA.md").write_text("\n".join(md), encoding="utf-8")
    print("\n".join(md))


if __name__ == "__main__":
    main()
