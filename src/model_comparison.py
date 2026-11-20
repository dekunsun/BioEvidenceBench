"""Four Claude models on the frozen G1 condition, test pages (exploratory, DEVIATIONS.md).

    python src/model_comparison.py

Same prompt (p4-guide-v0.6), same three text versions, sync mode; only the model differs.
Opus is the frozen batch run; Sonnet / Haiku / Fable are sync runs made after unsealing. Cost per
page = the run's own cost.json total / (pages x versions); per 1,000 pages for one text version.
Writes results/model_comparison/REPORT.md and scores.csv.
"""
from __future__ import annotations

import json

import pandas as pd

from common import ROOT
from score import score_run_detail

RUNS = {"claude-opus-5-5 (batch, frozen)": "20261119-2052_claude-opus-5-5_test_batch",
        "claude-sonnet-5-5": "20261120-0143_claude-sonnet-5-5_test_sync",
        "claude-haiku-5-5": "20261120-0145_claude-haiku-5-5_test_sync",
        "claude-fable-5-2": "20261120-0148_claude-fable-5-2_test_sync"}
GOLD = ROOT / "gold" / "gold_mentions_gloria_test.csv"
OUT = ROOT / "results" / "model_comparison"


def main() -> None:
    rows, cost = [], []
    for name, run in RUNS.items():
        s = score_run_detail(run, GOLD, "test")["summary"]
        s = s[(s.field == "ALL_PRIMARY") & (s.condition == "G1")]
        for r in s.itertuples():
            rows.append({"model": name, "book": r.book, "version": r.version, "value_F1": r.value_F1,
                         "lo": r.value_F1_lo, "hi": r.value_F1_hi})
        d = ROOT / "results" / run
        cj = json.loads((d / "cost.json").read_text())
        usd, n_req = cj["usd_total"], cj["requests"]
        cfg = json.loads((d / "config.json").read_text())
        cost.append({"model": name, "requests_all": n_req, "usd_total_run": round(usd, 3),
                     "usd_per_request": round(usd / n_req, 4),
                     "usd_per_1000_pages": round(1000 * usd / n_req, 2),
                     "mode": "batch (50% off)" if "batch" in run else "sync",
                     "note": f"{len(cfg.get('versions', []))} versions x {','.join(cfg.get('conditions', []))}"})
    d = pd.DataFrame(rows)
    OUT.mkdir(parents=True, exist_ok=True)
    d.to_csv(OUT / "scores.csv", index=False)
    c = pd.DataFrame(cost)
    c.to_csv(OUT / "cost.csv", index=False)
    piv = d.assign(cell=d.apply(lambda r: f"{r.value_F1:.3f} [{r.lo:.2f}-{r.hi:.2f}]", axis=1)) \
           .pivot_table(index="model", columns=["book", "version"], values="cell", aggfunc="first")
    lines = ["# Four Claude models, G1, test pages (exploratory)", "",
             "ALL_PRIMARY value F1 with 95% page-bootstrap interval, per book. Same prompt p4-guide-v0.6. "
             "Opus is the frozen pre-registered run; the others were run after unsealing (DEVIATIONS.md).", "",
             piv.to_markdown(), "", "Cost (all requests of the run, test pages; per request = one page x one "
             "text version x one condition):", "", c.to_markdown(index=False), ""]
    (OUT / "REPORT.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
