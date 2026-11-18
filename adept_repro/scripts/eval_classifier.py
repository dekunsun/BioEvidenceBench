"""
Reproduce the ADEPT description-classifier evaluation.

What NHM published:
  * Hugging Face meta.json "performance" block for benhartley/en_description_classifier
    (spaCy `evaluate` output; positive class "description" P=0.9304, R=0.8963).
  * BHL Day 2026 slides: 151 found, 13 missed, 14 false positives, 1,014 correctly rejected.

What this script does (no network calls except the model download done by ADEPT itself):
  1. Loads the test split shipped in the ADEPT repo (train/classifier/corpus/test.spacy).
  2. Checks it equals a re-split of adept/data/assets/train-classifier.csv with the
     parameters in train/classifier/scripts/convert.py (test_size=0.2, random_state=0,
     stratify on is_desc). This tells us whether the shipped split is the one the
     training script would produce.
  3. Runs the pretrained model (ADEPT's BHLClassifier, pinned HF revision) and reports
     confusion matrices at the threshold ADEPT uses at run time (0.9) and at 0.5.
  4. Checks train/test leakage (exact duplicate texts across splits).

Note: the training command in train/classifier/project.yml passes the TEST split as
`--paths.dev`, so spaCy selected `model-best` on the same data it is scored on.

Usage (inside the ADEPT venv):
    python adept_repro/scripts/eval_classifier.py --out adept_repro/outputs/classifier_eval
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
from sklearn.model_selection import train_test_split
from spacy.tokens import DocBin

import adept
from adept.bhl.classifier import BHLClassifier

ADEPT_ROOT = Path(adept.__file__).resolve().parent.parent
PUBLISHED_SLIDES = {"tp": 151, "fn": 13, "fp": 14, "tn": 1014}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def confusion(y_true, scores, threshold):
    tp = fp = fn = tn = 0
    for y, s in zip(y_true, scores):
        pred = s >= threshold
        if y and pred:
            tp += 1
        elif y and not pred:
            fn += 1
        elif not y and pred:
            fp += 1
        else:
            tn += 1
    p = tp / (tp + fp) if tp + fp else float("nan")
    r = tp / (tp + fn) if tp + fn else float("nan")
    f = 2 * p * r / (p + r) if p + r else float("nan")
    return {"threshold": threshold, "tp": tp, "fn": fn, "fp": fp, "tn": tn,
            "precision": round(p, 4), "recall": round(r, 4), "f1": round(f, 4),
            "specificity": round(tn / (tn + fp), 4)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    test_path = ADEPT_ROOT / "train/classifier/corpus/test.spacy"
    train_path = ADEPT_ROOT / "train/classifier/corpus/train.spacy"
    csv_path = ADEPT_ROOT / "adept/data/assets/train-classifier.csv"

    blank = spacy.blank("en")
    test_docs = list(DocBin().from_disk(test_path).get_docs(blank.vocab))
    train_docs = list(DocBin().from_disk(train_path).get_docs(blank.vocab))
    test_texts = [d.text for d in test_docs]
    y_true = [int(d.cats["description"]) for d in test_docs]

    # 2. Does the shipped split equal the scripted split?
    df = pd.read_csv(csv_path)
    _, resplit = train_test_split(df, test_size=0.2, random_state=0, stratify=df.is_desc)
    split_check = {
        "csv_rows": len(df),
        "csv_positives": int(df.is_desc.sum()),
        "shipped_test_docs": len(test_docs),
        "shipped_train_docs": len(train_docs),
        "resplit_test_rows": len(resplit),
        "resplit_equals_shipped_in_order": resplit.text.tolist() == test_texts,
        "resplit_equals_shipped_as_set": set(resplit.text) == set(test_texts),
    }

    # 4. Leakage: exact duplicate texts in both train and test
    train_set = {d.text for d in train_docs}
    dup = [t for t in test_texts if t in train_set]
    split_check["test_texts_also_in_train"] = len(dup)
    split_check["duplicate_texts_within_csv"] = int(df.text.duplicated().sum())

    # 3. Score with the pretrained model, through ADEPT's own loader
    clf = BHLClassifier()
    scores = [doc.cats["description"] for doc in clf.nlp.pipe(test_texts, batch_size=64)]

    results = {
        "run_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "adept_commit": subprocess.run(["git", "-C", str(ADEPT_ROOT), "rev-parse", "HEAD"],
                                       capture_output=True, text=True).stdout.strip(),
        "model": {"repo": "benhartley/en_description_classifier (code says Benscott/, HF redirects)",
                  "revision": "d009096cdbfaf67526bb5187e7a980c1a765d984",
                  "meta_name": clf.nlp.meta.get("name"), "meta_version": clf.nlp.meta.get("version"),
                  "trained_with_spacy": clf.nlp.meta.get("spacy_version"),
                  "run_with_spacy": spacy.__version__},
        "inputs": {"test.spacy_sha256": sha256(test_path), "train-classifier.csv_sha256": sha256(csv_path)},
        "split_check": split_check,
        "adept_runtime_threshold": BHLClassifier.threshold,
        "confusion_at_0.9": confusion(y_true, scores, 0.9),
        "confusion_at_0.5": confusion(y_true, scores, 0.5),
        "published_slides": PUBLISHED_SLIDES,
        "published_hf_meta_description": {"p": 0.9303797468, "r": 0.8963414634, "f": 0.9130434783},
    }
    # Threshold sweep: does any threshold give the slide numbers?
    sweep = [confusion(y_true, scores, t / 100) for t in range(5, 100, 5)]
    results["slides_match_thresholds"] = [
        c["threshold"] for c in (confusion(y_true, scores, t / 1000) for t in range(1, 1000))
        if (c["tp"], c["fn"], c["fp"], c["tn"]) == tuple(PUBLISHED_SLIDES.values())]

    (args.out / "summary.json").write_text(json.dumps(results, indent=2))
    pd.DataFrame(sweep).to_csv(args.out / "threshold_sweep.csv", index=False)
    pd.DataFrame({"text_sha1": [hashlib.sha1(t.encode()).hexdigest() for t in test_texts],
                  "gold_is_desc": y_true, "score_description": [round(s, 6) for s in scores]}
                 ).to_csv(args.out / "test_scores.csv", index=False)
    json.dump(results, sys.stdout, indent=2)


if __name__ == "__main__":
    main()
