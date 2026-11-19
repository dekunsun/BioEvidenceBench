"""Copy Gloria's decisions from the short names sheet to every mention (no judgement here).

    python src/expand_links.py            # gold/gold_links_gloria_names.csv -> gold/gold_links_gloria.csv

Gloria fills one row per distinct printed name in `gold/gold_links_gloria_names.csv`
(4 columns are required: printed_rank, resolution_status, accepted_usage_key, evidence_source;
see ANNOTATION_GUIDE section 3). This script copies each name's row to every mention of that
name in `gold/gold_links_gloria.csv`, the file `src/link_taxa.py` scores. It only copies: a name
the sheet leaves empty stays empty, and the script reports it.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DECISION_COLS = ["printed_rank", "resolution_status", "match_method", "matched_rank", "taxonomic_status",
                 "matched_usage_key", "accepted_usage_key", "evidence_source", "notes"]


def name_of(text: str) -> str:
    return text.replace("-\n", "").replace("\n", " ")


def expand(names_path: Path, links_path: Path) -> pd.DataFrame:
    names = pd.read_csv(names_path, dtype=str, keep_default_na=False).set_index("name")
    links = pd.read_csv(links_path, dtype=str, keep_default_na=False)
    missing = []
    for i, r in links.iterrows():
        n = name_of(r["text"])
        if n not in names.index:
            missing.append(n)
            continue
        for c in DECISION_COLS:
            if c in names.columns:
                links.at[i, c] = names.at[n, c]
    if missing:
        sys.exit(f"Names not in the sheet: {sorted(set(missing))}")
    empty = sorted({name_of(t) for t, s in zip(links.text, links.resolution_status) if not s.strip()})
    if empty:
        print(f"{len(empty)} names still have no resolution_status: {empty}")
    links.to_csv(links_path, index=False)
    return links


if __name__ == "__main__":
    expand(ROOT / "gold" / "gold_links_gloria_names.csv", ROOT / "gold" / "gold_links_gloria.csv")
