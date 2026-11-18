"""Rule baseline (E2): the simplest reasonable extractor, run on the same text
versions as the LLMs, with the same output shape.

  taxon        gnfinder v1.4.0 (Global Names), run locally, no verification.
               Install: GOBIN=<dir> go install github.com/gnames/gnfinder@v1.4.0
               and set GNFINDER=<dir>/gnfinder (or put it on PATH).
  locality     regex: text after "Hab." / "Habitat", and capitalised phrases
               after in / at / near / from, minus a small stoplist.
  date         regex: day-month-year, month-year, and years 1600-1913 (with
               ranges). It cannot tell occurrence dates from citation years;
               that weakness is part of what the baseline measures.
  person       regex: honorific + name (name only), authority abbreviations
               in parentheses such as "(Linn.)", and SURNAME, at the start of
               a citation line ("PFEIFFER, Pro. Zool. Soc.").
  institution  regex: "Mus. <Name>", "<Name> Museum / Society / Herbarium /
               College / University / Institution".

These rules were written from the field definitions in ANNOTATION_GUIDE v0.2
and checked only against dev pages. They are deliberately simple and
documented, not tuned.

Output: a run folder like the LLM runs (condition "RULE"). DEV mentions are
written in the open (dev_mentions.csv); TEST outputs go into the sealed gzip,
because a baseline's output could bias the labeller just like a model's.

Run:  GNFINDER=/path/to/gnfinder python src/baseline_rules.py [--pages all]
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
from datetime import datetime, timezone

import pandas as pd

from common import ROOT, sha256_text
from run_extraction import RESULTS, VERSIONS, Sink, finalize, now, select_pages, text_path

GNFINDER_VERSION = "v1.4.0"

_MONTH = r"(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|June?|July?|Aug(?:ust)?|Sept?(?:ember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\.?"
_YEAR = r"1[6-9]\d\d"
PATTERNS = {
    "date": [
        rf"\b\d{{1,2}}(?:st|nd|rd|th)?\.?\s+(?:of\s+)?{_MONTH},?\s+{_YEAR}\b",
        rf"\b{_MONTH}\s+\d{{1,2}}(?:st|nd|rd|th)?,?\s+{_YEAR}\b",
        rf"\b{_MONTH},?\s+{_YEAR}\b",
        rf"\b{_YEAR}(?:\s*[-–]\s*(?:{_YEAR}|\d\d))?\b",
    ],
    "locality": [
        r"\bHab(?:itat)?\.?\s*[:,]?\s*(?P<v>[A-Z][^.;:?\n]*)",
        r"\b(?:in|at|near|from)\s+(?:the\s+)?(?P<v>[A-Z][a-z]+(?:\s+(?:of\s+|de\s+|la\s+)?[A-Z][a-z]+){0,3})",
    ],
    "person": [
        r"\b(?:Mr|Mrs|Dr|Capt|Prof|Rev|Col|Lieut|Messrs)\.?\s+(?P<v>(?:[A-Z]\.\s*){0,3}[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)",
        r"\((?P<v>(?:Linn|Lam|Pfr|Gmel|Brug|Desh|Sow|Gray|Lath|Temm|Vieill|Gould|Reeve|Linnæus|Lamarck)\.?)\)",
        r"(?m)^(?P<v>[A-Z][A-ZÆÉ]{3,}(?:\s+[A-Z][A-Z]{2,})?)(?=,\s+[A-Z][a-z]*\.)",
    ],
    "institution": [
        r"\bMus\.\s+(?:[A-Z][a-z]+\s*){1,3}",
        r"\b(?:[A-Z][a-z]+\s+){1,3}(?:Museum|Society|Herbarium|College|University|Institution)\b(?:\s+of\s+[A-Z][a-z]+)?",
    ],
}
# Capitalised words that the "in / at / near / from <Name>" rule must not take as places.
LOCALITY_STOP = {"Plate", "Fig", "Figs", "Species", "Mr", "Mrs", "Dr", "The", "This", "That", "It",
                 "These", "Those", "Linnæus", "Linnaeus", "Lamarck", "January", "February",
                 "March", "April", "May", "June", "July", "August", "September", "October",
                 "November", "December", "Mus", "Museum"}


def gnfinder_bin() -> str:
    b = os.environ.get("GNFINDER") or shutil.which("gnfinder")
    if not b:
        raise SystemExit("gnfinder not found: set GNFINDER or put gnfinder v1.4.0 on PATH")
    return b


def find_taxa(path) -> list[dict]:
    out = subprocess.run([gnfinder_bin(), "-f", "compact", str(path)], capture_output=True,
                         text=True, check=True).stdout
    data = json.loads(out.strip().splitlines()[-1])
    rows = []
    for n in data.get("names") or []:
        start, end, verb = n["start"], n["end"], n["verbatim"]
        # gnfinder includes trailing punctuation in `verbatim` ("castus."); drop it from the span.
        stripped = verb.rstrip(" .,;:)")
        rows.append({"field": "taxon", "start": start, "end": start + len(stripped)})
    return rows


def find_regex(text: str) -> list[dict]:
    rows, seen = [], set()
    for field, pats in PATTERNS.items():
        for pat in pats:
            for m in re.finditer(pat, text):
                if "v" in m.re.groupindex and m.group("v"):
                    s, e = m.start("v"), m.end("v")
                else:
                    s, e = m.start(), m.end()
                val = text[s:e].rstrip()
                e = s + len(val)
                if not val:
                    continue
                if field == "locality" and val.split()[0] in LOCALITY_STOP:
                    continue
                key = (field, s, e)
                # one span per field: a later, overlapping pattern does not add a duplicate
                if key in seen or any(f == field and s < e2 and s2 < e for f, s2, e2 in seen):
                    continue
                seen.add(key)
                rows.append({"field": field, "start": s, "end": e})
    return rows


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pages", default="all")
    ap.add_argument("--versions", default=",".join(VERSIONS))
    ap.add_argument("--run-id")
    a = ap.parse_args()

    pages = select_pages(a.pages)
    run_id = a.run_id or f"{datetime.now(timezone.utc):%Y%m%d-%H%M}_rules-gnfinder-{GNFINDER_VERSION}_{a.pages}"
    run_dir = RESULTS / run_id
    run_dir.mkdir(parents=True)
    cfg = {"run_id": run_id, "created_at": now(), "model": f"rules + gnfinder {GNFINDER_VERSION}",
           "condition": "RULE", "gnfinder": {"version": GNFINDER_VERSION, "flags": "-f compact",
                                             "verification": False},
           "patterns": PATTERNS, "locality_stoplist": sorted(LOCALITY_STOP),
           "page_ids": pages.PageID.tolist(), "versions": a.versions.split(",")}
    (run_dir / "config.json").write_text(json.dumps(cfg, indent=2, ensure_ascii=False), encoding="utf-8")

    inputs, sink, meta = [], Sink(run_dir), []
    for p in pages.itertuples():
        for v in a.versions.split(","):
            path = text_path(v, p.PageID)
            text = path.read_text(encoding="utf-8")
            mentions = sorted(find_taxa(path) + find_regex(text), key=lambda m: (m["start"], m["field"]))
            cid = f"{p.PageID}__{v}__RULE"
            inputs.append({"custom_id": cid, "page_id": int(p.PageID), "split": p.split, "book": p.book,
                           "version": v, "condition": "RULE", "input_sha256": sha256_text(text),
                           "source": str(path.relative_to(ROOT))})
            rec = {"custom_id": cid, "page_id": int(p.PageID), "split": p.split, "version": v,
                   "condition": "RULE", "model": cfg["model"], "stop_reason": "end_turn", "usage": {},
                   "cost_usd": 0.0, "parsed": {"mentions": mentions}, "raw": None, "error": None,
                   "received_at": now()}
            sink.write(rec)
            meta.append({k: rec[k] for k in ("page_id", "split", "stop_reason", "usage", "cost_usd", "error")})
    sink.close()
    pd.DataFrame(inputs).to_csv(run_dir / "inputs.csv", index=False)
    finalize(run_dir, meta, cfg["model"], batch=False)


if __name__ == "__main__":
    main()
