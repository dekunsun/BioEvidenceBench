"""Copy Gloria's decisions from the short names sheet to every mention (no judgement here).

    python src/expand_links.py
        reads  gold/gold_links_gloria_names.xlsx (or .csv)  one row per distinct printed name
        writes gold/gold_links_gloria.csv                    one row per mention, scored by link_taxa.py
               gold/gold_links_gloria_key_lookup.csv         audit trail of the name -> key step

Gloria writes the **accepted name** she settled on (e.g. `Alauda arvensis`, from Avibase).
She does not copy numbers: since 2026 the GBIF website shows new taxon codes (e.g.
gbif.org/taxon/BFFT), while the API that src/link_taxa.py scores against still uses the
numeric backbone keys (Alauda arvensis = 8077224). This script turns her name into that key
with an exact, rank-checked lookup in the same API. It decides nothing: a name that is not an
exact, accepted match at the expected rank is NOT filled in but listed for her to look at.
"""
from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
GBIF_MATCH = "https://api.gbif.org/v1/species/match"
DECISION_COLS = ["printed_rank", "resolution_status", "match_method", "matched_rank", "taxonomic_status",
                 "matched_usage_key", "accepted_usage_key", "accepted_name", "evidence_source", "notes"]


def name_of(text: str) -> str:
    return text.replace("-\n", "").replace("\n", " ")


def gbif_exact(name: str, fetch=None) -> dict:
    fetch = fetch or (lambda n: requests.get(GBIF_MATCH, params={"name": n, "strict": "true"}, timeout=30,
                                             headers={"User-Agent": "bioevidencebench-linking-eval"}).json())
    return fetch(name)


def key_for(accepted_name: str, expected_rank: str, fetch=None) -> tuple[str, str]:
    """(key, problem). The key is filled only for an EXACT match on an ACCEPTED record whose
    canonical name equals the given name and whose rank is the expected one."""
    r = gbif_exact(accepted_name, fetch)
    if r.get("matchType") != "EXACT":
        return "", f"no exact match (matchType {r.get('matchType')})"
    if (r.get("canonicalName") or "").lower() != accepted_name.strip().lower():
        return "", f"matched another name: {r.get('canonicalName')}"
    if (r.get("rank") or "").lower() != expected_rank.lower():
        return "", f"rank is {r.get('rank')}, expected {expected_rank}"
    if r.get("status") != "ACCEPTED":
        return "", f"status {r.get('status')} in the GBIF backbone (accepted there: key {r.get('acceptedUsageKey')})"
    return str(r["usageKey"]), ""


def read_names(gold: Path) -> pd.DataFrame:
    x, c = gold / "gold_links_gloria_names.xlsx", gold / "gold_links_gloria_names.csv"
    d = pd.read_excel(x, sheet_name="names", dtype=str) if x.exists() else pd.read_csv(c, dtype=str)
    return d.fillna("").apply(lambda col: col.str.strip()).set_index("name")


def expand(names: pd.DataFrame, links_path: Path, lookup_path: Path, fetch=None) -> pd.DataFrame:
    log, problems = [], []
    for n, r in names.iterrows():
        status, acc = r.get("resolution_status", ""), r.get("accepted_name", "")
        if status in ("resolved", "partial") and acc and not r.get("accepted_usage_key", ""):
            rank = r.get("printed_rank", "") if status == "resolved" else "genus"
            key, problem = key_for(acc, rank, fetch)
            names.at[n, "accepted_usage_key"] = key
            log.append({"name": n, "accepted_name": acc, "expected_rank": rank, "gbif_key": key,
                        "problem": problem, "looked_up_at": datetime.now(timezone.utc).isoformat(timespec="seconds")})
            if problem:
                problems.append(f"{n} -> {acc}: {problem}")
        elif status in ("resolved", "partial") and not acc and not r.get("accepted_usage_key", ""):
            problems.append(f"{n}: {status} but no accepted_name")
    links = pd.read_csv(links_path, dtype=str, keep_default_na=False)
    missing = sorted({name_of(t) for t in links.text} - set(names.index))
    if missing:
        sys.exit(f"Names not in the sheet: {missing}")
    for c in DECISION_COLS:
        if c not in links.columns:
            links[c] = ""
    for i, r in links.iterrows():
        for c in DECISION_COLS:
            if c in names.columns:
                links.at[i, c] = names.at[name_of(r["text"]), c]
    links.to_csv(links_path, index=False)
    if log:
        pd.DataFrame(log).to_csv(lookup_path, index=False)
    empty = sorted({name_of(t) for t, s in zip(links.text, links.resolution_status) if not s})
    if empty:
        print(f"{len(empty)} names still have no resolution_status: {empty}")
    if problems:
        print("Names to look at again (key NOT filled):\n  " + "\n  ".join(problems))
    return links


if __name__ == "__main__":
    g = ROOT / "gold"
    expand(read_names(g), g / "gold_links_gloria.csv", g / "gold_links_gloria_key_lookup.csv")
