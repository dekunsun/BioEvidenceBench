"""Split the proposed sample into a development set and a locked test set.

  dev   prompts, deterministic checks and review thresholds are tuned here,
        and the pilot extraction runs here. Model output on dev pages may be
        looked at.
  test  locked. Nobody looks at model output on these pages until the gold
        set is finished and PREREGISTRATION.md is written.

Pages in the same book that are close together share layout, terms and OCR
quirks, so they must not straddle the split. We group proposed pages whose
SequenceOrder is within GAP of each other into one block, and assign whole
blocks. Per book we take DEV_PER_BOOK pages for dev, preferring blocks from
different strata and spread over the CER range; the rest is test.

Deterministic: re-running gives the same split.

Output: data/sample_split.csv
Run:    python src/split_sample.py
"""
from __future__ import annotations

import pandas as pd

from common import DATA

GAP = 2
DEV_PER_BOOK = 3


def blocks(d: pd.DataFrame) -> pd.Series:
    """Label consecutive-ish pages (SequenceOrder gap <= GAP) with one block id."""
    d = d.sort_values("SequenceOrder")
    new_block = d.SequenceOrder.diff().fillna(GAP + 1) > GAP
    return new_block.cumsum().reindex(d.index)


def main() -> None:
    prop = pd.read_csv(DATA / "sample_proposal.csv")
    prop = prop[prop.role == "proposed"].copy()
    out = []
    for book, d in prop.groupby("book"):
        d = d.copy()
        d["block"] = blocks(d)
        # One candidate per stratum: the page closest to that stratum's median CER,
        # so dev is typical rather than extreme. Strata visited in a fixed order.
        dev_blocks: list[int] = []
        for stratum in ["entity_rich", "low_density", "poor_ocr", "no_entities"]:
            s = d[(d.stratum == stratum) & ~d.block.isin(dev_blocks)]
            if s.empty:
                continue
            pick = s.iloc[(s.cer_nocase - s.cer_nocase.median()).abs().argsort()].iloc[0]
            if (d.block == pick.block).sum() + d.block.isin(dev_blocks).sum() <= DEV_PER_BOOK:
                dev_blocks.append(int(pick.block))
            if d.block.isin(dev_blocks).sum() >= DEV_PER_BOOK:
                break
        d["split"] = d.block.isin(dev_blocks).map({True: "dev", False: "test"})
        out.append(d)
    split = pd.concat(out)
    cols = ["split", "book", "stratum", "PageID", "SequenceOrder", "cer_nocase", "cer_band",
            "n_names", "block", "bhl_url"]
    split = split[cols].sort_values(["split", "book", "SequenceOrder"])
    split.to_csv(DATA / "sample_split.csv", index=False)
    print(split.to_string(index=False))
    print()
    print(pd.crosstab([split.book, split.split], split.stratum, margins=True))


if __name__ == "__main__":
    main()
