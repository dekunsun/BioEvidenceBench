"""Freeze the evaluation before any test output is unsealed (PREREGISTRATION, freeze table).

    python src/freeze.py --frozen-run <dev run id> [--frozen-run <dev run id> ...]
        checks that the gold set is complete, then writes FREEZE.json: the code commit,
        the SHA-256 of every gold file and of the code that decides a score, the prompt
        version, and the model settings of the named dev runs (the settings the test runs
        must use). Commit FREEZE.json right away; that commit is the freeze commit.

    python src/freeze.py --ready
        only lists what still stops the freeze; writes nothing.

    python src/freeze.py --verify
        recomputes every hash and lists what has changed since the freeze. unseal.py runs
        this and refuses to open sealed outputs if anything frozen has changed.

It decides nothing about labels and never writes a gold file.
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
FREEZE = ROOT / "FREEZE.json"
GOLD = ["gold/gold_mentions_gloria.csv", "gold/gold_mentions_gloria_test.csv", "gold/gold_links_gloria.csv",
        "gold/gold_links_gloria_names.csv", "gold/gold_changes_gloria.csv", "data/transcription_errata.csv",
        "data/sample_split.csv", "data/sample/manifest.csv", "gold/gold_mentions_friend.csv",
        "gold/agreement_adjudication_gloria.csv"]
OPTIONAL_GOLD = ["gold/annotation_issues_gloria.csv"]      # frozen if it exists
CODE = ["ANNOTATION_GUIDE.md", "PREREGISTRATION.md", "src/prompts.py", "src/score.py", "src/locate.py",
        "src/analysis.py", "src/analyze.py", "src/link_taxa.py", "src/baseline_rules.py",
        "src/run_extraction.py", "src/gemini_backend.py", "src/common.py"]
# settings copied from a dev run's config.json; everything else (pages, caps) may differ
RUN_KEYS = ["provider", "model", "effort", "max_tokens", "mode", "prompt_version", "system_sha256", "versions",
            "conditions", "generation_config", "api", "api_version", "anthropic_sdk", "google_genai_sdk"]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def hashes() -> dict[str, str]:
    files = GOLD + [p for p in OPTIONAL_GOLD if (ROOT / p).exists()] + CODE
    return {p: sha(ROOT / p) for p in files}


def git(*args) -> str:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()


def gold_problems() -> list[str]:
    """Reasons the gold set is not ready. Uses the same loaders the scorers use."""
    sys.path.insert(0, str(ROOT / "src"))
    import pandas as pd
    from check_gold import check
    problems = []
    split = pd.read_csv(ROOT / "data" / "sample_split.csv")
    for path, which in (("gold/gold_mentions_gloria.csv", "dev"), ("gold/gold_mentions_gloria_test.csv", "test")):
        res = check(ROOT / path)
        need = set(split.query("split == @which").PageID)
        if need - set(res.page_id.astype(int)):
            problems.append(f"{path}: no rows for {which} pages {sorted(need - set(res.page_id.astype(int)))}")
        bad = res[~res.status.str.startswith("ok")]
        if len(bad):
            problems.append(f"{path}: {len(bad)} rows fail check_gold.py")
        unclear = res[res.status.str.contains("needs adjudication")]
        if len(unclear):
            problems.append(f"{path}: {len(unclear)} UNCLEAR rows not adjudicated")
    try:
        from link_taxa import load_links
        load_links(ROOT / "gold" / "gold_links_gloria.csv")
    except SystemExit as e:
        problems.append(f"gold_links_gloria.csv: {e}")
    if not (ROOT / "results" / "agreement_independent" / "agreement.csv").exists():
        problems.append("no results/agreement_independent/ yet (src/agreement.py on the second labeller's pages)")
    return problems


def verify() -> list[str]:
    if not FREEZE.exists():
        return ["no FREEZE.json: the evaluation has not been frozen"]
    frozen = json.loads(FREEZE.read_text(encoding="utf-8"))["sha256"]
    now = hashes()
    changed = [f"{p}: changed since the freeze" for p in frozen if now.get(p) != frozen[p]]
    changed += [f"{p}: new file not in the freeze" for p in now if p not in frozen]
    return changed


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--frozen-run", action="append", default=[], help="dev run whose settings are frozen")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--ready", action="store_true", help="list what still stops the freeze; write nothing")
    a = ap.parse_args()
    if a.verify:
        changed = verify()
        print("\n".join(changed) if changed else "Nothing frozen has changed.")
        sys.exit(1 if changed else 0)
    if a.ready:
        problems = gold_problems() + (["uncommitted changes in the working tree"] if git("status", "--porcelain") else [])
        print("Ready to freeze." if not problems else "Still to do before the freeze:\n  " + "\n  ".join(problems))
        sys.exit(1 if problems else 0)
    if FREEZE.exists():
        sys.exit("FREEZE.json exists. A freeze is not redone; changes after it go in the deviations log.")
    if not a.frozen_run:
        sys.exit("Name the dev run(s) whose model settings the test runs will use (--frozen-run).")
    problems = gold_problems()
    if git("status", "--porcelain"):
        problems.append("uncommitted changes in the working tree: commit first")
    if problems:
        sys.exit("Not frozen:\n  " + "\n  ".join(problems))
    sys.path.insert(0, str(ROOT / "src"))
    from prompts import PROMPT_VERSION
    runs = {}
    for r in a.frozen_run:
        cfg = json.loads((ROOT / "results" / r / "config.json").read_text(encoding="utf-8"))
        if cfg.get("prompt_version") != PROMPT_VERSION:
            sys.exit(f"{r} used {cfg.get('prompt_version')}, the code has {PROMPT_VERSION}.")
        runs[r] = {k: cfg[k] for k in RUN_KEYS if k in cfg}
    record = {"frozen_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
              "code_commit": git("rev-parse", "HEAD"), "prompt_version": PROMPT_VERSION,
              "model_settings_from_dev_runs": runs, "sha256": hashes(),
              "note": "Commit this file at once. src/freeze.py --verify lists anything changed since."}
    FREEZE.write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"FREEZE.json written ({len(record['sha256'])} files). Commit it now; that commit is the freeze.")


if __name__ == "__main__":
    main()
