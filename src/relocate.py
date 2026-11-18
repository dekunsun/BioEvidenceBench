"""Re-run locate.py on a finished run after the locating rules change.

Rewrites results/<run_id>/dev_mentions.csv from dev_outputs.jsonl. Test
mentions are re-located only if the run has been unsealed (UNSEALED.md and
test_outputs.jsonl exist); the sealed .gz is never read here. Model output is
not changed; only how it is matched to the source text.

Run:  python src/relocate.py <run_id> [<run_id> ...]
"""
from __future__ import annotations

import json
import sys

import pandas as pd

from common import ROOT
from locate import locate_all

RESULTS = ROOT / "results"


def relocate(run_dir, outputs_name: str, mentions_name: str) -> pd.DataFrame | None:
    path = run_dir / outputs_name
    if not path.exists():
        return None
    inputs = pd.read_csv(run_dir / "inputs.csv").set_index("custom_id")
    rows = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            rec = json.loads(line)
            if not rec.get("parsed"):
                continue
            src = (ROOT / inputs.loc[rec["custom_id"], "source"]).read_text(encoding="utf-8")
            for i, m in enumerate(locate_all(src, rec["condition"], rec["parsed"].get("mentions", []))):
                rows.append({"page_id": rec["page_id"], "version": rec["version"],
                             "condition": rec["condition"], "i": i, **m})
    df = pd.DataFrame(rows)
    df.to_csv(run_dir / mentions_name, index=False)
    return df


if __name__ == "__main__":
    for run_id in sys.argv[1:]:
        run_dir = RESULTS / run_id
        dev = relocate(run_dir, "dev_outputs.jsonl", "dev_mentions.csv")
        print(run_id)
        if dev is not None:
            print(pd.crosstab([dev.version, dev.condition], dev.status).to_string())
        if (run_dir / "UNSEALED.md").exists():
            relocate(run_dir, "test_outputs.jsonl", "test_mentions.csv")
            print("  test mentions re-located (run is unsealed)")
