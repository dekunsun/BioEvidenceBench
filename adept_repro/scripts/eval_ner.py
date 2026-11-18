"""
Reproduce the published metrics of ADEPT's measurement/numeric NER model
(benhartley/en_adept_ner_trf, pinned revision 857dba1).

Despite the README calling it a "taxonomic named-entity recognition model", its
labels are MEASUREMENT, NUMERIC_CADJ, DIMENSION and CARDINAL. Taxon names in
ADEPT are found by the third-party TaxoNERD model (en_ner_eco_biobert).

Published (HF model card / meta.json "performance"): ents P=0.9736, R=0.9758,
F=0.9747, plus per-type P/R/F. The card does not say which split.

This script:
  1. Re-splits adept/data/assets/train-numeric.json with train/ner/scripts/convert.py
     parameters (70/15/15, random_state=0, stratified on label) and checks the result
     equals the shipped train/ner/corpus/*.spacy files.
  2. Scores the model on the shipped test and val splits with spaCy's own scorer
     (the same scorer `spacy evaluate` uses).
  3. Checks for exact duplicate sentences across splits.

Usage (ADEPT venv): python adept_repro/scripts/eval_ner.py --out adept_repro/outputs/ner_eval
"""
import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import spacy
from huggingface_hub import snapshot_download
from sklearn.model_selection import train_test_split
from spacy.tokens import DocBin
from spacy.training import Example

import adept
import adept.components.registry  # noqa: F401  registers semicolon_sentencizer etc. (what --code components.py does)
from adept.config import MODEL_DIR

ADEPT_ROOT = Path(adept.__file__).resolve().parent.parent
REVISION = "857dba16758cc25e50dfd7a9d42795f4747f6394"
PUBLISHED = {"ents_p": 0.9736247174, "ents_r": 0.9758308157, "ents_f": 0.9747265183}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    # Same call as adept/pipeline.py (re-fetches shared files if the classifier
    # snapshot overwrote them; both models share one local_dir upstream).
    model_dir = snapshot_download(repo_id="Benscott/en_adept_ner_trf", local_dir=MODEL_DIR, revision=REVISION)
    nlp = spacy.load(model_dir)
    assert nlp.meta["name"] == "adept_ner_trf", nlp.meta["name"]

    corpus = ADEPT_ROOT / "train/ner/corpus"
    blank = spacy.blank("en")
    splits = {s: list(DocBin().from_disk(corpus / f"{s}_numeric.spacy").get_docs(blank.vocab))
              for s in ["train", "val", "test"]}

    # 1. re-split check
    df = pd.read_json(ADEPT_ROOT / "adept/data/assets/train-numeric.json")
    df.columns = ["sent", "entities"]
    df["label"] = df["entities"].apply(
        lambda e: (lambda ls: next(iter(ls)) if len(ls) == 1 else "MULTI")({x[2] for x in e["entities"]}))
    tr, te = train_test_split(df, test_size=0.3, random_state=0, stratify=df[["label"]])
    te, va = train_test_split(te, test_size=0.5, random_state=0, stratify=te[["label"]])
    split_check = {"json_rows": len(df), "label_counts": df.label.value_counts().to_dict()}
    for name, part in [("train", tr), ("val", va), ("test", te)]:
        split_check[f"{name}_docs"] = len(splits[name])
        split_check[f"{name}_resplit_equal"] = part.sent.tolist() == [d.text for d in splits[name]]
    texts = {s: {d.text for d in docs} for s, docs in splits.items()}
    split_check["test_in_train"] = len(texts["test"] & texts["train"])
    split_check["val_in_train"] = len(texts["val"] & texts["train"])

    # 2. score
    scores = {}
    for s in ["test", "val"]:
        examples = [Example(nlp.make_doc(d.text), d) for d in splits[s]]
        sc = nlp.evaluate(examples)
        scores[s] = {"ents_p": sc["ents_p"], "ents_r": sc["ents_r"], "ents_f": sc["ents_f"],
                     "ents_per_type": sc["ents_per_type"],
                     "n_docs": len(examples), "n_gold_ents": sum(len(d.ents) for d in splits[s])}

    out = {
        "run_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "adept_commit": subprocess.run(["git", "-C", str(ADEPT_ROOT), "rev-parse", "HEAD"],
                                       capture_output=True, text=True).stdout.strip(),
        "model": {"repo": "benhartley/en_adept_ner_trf", "revision": REVISION,
                  "pipeline": nlp.pipe_names, "labels": list(nlp.get_pipe("ner").labels),
                  "trained_with_spacy": nlp.meta.get("spacy_version"), "run_with_spacy": spacy.__version__},
        "inputs_sha256": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(corpus.glob("*.spacy"))},
        "split_check": split_check,
        "scores": scores,
        "published": PUBLISHED,
    }
    (args.out / "summary.json").write_text(json.dumps(out, indent=2))
    json.dump(out, sys.stdout, indent=2)


if __name__ == "__main__":
    main()
