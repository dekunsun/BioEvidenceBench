"""
Copy the small, human-readable outputs of one ADEPT CLI run into
adept_repro/outputs/<name>/ together with a run.json (command, ADEPT commit,
timestamps, input hashes, and a page funnel: name hits -> pages passing the
cheap trait-term filter -> pages with detected descriptions -> trait records).

ADEPT writes everything under vendor/ADEPT/adept/data/processing/ (git-ignored
upstream), so without this step nothing of the run would be kept.

Usage (ADEPT venv):
  python adept_repro/scripts/export_run.py --name traits_leersia_hexandra --taxon "Leersia hexandra" \
     --command 'adept traits --taxa "Leersia hexandra" --group angiosperm' \
     --log adept_repro/outputs/logs/traits_leersia_default.log \
     --xlsx vendor/.../output/bhl/angiosperm-leersia-hexandra.bhl.traits.xlsx
"""
import argparse
import hashlib
import json
import re
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import yaml

import adept
from adept.config import BHL_NAMES_INDEX_PATH, INTERMEDIATE_DATA_DIR

ADEPT_ROOT = Path(adept.__file__).resolve().parent.parent
OUT_ROOT = Path(__file__).resolve().parent.parent / "outputs"


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--name", required=True)
    ap.add_argument("--taxon", required=True)
    ap.add_argument("--command", required=True)
    ap.add_argument("--log", type=Path, required=True)
    ap.add_argument("--xlsx", type=Path)
    ap.add_argument("--csv", type=Path, help="descriptions CSV written by `adept descriptions`")
    args = ap.parse_args()
    out = OUT_ROOT / args.name
    out.mkdir(parents=True, exist_ok=True)

    taxon = args.taxon
    search_yaml = INTERMEDIATE_DATA_DIR / "bhl/search" / f"{taxon}.en.yaml"
    desc_yaml = INTERMEDIATE_DATA_DIR / "bhl/description" / f"{taxon}.bhl.yaml"
    eco_yaml = INTERMEDIATE_DATA_DIR / "ecoflora" / f"{taxon}.yaml"

    names = pd.read_parquet(BHL_NAMES_INDEX_PATH)
    from adept.tasks.description.bhl.search import BHLSearchTask
    hits = BHLSearchTask(taxon=taxon).search()
    passed = yaml.full_load(search_yaml.open()) or {}
    bhl_desc = yaml.full_load(desc_yaml.open()) or []
    log = args.log.read_text(errors="replace")

    funnel = {
        "bhl_name_occurrences": int(len(hits)),
        "bhl_pages_with_name_or_synonym": int(hits.PageID.nunique()),
        "bhl_pages_passing_trait_term_filter(min_terms=15,min_chars=2500)": len(passed),
        "bhl_pages_with_detected_description": len(bhl_desc),
        "bhl_description_paragraphs": sum(d["text"].count("\n\n") + 1 for d in bhl_desc),
    }
    sources = {
        "ecoflora_description_found": bool(eco_yaml.exists() and (yaml.full_load(eco_yaml.open()) or [{}])[0].get("text")),
        "efloras_http_403_errors_in_log": len(re.findall(r"403 Client Error: Forbidden for url: http://efloras", log)),
        "efloras_no_results_warnings": len(re.findall(r"No results for .* in efloras", log)),
        "luigi_summary": re.findall(r"This progress looks .*", log),
    }

    copied = {}
    if args.xlsx:
        for sheet, df in pd.read_excel(args.xlsx, sheet_name=None).items():
            df.dropna(axis=1, how="all").to_csv(out / f"traits_{sheet}.csv", index=False)
            copied[f"traits_{sheet}.csv"] = f"sheet '{sheet}' of {args.xlsx.name} (empty columns dropped)"
    if args.csv:
        shutil.copy(args.csv, out / "descriptions.csv")
        copied["descriptions.csv"] = str(args.csv.resolve().relative_to(ADEPT_ROOT))
        df = pd.read_csv(args.csv)
        sources["descriptions_per_source"] = df.source.value_counts().to_dict()
    shutil.copy(desc_yaml, out / "bhl_descriptions.yaml")
    copied["bhl_descriptions.yaml"] = "BHLDescriptionTask output (page id -> detected description text)"

    # Keep the log without DEBUG/INFO noise
    keep = [ln for ln in log.splitlines()
            if not ln.startswith(("DEBUG", "INFO")) and "warnings.warn" not in ln and "Warning" not in ln]
    (out / "log_filtered.txt").write_text("\n".join(keep) + "\n")

    start = args.log.with_suffix(".start")
    run = {
        "command": args.command,
        "run_started_utc": start.read_text().strip() if start.exists() else None,
        "exported_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "adept_commit": subprocess.run(["git", "-C", str(ADEPT_ROOT), "rev-parse", "HEAD"],
                                       capture_output=True, text=True).stdout.strip(),
        "adept_local_changes": "patches/0001-add-missing-adept-bhl-ocr-stub.patch (stub module; no logic change)",
        "text_source": "BHL legacy OCR from s3://bhl-open-data/ocr/ copied into ADEPT's local OCR archive "
                       "(scripts/fetch_s3_ocr.py); no BHL API calls succeeded",
        "names_index": {"path": "adept/.cache/bhl-names.parquet (subset for queried taxa; see build_bhl_names_index.py)",
                        "rows": int(len(names)), "sha256": sha256(BHL_NAMES_INDEX_PATH)},
        "funnel": funnel,
        "sources": sources,
        "files": copied,
    }
    (out / "run.json").write_text(json.dumps(run, indent=2))
    print(json.dumps(run, indent=2))


if __name__ == "__main__":
    main()
