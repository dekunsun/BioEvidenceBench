"""Step 0 of rl/PLAN_zh.md: seal 16 new test pages for the next blind entity test.

    python src/rl_seal_pages.py

Sampling frame: Butler and Reeve pages in bhl-impact-gt (data/cache/gt_english.parquet), minus
the 22 sample pages (data/sample_split.csv), pages whose expert text is under 300 characters, and
pages whose BHL PageTypeName contains "Index" (out of scope, GUIDE_ADDENDUM.md). 8 pages per book
are drawn with a fixed seed. Only page IDs are written; no page text is read or printed here.

Writes rl/sealed/pages.csv and rl/sealed/pages.csv.sha256. Sealed pages are never sent to a model
and never used in rl/ training data. To unseal: Gloria labels them first (guide v0.10), the labels
are committed, then a line goes into rl/LOG.md.
"""
from __future__ import annotations

import hashlib
import random

import pandas as pd

from common import CACHE, DATA, ROOT

SEED = 20261120
PER_BOOK = 8
MIN_CHARS = 300
OUT = ROOT / "rl" / "sealed"


def main() -> None:
    gt = pd.read_parquet(CACHE / "gt_english.parquet",
                         columns=["PageID", "BarCode", "gt_chars", "PageTypeName", "SequenceOrder"])
    sample = set(pd.read_csv(DATA / "sample_split.csv").PageID.astype(int))
    book = {"birdsofgreatbrit02butl": "Butler", "conchologiaiconi05reev": "Reeve"}
    frame = gt[~gt.PageID.isin(sample)
               & (gt.gt_chars >= MIN_CHARS)
               & ~gt.PageTypeName.fillna("").str.contains("Index")].copy()
    frame["book"] = frame.BarCode.map(book)
    rows = []
    for b in ("Butler", "Reeve"):
        ids = sorted(frame.loc[frame.book == b, "PageID"].astype(int))
        drawn = random.Random(f"{SEED}-{b}").sample(ids, PER_BOOK)
        rows += [{"PageID": p, "book": b, "draw_order": i + 1, "frame_size": len(ids)}
                 for i, p in enumerate(drawn)]
    OUT.mkdir(parents=True, exist_ok=True)
    out = pd.DataFrame(rows)
    path = OUT / "pages.csv"
    out.to_csv(path, index=False)
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    (OUT / "pages.csv.sha256").write_text(f"{digest}  pages.csv\n", encoding="utf-8")
    print(f"sealed {len(out)} pages (frame: Butler {rows[0]['frame_size']}, Reeve {rows[-1]['frame_size']}); "
          f"sha256 {digest}")


if __name__ == "__main__":
    main()
