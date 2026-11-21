"""Module 7b, stage 4: draw the locked test sets once (TEST_PROTOCOL.md). CPU, run here.

    python rl/training/make_test_p0.py

- `data/p0_test_inbook.jsonl`: 500 lines of split v2 `intest`, 100 per training book, seed 20261122,
  leaving out the 22 in-book test lines (17 of them usable) that the alignment audits displayed.
- `data/p0_test_cuvier.jsonl`: 500 usable lines of the held-out book (`rl_task_b_build_cuvier.py`),
  same seed, drawn uniformly.
- `data/p0_test_inbook_rest.jsonl`: every other usable in-book test line (larger confirmation, P1).
- `configs/TEST_SETS.md`: counts by book and kind, SHA-256 of each file. No line text is printed.
"""
from __future__ import annotations

import hashlib
import json
import random

import pandas as pd

import common_7b as C
from make_data_p0 import add_context, describe

UNITS = C.ROOT / "data" / "cache" / "taskb" / "units"
OUT = C.ROOT / "rl" / "training" / "data"
BUILD = C.ROOT / "rl" / "env" / "task_b_ocr_repair" / "build"
SEED, PER_BOOK, N_CUVIER = 20261122, 100, 500


def audited_lines() -> set[tuple[int, int]]:
    a = pd.concat([pd.read_csv(BUILD / "audit_sample.csv")[["page_id", "line_no"]],
                   pd.read_csv(BUILD / "audit_round1" / "audit_sample_round1_claude.csv")[["page_id", "line_no"]]])
    return {(int(p), int(n)) for p, n in zip(a.page_id, a.line_no)}


def main() -> None:
    load = lambda f: [json.loads(line) for line in (UNITS / f).open(encoding="utf-8")]  # noqa: E731
    intest, cuvier = load("intest.jsonl"), load("cuvier.jsonl")
    assert all(u["split"] == "intest" for u in intest) and all(u["book"] == "Cuvier" for u in cuvier)
    seen = audited_lines()
    pool = [u for u in intest if (u["page_id"], u["line_no"]) not in seen]
    n_left_out = len(intest) - len(pool)
    rng = random.Random(SEED)
    chosen = []
    for book in sorted({u["book"] for u in pool}):
        us = sorted((u for u in pool if u["book"] == book), key=lambda u: (u["page_id"], u["line_no"]))
        chosen += rng.sample(us, PER_BOOK)
    ids = {(u["page_id"], u["line_no"]) for u in chosen}
    rest = [u for u in pool if (u["page_id"], u["line_no"]) not in ids]
    cuv = rng.sample(sorted(cuvier, key=lambda u: (u["page_id"], u["line_no"])), N_CUVIER)

    in_idx = pd.read_csv(UNITS / "all_units_index.csv")
    cu_idx = pd.DataFrame([json.loads(line) for line in (UNITS / "cuvier_all_units.jsonl").open(encoding="utf-8")
                           if "line_no" in json.loads(line)])[["page_id", "line_no", "input"]]
    order = lambda us: sorted(us, key=lambda u: (u["book"], u["page_id"], u["line_no"]))  # noqa: E731
    files = {"p0_test_inbook": order(add_context(chosen, in_idx)),
             "p0_test_cuvier": order(add_context(cuv, cu_idx)),
             "p0_test_inbook_rest": order(add_context(rest, in_idx))}
    md = ["# Locked test sets (module 7b, stage 4)", "",
          f"*Drawn once by `rl/training/make_test_p0.py`, seed {SEED}, 2026-11-21, before any test line was "
          f"scored. In-book: {PER_BOOK} per training book from split v2 `intest`, leaving out the "
          f"{n_left_out} usable lines that the alignment audits displayed. Cuvier: {N_CUVIER} usable lines "
          "drawn uniformly. Rest: every other usable in-book test line. Context = nearest OCR line above / "
          "below on the same page.*", ""]
    for name, items in files.items():
        p = OUT / f"{name}.jsonl"
        C.write_items(items, p)
        md += describe(name, items, p)
    (C.ROOT / "rl" / "training" / "configs" / "TEST_SETS.md").write_text("\n".join(md), encoding="utf-8")
    print("\n".join(md))
    print({n: hashlib.sha256((OUT / f"{n}.jsonl").read_bytes()).hexdigest()[:12] for n in files})


if __name__ == "__main__":
    main()
