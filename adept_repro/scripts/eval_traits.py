"""
Re-run ADEPT's trait-extraction evaluation (notebooks/adept_evaluation.ipynb)
on the bundled reference/prediction CSVs, then compare with the bundled results.

The notebook's own path cells point at the author's laptop and an .xlsx we do not
have, so we load the two CSVs from notebooks/adept_evaluation/data/ (their SHA-256
match notebooks/adept_evaluation/results/evaluation_settings.json) and execute the
notebook's validation, matching and scoring cells unchanged.

Usage (ADEPT venv): python adept_repro/scripts/eval_traits.py --out adept_repro/outputs/traits_eval
"""
import argparse
import json
from pathlib import Path

import pandas as pd

import adept

ADEPT_ROOT = Path(adept.__file__).resolve().parent.parent
BUNDLE = ADEPT_ROOT / "notebooks/adept_evaluation"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    nb = json.loads((ADEPT_ROOT / "notebooks/adept_evaluation.ipynb").read_text())
    cells = ["".join(c["source"]) for c in nb["cells"] if c["cell_type"] == "code"]

    ns = {}
    exec(cells[0], ns)  # imports
    ns.update(
        REFERENCE_PATH=BUNDLE / "data/adept_trait_extraction_reference.csv",
        PREDICTIONS_PATH=BUNDLE / "data/adept_trait_extraction_predictions.csv",
        METADATA_COLUMNS={"taxon", "source", "source_id", "matched_name", "key"},
        EXCLUDED_CELLS=set(),
        OUTPUT_DIR=args.out,
    )
    ns["ref_df"] = pd.read_csv(ns["REFERENCE_PATH"])
    ns["pred_df"] = pd.read_csv(ns["PREDICTIONS_PATH"])
    # cells[1..4] = author's paths, xlsx loading, key building (keys already in the CSVs)
    for code in cells[5:]:
        exec(code, ns)

    ours = pd.read_csv(args.out / "overall_metrics.csv")
    theirs = pd.read_csv(BUNDLE / "results/overall_metrics.csv")
    ours_f = pd.read_csv(args.out / "per_field_metrics.csv")
    theirs_f = pd.read_csv(BUNDLE / "results/per_field_metrics.csv")
    report = {
        "overall_ours": ours.to_dict("records"),
        "overall_published": theirs.to_dict("records"),
        "overall_identical": ours.equals(theirs),
        "per_field_identical": ours_f.equals(theirs_f),
    }
    (args.out / "comparison.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
