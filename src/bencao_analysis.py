"""本草綱目 pilot: analyses added after the freeze (data/bencao/FREEZE_bencao.json), kept out of the frozen
src/bencao_extract.py so that `python src/bencao_freeze.py --verify` stays clean. Nothing here changes how a
mention is extracted, located or scored.

    python src/bencao_analysis.py bootstrap <reference run> <run> ...   # page-bootstrap intervals for value F1
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from bencao_extract import PAGES, PRIMARY, ROOT  # noqa: E402


def bootstrap(run_dirs: list[str], reps: int = 5000) -> None:
    """Value F1 per text version with 95% intervals from resampling half-leaves (seed 20261124), and the paired
    difference from the first run given (the reference text). Six half-leaves: wide intervals, read as such.
    -> results/bencao_pilot/value_f1_bootstrap_<prompt>.csv"""
    import numpy as np
    from collections import Counter
    gold = pd.read_csv(ROOT / "gold" / "gold_mentions_bencao_gloria.csv", keep_default_na=False)

    def per_page(run: Path) -> dict:
        pred = pd.read_csv(run / "mentions.csv", keep_default_na=False)
        pred = pred[pred.status.str.startswith("ok")]
        out = {}
        for pb in PAGES:
            tp = fp = fn = 0
            for f in PRIMARY:
                g = gold[(gold.page_id == pb) & (gold.field == f)]
                req = Counter(t.replace("\n", "") for t in g[g.adjudication != "expert_pending"].text)
                opt = Counter(t.replace("\n", "") for t in g[g.adjudication == "expert_pending"].text)
                p = Counter(str(v).replace("\n", "") for v in pred[(pred.page_id == pb) & (pred.field == f)].value)
                h = req & p
                tp += sum(h.values()); fp += sum(((p - h) - opt).values()); fn += sum((req - h).values())
            out[pb] = np.array([tp, fp, fn])
        return out

    f1 = lambda a: 2 * a[0] / (2 * a[0] + a[1] + a[2])
    runs = [Path(d) for d in run_dirs]
    C = {r: per_page(r) for r in runs}
    rng = np.random.default_rng(20261124)
    samples = [rng.choice(PAGES, len(PAGES)) for _ in range(reps)]
    ref = runs[0]
    rows = []
    for r in runs:
        text = json.loads((r / "config.json").read_text(encoding="utf-8")).get("text", "verified_plain")
        pts = [f1(sum(C[r][p] for p in s)) for s in samples]
        diffs = [f1(sum(C[r][p] for p in s)) - f1(sum(C[ref][p] for p in s)) for s in samples]
        rows.append({"text": text, "run": r.name, "value_f1": round(f1(sum(C[r].values())), 3),
                     "ci_low": round(float(np.percentile(pts, 2.5)), 3), "ci_high": round(float(np.percentile(pts, 97.5)), 3),
                     "diff_vs_first": round(f1(sum(C[r].values())) - f1(sum(C[ref].values())), 3),
                     "diff_ci_low": round(float(np.percentile(diffs, 2.5)), 3),
                     "diff_ci_high": round(float(np.percentile(diffs, 97.5)), 3),
                     "per_page": " ".join(f"{p}:{f1(C[r][p]):.2f}" for p in PAGES)})
    d = pd.DataFrame(rows)
    pv = json.loads((runs[0] / "config.json").read_text(encoding="utf-8"))["prompt_version"].split("-")[1]
    d.to_csv(ROOT / "results" / "bencao_pilot" / f"value_f1_bootstrap_{pv}.csv", index=False)
    print(d.drop(columns=["run"]).to_string(index=False))


if __name__ == "__main__":
    if sys.argv[1] == "bootstrap":
        bootstrap(sys.argv[2:])
