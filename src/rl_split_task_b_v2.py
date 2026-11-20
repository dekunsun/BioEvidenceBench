"""Task B split v2 (Gloria, 2026-11-20): stratify by content pages, not by all pages.

    python src/rl_split_task_b_v2.py

Why: under split v1 (`rl_split_task_b.py`, blocks of 10 scan pages) the dev blocks of the two small
books fell on plates and blank pages: Piscium querelae had no dev line and Das Chitinskelett 10.
Reward checks and GRPO development curves could not be read for those books.

Rule (fixed before any model has seen a task B page; no model output and no alignment result is
read, so the split cannot select on how well a page aligns or how a model does on it):
- A **content page** has at least one expert-transcription line of 15 characters and 2 words
  (the same minimum a line needs to become a unit). Only the expert transcription is read.
- Cuvier is the held-out book and is not read at all: its pages stay `heldout_book`.
- The 22 BioEvidenceBench sample pages and the 16 sealed pages stay `excluded`.
- Other pages that are not content pages are `no_text` (never used).
- Content pages of each book, in scan order, are cut into contiguous blocks: 10 pages for books
  with 100 content pages or more, 5 for smaller books. Blocks are shuffled with a fixed seed and
  assigned to dev and intest, each max(2, round(0.1 * blocks)) blocks, and the rest to train.

Writes rl/env/task_b_ocr_repair/splits_v2.csv (+ .sha256) and SPLIT_V2.md, a comparison with v1
(pages per split, and pages that moved). splits.csv (v1) is kept unchanged as the record.
"""
from __future__ import annotations

import hashlib
import random

import pandas as pd

import rl_task_b as T
from common import ROOT

SEED = 20261120
OUT = ROOT / "rl" / "env" / "task_b_ocr_repair"
HELDOUT_BOOK = "Cuvier"


def is_content(pid: int) -> bool:
    return any(len(s.strip()) >= 15 and len(T.words(s.strip())) >= 2 for s in T.expert_text(pid).split("\n"))


def main() -> None:
    v1 = pd.read_csv(OUT / "splits.csv")
    v2 = v1.copy()
    v2["block"] = -1
    for book, g in v1.groupby("book"):
        if book == HELDOUT_BOOK:
            continue
        g = g.sort_values("seq")
        usable = g[g.split != "excluded"]
        content = [int(p) for p in usable.PageID if is_content(int(p))]
        v2.loc[usable.index[~usable.PageID.isin(content)], "split"] = "no_text"
        size = 10 if len(content) >= 100 else 5
        blocks = [content[i:i + size] for i in range(0, len(content), size)]
        order = list(range(len(blocks)))
        random.Random(f"{SEED}-v2-{book}").shuffle(order)
        n_hold = max(2, round(0.1 * len(blocks)))
        for rank, bi in enumerate(order):
            split = "dev" if rank < n_hold else "intest" if rank < 2 * n_hold else "train"
            idx = v2.index[v2.PageID.isin(blocks[bi])]
            v2.loc[idx, "split"] = split
            v2.loc[idx, "block"] = bi
    path = OUT / "splits_v2.csv"
    v2[["PageID", "BarCode", "book", "seq", "block", "split", "excluded_why"]].to_csv(path, index=False)
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    (OUT / "splits_v2.csv.sha256").write_text(f"{digest}  splits_v2.csv\n", encoding="utf-8")

    both = v1[["PageID", "book", "split"]].merge(v2[["PageID", "split"]], on="PageID", suffixes=("_v1", "_v2"))
    moved = both[both.split_v1 != both.split_v2]
    lines = ["# Task B split v2: by content pages", "",
             "Rule and reasons: docstring of `src/rl_split_task_b_v2.py` (Gloria's decision, 2026-11-20). "
             "No model had been run on any task B page when the split was changed, and the rule reads only "
             "the expert transcription, so the change cannot pick pages by results. Cuvier is not read. "
             f"`splits.csv` (v1) is kept unchanged. SHA-256 of `splits_v2.csv`: `{digest}`.", "",
             "## Pages per split, v1", "", pd.crosstab(v1.book, v1.split, margins=True).to_markdown(), "",
             "## Pages per split, v2", "", pd.crosstab(v2.book, v2.split, margins=True).to_markdown(), "",
             "## Pages that changed split (v1 → v2)", "",
             pd.crosstab([moved.book, moved.split_v1], moved.split_v2).to_markdown() if len(moved) else "none", "",
             f"{len(moved)} of {len(v1)} pages changed split. Line counts per split are in `build/STATS.md`."]
    (OUT / "SPLIT_V2.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
