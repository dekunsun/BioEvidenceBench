"""本草綱目 case: freeze the dev configuration before an independent test set is chosen and labelled.

    python src/bencao_freeze.py            -> data/bencao/FREEZE_bencao.json (commit it at once)
    python src/bencao_freeze.py --verify   -> lists every frozen file that has changed since

Frozen: the guide, the extraction prompt and schema (inside src/bencao_extract.py), locator and scorer, the
variant table that the folded metrics use, the OCR scripts and their settings, the link-key rule, and the
dev gold with its change log. The dev runs named below are the settings the test runs must repeat.
Rules found on test pages go into the guide and the test gold, never into the prompt, as for the English
books; scores are then reported with all rows and with later-rule rows optional.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "bencao" / "FREEZE_bencao.json"
FILES = ["docs/notes/bencao_guide.md", "src/bencao_extract.py", "src/bencao_variants.py",
         "data/bencao/variant_table.csv", "src/bencao_ocr_claude.py", "src/bencao_ocr_paddle.py",
         "src/bencao_pilot.py", "src/bencao_link_keys.py",
         "gold/gold_mentions_bencao_gloria.csv", "gold/gold_changes_bencao_gloria.csv"]
DEV_RUNS = ["20261124-0900_bencao_extract_claude-opus-5-5",
            "20261124-0901_bencao_extract_claude-opus-5-5_claude_opus",
            "20261124-0902_bencao_extract_claude-opus-5-5_claude_haiku",
            "20261124-0904_bencao_extract_claude-opus-5-5_paddleocr"]
OCR_RUNS = ["20261123-0058_bencao_ocr_claude-haiku-5-5", "20261123-0059_bencao_ocr_claude-opus-5-5",
            "20261123-0547_bencao_ocr_paddleocr"]


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--verify", action="store_true")
    a = ap.parse_args()
    if a.verify:
        f = json.loads(OUT.read_text(encoding="utf-8"))
        changed = [k for k, v in f["files"].items() if sha(ROOT / k) != v]
        print("changed since the freeze:", changed or "nothing")
        sys.exit(1 if changed else 0)
    sys.path.insert(0, str(ROOT / "src"))
    import bencao_extract as be
    from bencao_ocr_paddle import SETTINGS
    runs = {}
    for r in DEV_RUNS:
        c = json.loads((ROOT / "results" / r / "config.json").read_text(encoding="utf-8"))
        runs[r] = {k: c.get(k) for k in ("model", "prompt_version", "effort", "max_tokens", "text")}
    freeze = {
        "frozen_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "code_commit": subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip(),
        "guide_version": "v0.5", "prompt_version": be.PROMPT_VERSION,
        "prompt_sha256": hashlib.sha256((be.SYSTEM + be.RULES + json.dumps(be.SCHEMA, sort_keys=True)).encode()).hexdigest(),
        "dev_pages": be.PAGES, "texts": be.TEXTS, "paddleocr_settings": SETTINGS,
        "dev_extraction_runs": runs, "dev_ocr_runs": OCR_RUNS,
        "primary_metric": "value F1 on ALL_PRIMARY (taxon, person, locality, cited_work), exact forms; "
                          "folded value F1 and names intact (exact and folded) always reported beside it",
        "files": {k: sha(ROOT / k) for k in FILES},
        "approved": "the author, 2026-11-24 (proposed by her: freeze guide, prompt, OCR settings and scorer, "
                    "then prepare an independent test set)"}
    OUT.write_text(json.dumps(freeze, ensure_ascii=False, indent=1), encoding="utf-8")
    print(OUT, len(FILES), "files frozen")


if __name__ == "__main__":
    main()
