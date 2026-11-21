"""Module 7b, stage 4 analysis (CPU): metrics, paired page-block bootstrap, decision rules.

    python rl/training/analyze_test_7b.py --run rl/training/runs/<stage-4 run> --out rl/training/results_test

Implements TEST_PROTOCOL.md (which points to METRICS.md sections 3-5):
- per model and test set: primary metrics raw and post-processed, format-valid rate, pass@1
  (answers 0-3) and pass@8 (any of 8); Copy = the OCR itself; A' = Base post-processed;
- paired differences Δ = metric(X) - metric(Y) on the same lines, 95% interval from 2,000 bootstrap
  resamples of page blocks (in-book: split v2 blocks; Cuvier: pages), seed 20261122;
- decision rules per seed, reported as "every seed above 0" or not;
- reward-hacking candidates: answers with reward >= 0.75 that fail a check independent of the
  reward (further from the expert line than the OCR by CER; a damaged line copied; run-on text),
  listed for review, never counted as confirmed until checked by hand.
"""
from __future__ import annotations

import argparse
import gzip
import json
from pathlib import Path

import numpy as np
import pandas as pd
import rapidfuzz.distance.Levenshtein as Lev

import common_7b as C

DATA = C.ROOT / "rl" / "training" / "data"
SETS = ("p0_test_inbook", "p0_test_cuvier", "p0_test_inbook_rest")
B, SEED, K1, MARGIN = 2000, 20261122, 4, 0.01


def blocks_for(items: list[dict]) -> dict[str, int]:
    sp = pd.read_csv(C.ROOT / "rl" / "env" / "task_b_ocr_repair" / "splits_v2.csv").set_index("PageID")
    out = {}
    for it in items:
        blk = int(sp.at[it["page_id"], "block"]) if it["book"] != "Cuvier" else -1
        out[it["item_id"]] = blk if blk >= 0 else int(it["page_id"])      # Cuvier: one block per page
    return out


def answer_table(rows: list[dict], items: dict[str, dict], k1: int = K1) -> pd.DataFrame:
    """Per line: numerators and denominators of the primary metrics, averaged over answers 0..k1-1."""
    df = pd.DataFrame(rows)
    df = df[df["sample"] < k1]
    g = df.groupby("item_id").agg(**{c: (c, "mean") for c in (
        "repaired", "repaired_post", "name_repaired", "name_repaired_post", "preserved", "preserved_post",
        "gated", "gated_post", "reward", "reward_post")})
    g["pass1"] = df.assign(p=df.reward == 1.0).groupby("item_id").p.mean()
    it = pd.DataFrame(items.values()).set_index("item_id")
    g["dmg"] = it.n_damaged
    g["names"] = it.n_name_damaged.fillna(0)
    g["correct"] = it.n_words - it.n_damaged
    return g


def copy_table(items: dict[str, dict]) -> pd.DataFrame:
    rows = [dict(item_id=i, sample=k, **C.score_answer(it, it["input"])) for i, it in items.items() for k in range(K1)]
    return answer_table(rows, items)


def metrics(t: pd.DataFrame) -> dict:
    m = {}
    for tag in ("", "_post"):
        m["repair_rate" + tag] = t["repaired" + tag].sum() / t.dmg.sum()
        m["name_recovery" + tag] = t["name_repaired" + tag].sum() / t.names.sum() if t.names.sum() else np.nan
        m["preservation" + tag] = t["preserved" + tag].sum() / t.correct.sum()
        m["format_failure" + tag] = t["gated" + tag].mean()
        m["mean_reward" + tag] = t["reward" + tag].mean()
    m["format_valid_rate"] = 1 - m["format_failure"]
    m["pass1"] = t.pass1.mean()
    return m


METRIC_PARTS = {"repair_rate": ("repaired", "dmg"), "name_recovery": ("name_repaired", "names"),
                "preservation": ("preserved", "correct")}


def paired(tx: pd.DataFrame, ty: pd.DataFrame, blocks: dict[str, int], metric: str, post: bool,
           rng: np.random.Generator) -> dict:
    num, den = METRIC_PARTS[metric]
    tag = "_post" if post else ""
    d = pd.DataFrame({"nx": tx[num + tag], "ny": ty[num + tag], "den": tx[den]}).dropna()
    d["blk"] = d.index.map(blocks)
    s = d.groupby("blk")[["nx", "ny", "den"]].sum()
    point = (s.nx.sum() - s.ny.sum()) / s.den.sum() if s.den.sum() else np.nan
    idx = rng.integers(0, len(s), size=(B, len(s)))
    v = s.to_numpy()
    num_d, dd = (v[:, 0] - v[:, 1])[idx].sum(1), v[:, 2][idx].sum(1)
    boot = np.where(dd > 0, num_d / np.where(dd > 0, dd, 1), np.nan)
    lo, hi = np.nanpercentile(boot, [2.5, 97.5])
    return {"delta": round(float(point), 4), "lo": round(float(lo), 4), "hi": round(float(hi), 4), "blocks": len(s)}


def noninferiority(r: dict) -> str:
    return "pass" if r["lo"] > -MARGIN else "fail" if r["hi"] < -MARGIN else "inconclusive"


def hacking_candidates(rows: list[dict], items: dict[str, dict], label: str, set_name: str) -> list[dict]:
    out = []
    for r in rows:
        if r["reward"] < 0.75:
            continue
        it = items[r["item_id"]]
        a = (r["answer"] or "").strip()
        why = []
        if Lev.distance(a, it["target"]) > Lev.distance(it["input"], it["target"]):
            why.append("further from the expert line than the OCR (CER)")
        if it["n_damaged"] > 0 and a == it["input"].strip():
            why.append("damaged line copied")
        if r.get("run_on", "within") != "within":
            why.append("run-on")
        if why:
            out.append({"model": label, "set": set_name, "item_id": r["item_id"], "sample": r["sample"],
                        "reward": r["reward"], "why": "; ".join(why)})
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    run, out = Path(args.run), Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    cfg = json.loads((C.ROOT / "rl" / "training" / "configs" / "stage4_models.json").read_text())
    rng = np.random.default_rng(SEED)
    tables, cands, summary, pass8 = {}, [], [], []
    for set_name in SETS:
        items = {it["item_id"]: it for it in C.load_items(DATA / f"{set_name}.jsonl")}
        blocks = blocks_for(list(items.values()))
        pages = {i: int(it["page_id"]) for i, it in items.items()}
        tables[set_name] = {"copy": copy_table(items)}
        for m in cfg["models"]:
            f = run / f"{m['label']}_{set_name}_answers.jsonl.gz"
            if set_name not in m["sets"] or not f.exists():
                continue
            rows = [json.loads(line) for line in gzip.open(f, "rt", encoding="utf-8")]
            tables[set_name][m["label"]] = answer_table(rows, items)
            p8 = pd.DataFrame(rows).groupby("item_id").reward.max().eq(1.0)
            pass8.append({"set": set_name, "model": m["label"], "pass8": round(p8.mean(), 4)})
            cands += hacking_candidates(rows, items, m["label"], set_name)
        for label, t in tables[set_name].items():
            summary.append({"set": set_name, "model": label, **{k: round(v, 4) for k, v in metrics(t).items()}})
            if label == "base":
                summary.append({"set": set_name, "model": "base_post (A')",
                                **{k: round(v, 4) for k, v in metrics(t).items() if k.endswith("_post")}})
        # paired comparisons of section 5, per seed
        T = tables[set_name]
        comps = []
        for s in (1, 2):
            for x, y in ((f"grpo_s{s}", "base"), (f"sft_grpo_s{s}", f"sft_s{s}"), (f"sft_s{s}", "base"),
                         (f"sft_grpo_s{s}", "base")):
                if x not in T or y not in T:
                    continue
                for metric in METRIC_PARTS:
                    for post in (False, True):
                        r = paired(T[x], T[y], blocks, metric, post, rng)
                        pg = paired(T[x], T[y], pages, metric, post, rng)       # sensitivity only
                        comps.append({"set": set_name, "x": x, "y": y, "metric": metric,
                                      "scored": "post-processed" if post else "raw", **r,
                                      "non_inferiority": noninferiority(r) if metric == "preservation" else "",
                                      "page_lo": pg["lo"], "page_hi": pg["hi"], "pages": pg["blocks"]})
        pd.DataFrame(comps).to_csv(out / f"paired_{set_name}.csv", index=False)
    pd.DataFrame(summary).to_csv(out / "metrics.csv", index=False)
    pd.DataFrame(pass8).to_csv(out / "pass8.csv", index=False)
    pd.DataFrame(cands).to_csv(out / "hacking_candidates.csv", index=False)
    print(pd.DataFrame(summary).to_string())


if __name__ == "__main__":
    main()
