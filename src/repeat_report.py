"""Run-to-run noise: compare repeated runs of the same configuration on DEV pages.

A model without a fixed temperature gives slightly different output each
time. Before reading anything into a difference between two conditions, we
need to know how much the same condition differs from itself.

Part 1, output consistency (needs no gold labels). A mention is identified by
(page, field, start, end) in the text the model read. For each text version
and condition:
  n_r1, n_r2, ...   mentions per repeat
  in_all            mentions found by every repeat
  in_any            mentions found by at least one repeat
  all_over_any      in_all / in_any  (1.0 = identical output every time)
  mean_pairwise_f1  mean over pairs of repeats of 2|A∩B| / (|A|+|B|)
  unlocated         outputs that could not be placed in the source, summed over repeats

Part 2, F1 per repeat (only with --gold; needs dev gold labels): value-level,
lenient and exact F1 of every repeat per book, version, condition and field,
with the mean and the sample standard deviation across repeats.

Dev pages only. This script never reads test outputs.

Run:  python src/repeat_report.py --runs <r1> <r2> <r3> --name p3_dev [--gold gold/gold_mentions_gloria.csv]
Output: results/repeats_<name>/consistency.csv, f1_by_repeat.csv, f1_summary.csv, REPORT.md
"""
from __future__ import annotations

import argparse
import itertools
import json

import pandas as pd

from common import ROOT

RESULTS = ROOT / "results"
NOT_LOCATED = {"not_found", "invalid_evidence"}


def mention_keys(run_id: str) -> pd.DataFrame:
    d = pd.read_csv(RESULTS / run_id / "dev_mentions.csv", dtype=str, keep_default_na=False)
    d["located"] = ~d.status.isin(NOT_LOCATED) & (d.start != "")
    d["key"] = d.page_id + "|" + d.field + "|" + d.start.str.replace(r"\.0$", "", regex=True) \
        + "|" + d.end.str.replace(r"\.0$", "", regex=True)
    d["run"] = run_id
    return d


def consistency(runs: list[str]) -> pd.DataFrame:
    data = {r: mention_keys(r) for r in runs}
    combos = sorted(set().union(*[set(zip(d.version, d.condition)) for d in data.values()]))
    rows = []
    for version, condition in combos:
        for field in ["ALL"] + sorted(set().union(*[set(d.field) for d in data.values()])):
            sets, unloc = [], 0
            for r in runs:
                d = data[r]
                d = d[(d.version == version) & (d.condition == condition)]
                if field != "ALL":
                    d = d[d.field == field]
                sets.append(set(d[d.located].key))
                unloc += int((~d.located).sum())
            inter, union = set.intersection(*sets), set.union(*sets)
            pair = [2 * len(a & b) / (len(a) + len(b)) if (a or b) else 1.0
                    for a, b in itertools.combinations(sets, 2)]
            row = {"version": version, "condition": condition, "field": field}
            row |= {f"n_r{i + 1}": len(s) for i, s in enumerate(sets)}
            row |= {"in_all": len(inter), "in_any": len(union),
                    "all_over_any": round(len(inter) / len(union), 3) if union else 1.0,
                    "mean_pairwise_f1": round(sum(pair) / len(pair), 3) if pair else 1.0,
                    "unlocated": unloc}
            rows.append(row)
    return pd.DataFrame(rows)


def f1_by_repeat(runs: list[str], gold: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    from score import score_run   # imported here so Part 1 works without gold or scipy
    parts = []
    for i, r in enumerate(runs, 1):
        s, _ = score_run(r, gold, "dev")
        parts.append(s.assign(repeat=i, run=r))
    long = pd.concat(parts, ignore_index=True)
    keys = ["book", "version", "condition", "field"]
    summ = long.groupby(keys).agg(
        gold=("gold", "first"),
        **{f"{lvl}_F1_mean": (f"{lvl}_F1", "mean") for lvl in ("value", "lenient", "exact")},
        **{f"{lvl}_F1_sd": (f"{lvl}_F1", "std") for lvl in ("value", "lenient", "exact")},
        value_F1_min=("value_F1", "min"), value_F1_max=("value_F1", "max")).round(3).reset_index()
    return long, summ


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", nargs="+", required=True)
    ap.add_argument("--name", required=True)
    ap.add_argument("--gold")
    a = ap.parse_args()
    if len(a.runs) < 2:
        raise SystemExit("Give at least two runs")
    cfgs = [json.loads((RESULTS / r / "config.json").read_text()) for r in a.runs]
    same = {(c.get("model"), c.get("prompt_version"), c.get("effort"), c.get("system_sha256")) for c in cfgs}
    if len(same) != 1:
        raise SystemExit(f"Runs do not share one configuration: {same}")

    out = RESULTS / f"repeats_{a.name}"
    out.mkdir(exist_ok=True)
    cons = consistency(a.runs)
    cons.to_csv(out / "consistency.csv", index=False)
    model, prompt, effort, _ = next(iter(same))
    lines = [f"# Repeat report: {a.name} (DEV pages only)", "",
             f"Runs: {', '.join('`' + r + '`' for r in a.runs)}",
             f"Configuration (identical in all runs): model `{model}`, prompt `{prompt}`, effort `{effort}`.", "",
             "## Output consistency (no gold needed)", "",
             "A mention is (page, field, start, end) in the text the model read. `all_over_any` is the share",
             "of mentions found by every repeat among those found by any repeat.", "",
             cons[cons.field == "ALL"].drop(columns="field").to_markdown(index=False), "",
             "By field: `consistency.csv`.", ""]
    if a.gold:
        long, summ = f1_by_repeat(a.runs, a.gold)
        long.to_csv(out / "f1_by_repeat.csv", index=False)
        summ.to_csv(out / "f1_summary.csv", index=False)
        show = summ[summ.field == "ALL_PRIMARY"][["book", "version", "condition", "gold", "value_F1_mean",
                                                 "value_F1_sd", "value_F1_min", "value_F1_max",
                                                 "lenient_F1_mean", "lenient_F1_sd"]]
        lines += ["## F1 per repeat (dev gold)", "",
                  "Mean and sample standard deviation over the repeats, primary fields together.",
                  "Per repeat and per field: `f1_by_repeat.csv`, `f1_summary.csv`.", "",
                  show.to_markdown(index=False), ""]
    else:
        lines += ["## F1 per repeat", "",
                  "Not computed: there are no dev gold labels yet. Re-run with `--gold` once the 6 dev",
                  "pages are labelled.", ""]
    (out / "REPORT.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
