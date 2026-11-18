"""Open the sealed test outputs of a run, but only after the gold set is done.

Checks, in order:
  1. gold/gold_mentions_<labeller>.csv exists and has at least one row for
     every TEST page (a page with nothing to label has a `none` row);
  2. check_gold.py finds no offset problems in it;
  3. the sealed file's SHA-256 matches the one recorded in SEALED.md at run time.
Only then it writes results/<run_id>/test_outputs.jsonl and test_mentions.csv.

Run:  python src/unseal.py <run_id> --labeller gloria
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import re
import sys

import pandas as pd

from check_gold import check
from common import DATA, ROOT
from locate import locate_all

RESULTS = ROOT / "results"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("run_id")
    ap.add_argument("--labeller", required=True)
    a = ap.parse_args()
    run_dir = RESULTS / a.run_id

    gold_path = ROOT / "gold" / f"gold_mentions_{a.labeller}.csv"
    if not gold_path.exists():
        sys.exit(f"No gold file {gold_path}. Label the test pages first.")
    test_ids = set(pd.read_csv(DATA / "sample_split.csv").query("split == 'test'").PageID)
    res = check(gold_path)
    missing = test_ids - set(res.page_id.astype(int))
    if missing:
        sys.exit(f"Gold labels missing for test pages {sorted(missing)}. Still sealed.")
    bad = res[~res.status.str.startswith("ok")]
    if len(bad):
        sys.exit(f"{len(bad)} gold rows fail check_gold.py. Fix them first. Still sealed.")

    sealed = run_dir / "sealed" / "test_outputs.jsonl.gz"
    want = re.search(r"SHA-256: `([0-9a-f]{64})`", (run_dir / "SEALED.md").read_text()).group(1)
    got = hashlib.sha256(sealed.read_bytes()).hexdigest()
    if got != want:
        sys.exit(f"Sealed file hash {got} does not match SEALED.md {want}. Do not use this run.")

    inputs = pd.read_csv(run_dir / "inputs.csv").set_index("custom_id")
    rows = []
    with gzip.open(sealed, "rt", encoding="utf-8") as f, \
            open(run_dir / "test_outputs.jsonl", "w", encoding="utf-8") as out:
        for line in f:
            out.write(line)
            rec = json.loads(line)
            if not rec.get("parsed"):
                continue
            src = (ROOT / inputs.loc[rec["custom_id"], "source"]).read_text(encoding="utf-8")
            for i, m in enumerate(locate_all(src, rec["condition"], rec["parsed"].get("mentions", []))):
                rows.append({"page_id": rec["page_id"], "version": rec["version"],
                             "condition": rec["condition"], "i": i, **m})
    pd.DataFrame(rows).to_csv(run_dir / "test_mentions.csv", index=False)
    (run_dir / "UNSEALED.md").write_text(
        f"Unsealed after gold file `{gold_path.name}` passed checks for all {len(test_ids)} test pages.\n"
        f"Hash verified: `{got}`.\n", encoding="utf-8")
    print(f"Unsealed {run_dir.name}: {len(rows)} test mentions located.")


if __name__ == "__main__":
    main()
