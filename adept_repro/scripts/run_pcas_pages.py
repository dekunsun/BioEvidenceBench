"""
Try ADEPT's description detection and trait extraction on a few PCAS botany pages
(Proc. Calif. Acad. Sci. 3rd ser. Botany v.1, BHL item 48989; Eastwood 1898,
"Studies in the herbarium and the field No. 2"), using BHL S3 OCR.

No gold labels are made. This is a qualitative look at what ADEPT does on an
external domain page, for BioEvidenceBench's PCAS case study.

ADEPT's BHL path is taxon-driven: you give a binomial, it finds pages, and then
BHLDetectDescriptions(taxon) keeps paragraphs whose TaxoNERD taxon entities all
match that name (or synonyms) and that the description classifier scores >= 0.9.
Here we have pages, not a taxon, so for each page we:
  1. run ADEPT's preprocess + TaxoNERD (the same `nlp` object ADEPT uses) and list
     well-formed binomial taxon entities on the page;
  2. for each such binomial, run ADEPT's BHLDetectDescriptions(binomial) on the page
     unchanged (this is exactly what BHLDescriptionTask does per page);
  3. send every detected description through ADEPT's trait Pipeline and the
     angiosperm field template, as DescriptionsTask does;
  4. as a diagnostic, also score every paragraph (> 50 tokens) with the description
     classifier, whatever its taxon, so we can see what the 0.9 threshold drops.

Usage (ADEPT venv, OCR already in the archive via fetch_s3_ocr.py):
  python adept_repro/scripts/run_pcas_pages.py --pages 13793662 13793669 13793689 13793690 13793698 \
      --out adept_repro/outputs/pcas
"""
import argparse
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import yaml

import adept
from adept.bhl.descriptions import BHLDetectDescriptions
from adept.config import BHL_OCR_ARCHIVE_PATH, TaxonomicGroup, fields_template
from adept.utils.helpers import is_binomial

ADEPT_ROOT = Path(adept.__file__).resolve().parent.parent


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pages", nargs="+", type=int, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    from adept.pipeline import Pipeline
    pipeline = Pipeline()
    group = TaxonomicGroup.angiosperm
    field_mappings = yaml.full_load(fields_template.open())[group]

    nlp = BHLDetectDescriptions.nlp
    preprocess = BHLDetectDescriptions.preprocess
    classifier = BHLDetectDescriptions.classifier

    para_rows, desc_rows, records = [], [], []
    for page_id in args.pages:
        path = next(BHL_OCR_ARCHIVE_PATH.glob(f"*-{page_id:08d}-*.txt"))
        text = path.read_text()
        doc = nlp(preprocess(text))

        # 4. diagnostic paragraph scores
        for i, para in enumerate(BHLDetectDescriptions._doc_to_paragraphs(doc)):
            if len(para) <= BHLDetectDescriptions.MINIMUM_WORD_COUNT:
                continue
            score = classifier.nlp(para.text).cats["description"]
            para_rows.append({"page_id": page_id, "para_idx": i, "n_tokens": len(para),
                              "score_description": round(score, 4), "is_desc_at_0.9": score >= 0.9,
                              "taxa_in_para": "; ".join(e.text for e in para.ents if e.label_ == "LIVB"),
                              "snippet": para.text[:160].replace("\n", " ")})

        # 1-3. ADEPT's own detection, per binomial found on the page
        binomials = sorted({" ".join(e.text.split()[:2]) for e in doc.ents
                            if e.label_ == "LIVB" and e.text[0].isupper() and is_binomial(" ".join(e.text.split()[:2]))})
        for taxon in binomials:
            result = BHLDetectDescriptions(taxon)(text)
            if not result:
                continue
            descriptions, matched = result
            for d in descriptions:
                fields = pipeline(d, group)
                rec = fields.to_mapped_dict(field_mappings)
                rec = {k: v for k, v in rec.items() if v not in (None, "", [], {})}
                desc_rows.append({"page_id": page_id, "query_taxon": taxon, "matched_names": "; ".join(matched),
                                  "n_chars": len(d), "n_trait_fields": len(rec),
                                  "snippet": d[:200].replace("\n", " ")})
                records.append({"page_id": page_id, "query_taxon": taxon, "description": d, "traits": rec})

    meta = {"run_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "adept_commit": subprocess.run(["git", "-C", str(ADEPT_ROOT), "rev-parse", "HEAD"],
                                           capture_output=True, text=True).stdout.strip(),
            "bhl_item": 48989, "pages": args.pages, "ocr_source": "BHL open-data S3 (legacy BHL OCR)",
            "rights": "item.CopyrightStatus = NOT_IN_COPYRIGHT (BHL item table, S3 export of 2026-06-06)",
            "gold_labels": "none"}
    pd.DataFrame(para_rows).to_csv(args.out / "paragraph_scores.csv", index=False)
    pd.DataFrame(desc_rows).to_csv(args.out / "detected_descriptions.csv", index=False)
    (args.out / "traits.json").write_text(json.dumps({"meta": meta, "records": records}, indent=2, default=str))
    print(json.dumps(meta, indent=2))
    print(pd.DataFrame(desc_rows)[["page_id", "query_taxon", "n_chars", "n_trait_fields"]].to_string()
          if desc_rows else "no descriptions detected")


if __name__ == "__main__":
    main()
