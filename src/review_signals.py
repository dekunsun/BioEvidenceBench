"""Exploratory (DEVIATIONS.md): which cheap signal tells a reviewer where the errors are?

    python src/review_signals.py

Unit: one Opus G1 prediction on a test page, on every text version that was run (the frozen
test run's expert / modern / legacy texts and the 21 OCR-ladder versions). A prediction is an
ERROR when it is not a value-level true positive (a misread value, a value with no gold
mention, or one that cannot be placed). For each signal, a prediction is FLAGGED for review;
the rest would be "proposed auto-accept". Nothing is skipped in reality: this is a shadow
comparison of how well each signal concentrates the errors.

Signals (none uses the gold):
  ocr_junk      the value contains characters a printed name or place does not: digits inside a
                word, ^ / \\ | } { < > ~ _ = + * #, or a capital letter after a lower-case one
                inside a word (OCR splices such as "Aidon (^alcnimAs", "LinuKus")
  gbif_no_exact taxon values only: GBIF species/match (kingdom Animalia) gives no EXACT match
                for the value (other fields: never flagged)
  not_agreed    Gemini 4 Carbon did not return the same value at the same place (value-level
                agreement, stricter than the frozen RQ4 flag); only versions both models read
  legacy_text   the value comes from BHL's legacy OCR (a text-quality signal, no model needed)
  any_cheap     ocr_junk OR gbif_no_exact
For each signal and text version: flagged share, errors caught (recall), precision of the
flags, and errors left among the unflagged predictions.
Writes results/review_signals/.
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone

import pandas as pd
import requests

from common import ROOT
from score import norm_value, score_run_detail

OUT = ROOT / "results" / "review_signals"
GOLD = ROOT / "gold" / "gold_mentions_gloria_test.csv"
OPUS = ["20261119-2052_claude-opus-5-5_test_batch", "20261120-ocrladder_claude-opus-5-5_test_G1",
        "20261120-ocrladder2_claude-opus-5-5_test_G1"]
GEMINI = "20261119-2052_gemini-4-carbon_test_sync"
_JUNK = re.compile(r"[\^/\\|{}<>~_=+*#]|[A-Za-z]\d|\d[A-Za-z]|(?<=[a-z])[A-Z](?=[a-z])")


def ocr_junk(value: str) -> bool:
    v = re.sub(r"\b(Mc|Mac|De|Le|La|Van|Von|D')(?=[A-Z])", "", value)      # real interior capitals
    return bool(_JUNK.search(v))


class Gbif:
    def __init__(self, path):
        self.path, self.rows = path, {}
        if path.exists():
            for line in path.read_text(encoding="utf-8").splitlines():
                r = json.loads(line)
                self.rows[r["q"]] = r["r"]

    def exact(self, name: str) -> bool:
        q = re.sub(r"\s+", " ", name.replace("-\n", "").replace("*", "")).strip(" .,;:()")
        if not q:
            return False
        if q not in self.rows:
            r = requests.get("https://api.gbif.org/v1/species/match", timeout=30,
                             params={"name": q, "kingdom": "Animalia"},
                             headers={"User-Agent": "bioevidencebench-linking-eval"}).json()
            self.rows[q] = {k: r.get(k) for k in ("matchType", "rank", "status", "usageKey", "canonicalName")}
            with self.path.open("a", encoding="utf-8") as f:
                f.write(json.dumps({"q": q, "r": self.rows[q],
                                    "at": datetime.now(timezone.utc).isoformat(timespec="seconds")}) + "\n")
        return self.rows[q].get("matchType") == "EXACT"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    preds = []
    for r in OPUS:
        po = score_run_detail(r, GOLD, "test")["pred_outcomes"]
        preds.append(po[(po.condition == "G1") & (po.version != "modern_dots-mocr_plain")])
    p = pd.concat(preds, ignore_index=True)
    p["error"] = p.outcome != "tp_value"
    gem = score_run_detail(GEMINI, GOLD, "test")["pred_outcomes"]
    gem = gem[(gem.condition == "G1") & gem.m_start.notna()]
    gkey = {(r.page_id, r.version, r.field, int(r.m_start), int(r.m_end), norm_value(str(r.value)))
            for r in gem.itertuples()}
    gem_versions = set(gem.version)

    gb = Gbif(OUT / "gbif_responses.jsonl")
    p["ocr_junk"] = p.value.astype(str).map(ocr_junk)
    p["gbif_no_exact"] = [f == "taxon" and not gb.exact(str(v)) for f, v in zip(p.field, p.value)]
    p["not_agreed"] = [None if v not in gem_versions else
                       (pd.isna(ms) or (pid, v, f, int(ms), int(me), norm_value(str(val))) not in gkey)
                       for pid, v, f, ms, me, val in zip(p.page_id, p.version, p.field, p.m_start, p.m_end, p.value)]
    p["legacy_text"] = p.version == "legacy"
    p["any_cheap"] = p.ocr_junk | p.gbif_no_exact
    p.to_csv(OUT / "predictions.csv", index=False)

    rows = []
    groups = [("all OCR versions", p[p.version != "expert"])] + \
             [(v, d) for v, d in p.groupby("version") if v in ("expert", "legacy", "modern_dots-mocr")]
    for label, d in groups:
        for sig in ("ocr_junk", "gbif_no_exact", "any_cheap", "not_agreed", "legacy_text"):
            x = d[d[sig].notna()]
            if x.empty:
                continue
            f, e = x[sig].astype(bool), x.error
            for book, xb in [("both", x)] + list(x.groupby("book")):
                fb, eb = xb[sig].astype(bool), xb.error
                rows.append({"versions": label, "book": book, "signal": sig, "predictions": len(xb),
                             "errors": int(eb.sum()), "flagged": int(fb.sum()),
                             "flagged_share": round(fb.mean(), 3),
                             "errors_caught": int((fb & eb).sum()),
                             "recall": round((fb & eb).sum() / eb.sum(), 3) if eb.sum() else None,
                             "precision": round((fb & eb).sum() / fb.sum(), 3) if fb.sum() else None,
                             "errors_left_unflagged": int((~fb & eb).sum()),
                             "error_rate_unflagged": round((~fb & eb).sum() / (~fb).sum(), 3) if (~fb).sum() else None})
    s = pd.DataFrame(rows)
    s.to_csv(OUT / "summary.csv", index=False)
    show = s[s.book == "both"].drop(columns="book")
    lines = ["# Which cheap signal concentrates the errors? (exploratory, Opus G1, test pages)", "",
             "Shadow comparison: flagged = sent to review, unflagged = would be proposed for auto-accept. "
             "`recall` = share of errors flagged; `precision` = share of flags that are errors. Decided after "
             "unsealing (DEVIATIONS.md). `not_agreed` exists only where Gemini read the same text version.", "",
             show.to_markdown(index=False), "", "Per book: `summary.csv`."]
    (OUT / "REPORT.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
