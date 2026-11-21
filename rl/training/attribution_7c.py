"""Module 7c: where and why the trained models differ (CPU, on the frozen stage-4 answers).

    python rl/training/attribution_7c.py

Nothing here chooses a model or a setting: the answers are those of the locked test
(`runs/20261121-2112_test4`). Answers 0-3 (pass@1 setting), after the fixed clean-up (content).

1. Error types: each damaged reference word gets one type, first match in this order: scientific
   name (gnfinder flag), long s (ſ), ligature (æ œ), digit, split (the OCR has a space inside it),
   missing (no aligned OCR text), letters (an ordinary misread word). Repair rate per type and model.
2. Edit behaviour: edit rate (answer differs from the OCR), edit precision (reference words the
   model changed that are now right / words it changed), edit recall (= repair rate), words broken,
   words inserted.
3. Difficulty before training: lines grouped by Base's pass rate over its 8 answers (0%, 1-99%,
   100%); pass@1 and repair rate of each model per group.
4. Reading sheet for Gloria (METRICS.md 7): 40 in-book + 10 Cuvier lines, half "Base wrong, D right"
   and half the reverse (answer 0 of Base and of D seed 1, the GRPO condition of the larger
   confirmation), shuffled, with a comment column.
Writes rl/training/results_7c/.
"""
from __future__ import annotations

import gzip
import json
import random
import re

import pandas as pd

import common_7b as C

T = C.T
RUN = C.ROOT / "rl" / "training" / "runs" / "20261121-2112_test4"
OUT = C.ROOT / "rl" / "training" / "results_7c"
DATA = C.ROOT / "rl" / "training" / "data"
SETS = ("p0_test_inbook", "p0_test_cuvier")
TYPES = ("name", "long s", "ligature", "digit", "split", "missing", "letters")


def clean(ans: str, target: str) -> str:
    return T.accept_fractions(T.nfc(T.format_cleanup(ans or "")).strip(), target)


def damaged_words(it: dict) -> list[tuple[int, str]]:
    rows, _ = T.word_status(it["target"], it["input"])
    out = []
    for i, r in enumerate(rows):
        if T.word_kind(r) != "damaged":
            continue
        w, got = r["word"], r["aligned"] or ""
        flags = it.get("name_word_flags") or []
        t = ("name" if i < len(flags) and flags[i] else "long s" if "ſ" in w else
             "ligature" if re.search("[æœÆŒ]", w) else "digit" if re.search(r"\d", w) else
             "split" if re.search(r"\s", got.strip()) else "missing" if not got.strip() else "letters")
        out.append((i, t))
    return out


def per_answer(it: dict, ans: str) -> dict:
    a = clean(ans, it["target"])
    ref_in, _ = T.word_status(it["target"], it["input"])
    ref_out, _ = T.word_status(it["target"], a)
    changed = [i for i, (x, y) in enumerate(zip(ref_in, ref_out)) if (x["aligned"] or "") != (y["aligned"] or "")]
    dmg = damaged_words(it)
    return {"edited": re.sub(r"\s+", " ", a).strip() != re.sub(r"\s+", " ", it["input"]).strip(),
            "changed": len(changed), "changed_right": sum(ref_out[i]["ok"] for i in changed),
            "broken": sum(1 for x, y in zip(ref_in, ref_out) if x["ok"] and not y["ok"]),
            "inserted": len(T.inserted_words(a, it["target"])) - len(T.inserted_words(it["input"], it["target"])),
            "types": [(t, ref_out[i]["ok"]) for i, t in dmg]}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    cfg = json.loads((C.ROOT / "rl" / "training" / "configs" / "stage4_models.json").read_text())
    labels = [m["label"] for m in cfg["models"]]
    types, edits, diff, answers0 = [], [], [], {}
    for st in SETS:
        items = {it["item_id"]: it for it in C.load_items(DATA / f"{st}.jsonl")}
        loaded = {}
        for lab in labels:
            loaded[lab] = [json.loads(line) for line in gzip.open(RUN / f"{lab}_{st}_answers.jsonl.gz", "rt",
                                                                  encoding="utf-8")]
        base_pass = pd.DataFrame(loaded["base"]).groupby("item_id").reward.apply(lambda s: (s == 1.0).mean())
        group = base_pass.map(lambda p: "0%" if p == 0 else "100%" if p == 1 else "1-99%")
        for lab in labels:
            rows = [r for r in loaded[lab] if r["sample"] < 4]
            for r in rows:
                it = items[r["item_id"]]
                pa = per_answer(it, r["answer"])
                edits.append({"set": st, "model": lab, **{k: v for k, v in pa.items() if k != "types"},
                              "damaged": it["n_damaged"]})
                types += [{"set": st, "model": lab, "type": t, "ok": ok} for t, ok in pa["types"]]
                diff.append({"set": st, "model": lab, "group": group[r["item_id"]], "item_id": r["item_id"],
                             "pass": r["reward"] == 1.0, "repaired": r["repaired_post"], "damaged": it["n_damaged"]})
            answers0[(st, lab)] = {r["item_id"]: r for r in loaded[lab] if r["sample"] == 0}
        if st == "p0_test_inbook":
            items_in = items
        else:
            items_cu = items

    ty = pd.DataFrame(types)
    tab = ty.groupby(["set", "type", "model"]).ok.mean().unstack("model")[labels].round(3)
    n = ty[ty.model == "base"].groupby(["set", "type"]).size().rename("damaged words (per answer x4)")
    tab = tab.join(n / 4).reindex([(s, t) for s in SETS for t in TYPES if (s, t) in tab.index])
    tab.to_csv(OUT / "repair_by_error_type.csv")

    ed = pd.DataFrame(edits).groupby(["set", "model"]).agg(
        edit_rate=("edited", "mean"), changed=("changed", "sum"), changed_right=("changed_right", "sum"),
        broken_per_answer=("broken", "mean"), inserted_per_answer=("inserted", "mean"))
    ed["edit_precision"] = (ed.changed_right / ed.changed).round(3)
    ed = ed.drop(columns=["changed", "changed_right"]).round(3).reindex([(s, m) for s in SETS for m in labels])
    ed.to_csv(OUT / "edit_behaviour.csv")

    df = pd.DataFrame(diff)
    g = df.groupby(["set", "group", "model"]).agg(pass1=("pass", "mean"), rep=("repaired", "sum"), dmg=("damaged", "sum"))
    g["repair_rate"] = (g.rep / g.dmg.where(g.dmg > 0)).round(3)
    lines = df[df.model == "base"].groupby(["set", "group"]).item_id.nunique().rename("lines")
    dt = g.pass1.round(3).unstack("model")[labels].join(lines)
    dr = g.repair_rate.unstack("model")[labels].join(lines)
    dt.to_csv(OUT / "difficulty_pass1.csv")
    dr.to_csv(OUT / "difficulty_repair.csv")

    # reading sheet
    rng = random.Random(20261122)
    sheet = []
    for st, items, n_each in (("p0_test_inbook", items_in, 20), ("p0_test_cuvier", items_cu, 5)):
        b, d = answers0[(st, "base")], answers0[(st, "sft_grpo_s1")]
        better = sorted(i for i in items if b[i]["reward"] < 1 and d[i]["reward"] == 1 and items[i]["n_damaged"] > 0)
        worse = sorted(i for i in items if b[i]["reward"] == 1 and d[i]["reward"] < 1)
        for kind, pool in (("Base 错，D 对", better), ("Base 对，D 错", worse)):
            for i in rng.sample(pool, min(n_each, len(pool))):
                sheet.append({"组": kind, "书": items[i]["book"], "OCR 输入": items[i]["input"],
                              "Base 回答": b[i]["answer"], "D 回答（SFT→GRPO 种子 1）": d[i]["answer"],
                              "专家转录": items[i]["target"], "Base 奖励": b[i]["reward"], "D 奖励": d[i]["reward"],
                              "你的看法": ""})
    rng.shuffle(sheet)
    sh = pd.DataFrame(sheet)
    sh.insert(0, "编号", [f"R{i + 1:02d}" for i in range(len(sh))])
    with pd.ExcelWriter(OUT / "reading_sheet_gloria.xlsx") as w:
        pd.DataFrame({"说明": [
            "锁定测试集上随机抽的约 50 行：一半是 Base 第一个回答没得满分、D（SFT→GRPO 种子 1）得了满分；一半反过来。",
            "请读一读，在“你的看法”里写：修对的地方是真的修复还是碰巧；改错的是什么类型（学名、普通词、数字、标点、乱加词……）。",
            "奖励 1.0 = 所有受损词都改对、没有改坏或加词（不评标点，大小写中立）。"]}).to_excel(w, sheet_name="说明", index=False)
        sh.to_excel(w, sheet_name="lines", index=False)
    for name, t in (("repair_by_error_type", tab), ("edit_behaviour", ed), ("difficulty_pass1", dt),
                    ("difficulty_repair", dr)):
        print(f"\n## {name}\n{t.to_string()}")
    print("\nreading sheet:", sh["组"].value_counts().to_dict())


if __name__ == "__main__":
    main()
