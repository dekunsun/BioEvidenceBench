"""Replace the notes of the published release with the corrected model card (Gloria, 2026-11-21:
"你直接改"). Runs on a RunPod pod, where the token is the RunPod secret GITHUB_TOKEN (never printed).

    python rl/release/update_release_notes.py --out <dir>

Correction: the Cuvier name result rests on 10 damaged name words, not 20 (words had been counted
once per answer). Only the notes change; the file, tag and digest stay as published.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[2]
API = "https://api.github.com/repos/dekunsun/BioEvidenceBench/releases/454034654"
SHA = "bfeb5657e7e078d25b1c47c64a8afd2c63c80d5e8bb0594f285d0fafdea16e8c"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    out = Path(ap.parse_args().out)
    out.mkdir(parents=True, exist_ok=True)
    h = {"Authorization": f"Bearer {os.environ['GITHUB_TOKEN']}", "Accept": "application/vnd.github+json"}
    card = (ROOT / "rl" / "release" / "MODEL_CARD_sft_s2.md").read_text(encoding="utf-8")
    assert "on 20 words" not in card and "rests on 10 words" in card
    body = card + (f"\n\n**File**: `sft_s2.tar`, 1,203,578,880 bytes, SHA-256 `{SHA}`.\n\n"
                   "*Notes corrected 2026-11-21: the Cuvier name result rests on 10 damaged name words, not 20.*\n")
    r = requests.patch(API, headers=h, json={"body": body}, timeout=60)
    rel = r.json() if r.ok else {}
    res = {"http": r.status_code, "draft": rel.get("draft"), "tag": rel.get("tag_name"),
           "notes_have_10_words": "rests on 10 words" in rel.get("body", ""),
           "asset_digests": [a.get("digest") for a in rel.get("assets", [])]}
    (out / "update_result.json").write_text(json.dumps(res, indent=1))
    print(res)


if __name__ == "__main__":
    main()
