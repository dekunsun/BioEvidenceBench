"""Step 0 of rl/PLAN_zh.md: the page split for task B (OCR line repair), all six bhl-impact-gt books.

    python src/rl_split_task_b.py

Pages are ordered by the scan sequence in their file name and cut into contiguous blocks of 10.
- Cuvier (histoirenaturell10cuvi) is the held-out book: every page is `heldout_book`.
- In the other five books, blocks are shuffled with a fixed seed and assigned to `train`, `dev`
  and `intest` (in-book test) at about 80/10/10; every book gets at least one dev and one intest
  block. Splitting by block, not by page, keeps neighbouring pages and repeated running heads out
  of different splits.
- The 22 BioEvidenceBench sample pages and the 16 sealed pages (rl/sealed/pages.csv) are marked
  `excluded`, whatever block they fall in: they never enter task B.
Only page IDs and order are read (no page text). Writes rl/env/task_b_ocr_repair/splits.csv and
its SHA-256, and prints a summary.
"""
from __future__ import annotations

import hashlib
import random
import re

import duckdb
import pandas as pd

from common import DATA, GT_PARQUET, ROOT

SEED = 20261120
BLOCK = 10
HELDOUT = "histoirenaturell10cuvi"
SHORT = {"conchologiaiconi05reev": "Reeve", "histoirenaturell10cuvi": "Cuvier",
         "trudyrusskagoent161881russ": "Trudy", "birdsofgreatbrit02butl": "Butler",
         "daschitinskelett00prel": "Chitinskelett", "pisciumquerelaee00sche": "Piscium"}
OUT = ROOT / "rl" / "env" / "task_b_ocr_repair"


def main() -> None:
    pages = duckdb.connect().sql(f"SELECT PageID, BarCode, file_name FROM '{GT_PARQUET}'").df()
    pages["seq"] = pages.file_name.map(lambda f: int(re.search(r"_(\d{4})_full", f).group(1)))
    pages["book"] = pages.BarCode.map(SHORT)
    pages = pages.sort_values(["BarCode", "seq"]).reset_index(drop=True)
    pages["block"] = pages.groupby("BarCode").cumcount() // BLOCK

    sample = set(pd.read_csv(DATA / "sample_split.csv").PageID.astype(int))
    sealed = set(pd.read_csv(ROOT / "rl" / "sealed" / "pages.csv").PageID.astype(int))

    split_of = {}
    for bc, g in pages.groupby("BarCode"):
        blocks = sorted(g.block.unique())
        if bc == HELDOUT:
            split_of.update({(bc, b): "heldout_book" for b in blocks})
            continue
        rng = random.Random(f"{SEED}-{bc}")
        order = blocks[:]
        rng.shuffle(order)
        n = len(order)
        n_dev = n_test = max(1, round(0.1 * n))
        for i, b in enumerate(order):
            split_of[(bc, b)] = "dev" if i < n_dev else "intest" if i < n_dev + n_test else "train"
    pages["split"] = [split_of[(r.BarCode, r.block)] for r in pages.itertuples()]
    pages.loc[pages.PageID.isin(sample), "split"] = "excluded"
    pages.loc[pages.PageID.isin(sealed), "split"] = "excluded"
    pages["excluded_why"] = ""
    pages.loc[pages.PageID.isin(sample), "excluded_why"] = "bioevidencebench_sample"
    pages.loc[pages.PageID.isin(sealed), "excluded_why"] = "sealed"

    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / "splits.csv"
    pages[["PageID", "BarCode", "book", "seq", "block", "split", "excluded_why"]].to_csv(path, index=False)
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    (OUT / "splits.csv.sha256").write_text(f"{digest}  splits.csv\n", encoding="utf-8")
    print(pd.crosstab(pages.book, pages.split, margins=True).to_string())
    print("sha256", digest)


if __name__ == "__main__":
    main()
