"""PCAS botany external case (exploratory, reported separately; never pooled with Butler/Reeve).

    python src/score_pcas.py

Gold: gold/gold_mentions_pcas_gloria.csv (Gloria, labelled against the scans, no positions, text as
printed). There is no expert transcription, so scoring is value-level only ("bag" scoring as in
run_exploratory.py): per page and field, the multiset of normalised predicted values against the
gold texts (score.norm_value: case, whitespace, end punctuation; letters never changed).
Conditions (Opus 5.5, effort medium, sync): G1F = the frozen G1 prompt on BHL legacy OCR (values
sliced from the OCR); G2 = LLM repair on legacy OCR (scored on the reading); V1 = page image only.
Writes results/pcas/REPORT.md, scores.csv, misses.csv.
"""
from __future__ import annotations

import json
from collections import Counter

import pandas as pd

from common import ROOT
from score import norm_value

GOLDS = {"as labelled": ROOT / "gold" / "gold_mentions_pcas_gloria.csv",
         # Gloria's decisions made AFTER seeing model outputs (gold/gold_changes_pcas_gloria.csv, 2026-11-20):
         # titles out of person spans, narrow-to-wide chains as one span, one institution, a part-of-place
         # phrase, and `Carolinæ` as printed. Both are reported; neither replaces the other.
         "adjudicated": ROOT / "gold" / "gold_mentions_pcas_gloria_adjudicated.csv"}
OUT = ROOT / "results" / "pcas"
PRIMARY = ["taxon", "person", "locality", "institution", "date"]


def bag(pred: pd.DataFrame, gold: pd.DataFrame, fields: list[str]) -> tuple[int, int, int, list]:
    tp = fp = fn = 0
    misses = []
    for pid in sorted(set(gold.page_id) | set(pred.page_id)):
        for f in fields:
            pv = Counter(norm_value(str(v)) for v in pred[(pred.page_id == pid) & (pred.field == f)].value)
            for g in gold[(gold.page_id == pid) & (gold.field == f)].text:
                k = norm_value(g)
                if pv[k] > 0:
                    pv[k] -= 1
                    tp += 1
                else:
                    fn += 1
                    misses.append({"page_id": pid, "field": f, "kind": "missed gold", "text": g})
            for k, c in pv.items():
                if c > 0:
                    fp += c
                    misses += [{"page_id": pid, "field": f, "kind": "extra output", "text": k}] * c
    return tp, fp, fn, misses


def f1(tp, fp, fn):
    p = tp / (tp + fp) if tp + fp else 0.0
    r = tp / (tp + fn) if tp + fn else 0.0
    return round(p, 3), round(r, 3), round(2 * p * r / (p + r), 3) if p + r else 0.0


def main() -> None:
    rows, miss = [], []
    for (gname, gpath), d in ((g, d) for g in GOLDS.items()
                              for d in sorted((ROOT / "results").glob("*_explore_*_pcas"))):
        gold = pd.read_csv(gpath, keep_default_na=False)
        cfg = json.loads((d / "config.json").read_text())
        pred = pd.read_csv(d / "test_mentions.csv", keep_default_na=False)
        label = f"{cfg['condition']} · {cfg['versions'][0]}"
        for name, fields in (("ALL_PRIMARY", PRIMARY), *((f, [f]) for f in PRIMARY + ["vernacular"])):
            tp, fp, fn, m = bag(pred, gold, fields)
            p, r, F = f1(tp, fp, fn)
            rows.append({"gold_version": gname, "condition": label, "field": name, "gold": tp + fn, "tp": tp, "fp": fp, "fn": fn,
                         "P": p, "R": r, "F1": F})
            if name == "ALL_PRIMARY" or name == "vernacular":
                miss += [{"gold_version": gname, "condition": label, **x} for x in m]
        rows[-1]["usd"] = cfg["usd_total"]
    s = pd.DataFrame(rows)
    OUT.mkdir(parents=True, exist_ok=True)
    s.to_csv(OUT / "scores.csv", index=False)
    pd.DataFrame(miss).to_csv(OUT / "misses.csv", index=False)
    piv = s.pivot_table(index="field", columns=["gold_version", "condition"], values="F1"
                        ).reindex(["ALL_PRIMARY"] + PRIMARY + ["vernacular"])
    lines = ["# PCAS botany external case (exploratory)", "",
             "Eastwood 1898, PCAS 3rd ser. Botany vol. 1, 8 pages (BHL item 48989). Gold by Gloria against the "
             "scans (210 rows as labelled; 206 after her adjudication, made after model outputs were seen). Value-level (bag) F1, all pages pooled (8 pages: no interval). Opus 5.5. "
             "Not comparable with the main experiment's positional scores, and not pooled with it.", "",
             piv.to_markdown(), "",
             s[s.field == "ALL_PRIMARY"][["gold_version", "condition", "tp", "fp", "fn", "P", "R", "F1"]].to_markdown(index=False), "",
             "Misses and extra outputs per condition: `misses.csv`.", ""]
    (OUT / "REPORT.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
