"""Task B step 5: model trial and within-group reward variance (plan 6.7, 6.8).

    python src/rl_task_b_trial.py --pages pilot5 --prompt repair_v1 --max-usd 4   # the 5-page pilot
    python src/rl_task_b_trial.py --pages dev200 --max-usd 6                     # 200 dev items
    python src/rl_task_b_trial.py --report <run_id>                     # re-score and re-report

For each item (one OCR line, with the OCR lines before and after it as context) each model is
asked K times (default 8) to repair the line. Every answer is scored with Reward v1.2
(`rl_task_b.reward`). Reported per model: the share of items whose K rewards are not all equal
(only those give GRPO a learning signal), pass rates (reward 1.0), format failures, and cost.

Data: **dev split only** (split v2). The pilot takes 5 dev pages, one per training book, drawn
with a fixed seed among dev pages with at least 8 usable lines; per page 8 items: up to 6 lines
with 2-5 damaged words, then 2 clean lines (about 20%, plan 6.2), filling from 1 or more than 5
damaged words when a page has too few. In-book test pages, Cuvier and sealed pages are never read.

Settings: no temperature (Claude Opus 5.5 and Haiku 5.5 reject sampling parameters; the default
is 1.0), effort `low`, thinking at the model default (Opus 5.5 cannot turn it off), max_tokens
2000. Each run writes rl/env/task_b_ocr_repair/trial/<run_id>/: config.json (models, settings,
prompt SHA-256, unit-file SHA-256), prompt.txt, items.jsonl, outputs.jsonl (raw answers, usage,
stop reason, timestamps), rewards.csv, groups.csv, REPORT.md.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

import pandas as pd

import rl_task_b as T
from common import CACHE, ROOT

ENV = ROOT / "rl" / "env" / "task_b_ocr_repair"
TRIAL = ENV / "trial"
UNITS = CACHE / "taskb" / "units"
PROMPTS = ENV / "prompts"
# repair_v1: the 5-page pilot. repair_v2 (Gloria, 2026-11-21): adds that letter-spaced words are
# written without the spaces, the transcription's convention.
PROMPT_VERSION = "repair_v2"
SEED = 20261121
PILOT_PAGES = (8967011, 8992478, 9684334, 9739676, 12341902)   # the 5-page pilot (prompt repair_v1)
PRICES = {"claude-opus-5-5": (4.00, 20.00), "claude-haiku-5-5": (0.10, 0.50)}   # USD per M tokens in/out
BOOKS = {"Butler": ("Birds of Great Britain and Ireland, vol. 2", 1907, "English"),
         "Reeve": ("Conchologia iconica, vol. 5", 1849, "Latin and English"),
         "Trudy": ("Trudy Russkago entomologicheskago obshchestva / Horae Societatis Entomologicae Rossicae, vol. 16",
                   1881, "German, French, Latin and Russian"),
         "Chitinskelett": ("Das Chitinskelett von Eosentomon (Zoologica 64)", 1912, "German"),
         "Piscium": ("Piscium querelae et vindiciae", 1708, "Latin")}


def load_prompt(version: str = PROMPT_VERSION) -> tuple[str, str]:
    text = (PROMPTS / f"{version}.txt").read_text(encoding="utf-8")
    system = text.split("=== system ===\n", 1)[1].split("=== user ===\n", 1)[0].strip()
    user = text.split("=== user ===\n", 1)[1].strip()
    return system, user


def damage_class(n: int) -> str:
    return "clean" if n == 0 else "1" if n == 1 else "2-5" if n <= 5 else ">5"


def with_context(us: list[dict], idx: pd.DataFrame) -> list[dict]:
    """Add the OCR of the neighbouring expert lines (valid or not) as context."""
    # Nearest line above / below with OCR text (blank lines and short captions skipped). The
    # trials of 2026-11-21 used line_no +/- 1, which was often a blank line: "(none)".
    out = []
    for u in sorted(us, key=lambda u: (u["page_id"], u["line_no"])):
        pg = idx[(idx.page_id == u["page_id"]) & (idx.input.fillna("").str.strip() != "")].sort_values("line_no")
        before, after = pg[pg.line_no < u["line_no"]].input, pg[pg.line_no > u["line_no"]].input
        u = dict(u)
        u["prev"] = before.iloc[-1] if len(before) else "(none)"
        u["next"] = after.iloc[0] if len(after) else "(none)"
        u["item_id"] = f"{u['page_id']}-{u['line_no']}"
        u["damage_class"] = damage_class(u["n_damaged"])
        out.append(u)
    return out


def select_dev200(per_book: int = 40, clean: int = 8, exclude_pages: tuple = PILOT_PAGES) -> list[dict]:
    """40 dev items per training book, pilot pages left out: 32 damaged (2-5 damaged words first,
    then 1, then more than 5) and 8 clean (20%), drawn with a fixed seed; a book with too few of
    one kind is filled from the other."""
    units = [json.loads(line) for line in (UNITS / "dev.jsonl").open(encoding="utf-8")]
    assert all(u["split"] == "dev" for u in units)
    idx = pd.read_csv(UNITS / "all_units_index.csv")
    rng = random.Random(f"{SEED}-dev200")
    items = []
    for book in sorted(BOOKS):
        us = [u for u in units if u["book"] == book and u["page_id"] not in exclude_pages]
        cls = {c: [u for u in us if damage_class(u["n_damaged"]) == c] for c in ("2-5", "1", ">5", "clean")}
        for c in cls:
            rng.shuffle(cls[c])
        n_dmg = per_book - min(clean, len(cls["clean"]))
        dmg = (cls["2-5"] + cls["1"] + cls[">5"])[:n_dmg]
        cl = cls["clean"][:per_book - len(dmg)]
        items += with_context(dmg + cl, idx)
    return items


def select_items(n_pages: int = 5, per_page: int = 8) -> list[dict]:
    units = [json.loads(line) for line in (UNITS / "dev.jsonl").open(encoding="utf-8")]
    assert all(u["split"] == "dev" for u in units)
    idx = pd.read_csv(UNITS / "all_units_index.csv")
    rng = random.Random(SEED)
    by_page: dict[int, list[dict]] = {}
    for u in units:
        by_page.setdefault(u["page_id"], []).append(u)
    items = []
    for book in sorted(BOOKS):
        pages = sorted(p for p, us in by_page.items() if us[0]["book"] == book and len(us) >= per_page)
        pid = rng.choice(pages)
        us = sorted(by_page[pid], key=lambda u: u["line_no"])
        pool = {c: [u for u in us if damage_class(u["n_damaged"]) == c] for c in ("2-5", "clean", "1", ">5")}
        take = rng.sample(pool["2-5"], min(6, len(pool["2-5"])))
        take += rng.sample(pool["clean"], min(2, len(pool["clean"])))
        rest = [u for u in pool["1"] + pool[">5"] + pool["2-5"] + pool["clean"] if u not in take]
        take += rng.sample(rest, max(0, per_page - len(take)))
        # context: the OCR aligned to the neighbouring expert lines of the same page, valid or not
        ctx = idx[idx.page_id == pid].set_index("line_no").input.fillna("")
        for u in sorted(take, key=lambda u: u["line_no"]):
            u = dict(u)
            u["prev"] = ctx.get(u["line_no"] - 1, "") or "(none)"
            u["next"] = ctx.get(u["line_no"] + 1, "") or "(none)"
            u["item_id"] = f"{pid}-{u['line_no']}"
            u["damage_class"] = damage_class(u["n_damaged"])
            items.append(u)
    return items


def run(args) -> str:
    import anthropic
    system, user_tpl = load_prompt(args.prompt)
    items = select_items() if args.pages == "pilot5" else select_dev200()
    run_id = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M") + f"_taskb_trial_{args.pages}"
    out = TRIAL / run_id
    out.mkdir(parents=True, exist_ok=True)
    prompt_file = PROMPTS / f"{args.prompt}.txt"
    (out / "prompt.txt").write_text(prompt_file.read_text(encoding="utf-8"), encoding="utf-8")
    with (out / "items.jsonl").open("w", encoding="utf-8") as f:
        for it in items:
            f.write(json.dumps(it, ensure_ascii=False) + "\n")
    config = {"run_id": run_id, "models": args.models, "k": args.k, "effort": "low", "temperature": "not sent (default 1.0)",
              "thinking": "model default (adaptive)", "max_tokens": 2000, "prompt_version": args.prompt,
              "prompt_sha256": hashlib.sha256(prompt_file.read_bytes()).hexdigest(),
              "dev_units_sha256": hashlib.sha256((UNITS / "dev.jsonl").read_bytes()).hexdigest(),
              "reward": "Reward v1.2 (rl/env/task_b_ocr_repair/REWARD_DESIGN.md)", "seed": SEED,
              "pages": sorted({it["page_id"] for it in items}), "n_items": len(items), "max_usd": args.max_usd,
              "api": "Anthropic Messages API, sync, 8 threads", "prices_usd_per_mtok": PRICES}
    (out / "config.json").write_text(json.dumps(config, indent=2), encoding="utf-8")

    client = anthropic.Anthropic(api_key=os.environ["EVAL_ANTHROPIC_API_KEY"], max_retries=4)
    lock, spent = threading.Lock(), [0.0]
    jobs = [(m, it, k) for m in args.models for it in items for k in range(args.k)]

    def one(job):
        model, it, k = job
        rec = {"model": model, "item_id": it["item_id"], "sample": k,
               "sent_at": datetime.now(timezone.utc).isoformat(timespec="seconds")}
        if spent[0] > args.max_usd:
            return rec | {"error": "cap reached, not sent"}
        bt, yr, lang = BOOKS[it["book"]]
        msg = user_tpl.format(book_title=bt, year=yr, language=lang, prev=it["prev"], line=it["input"], next=it["next"])
        try:
            m = client.messages.create(model=model, max_tokens=2000, system=system,
                                       messages=[{"role": "user", "content": msg}],
                                       output_config={"effort": "low"})
            text = "".join(b.text for b in m.content if b.type == "text")
            usd = (m.usage.input_tokens * PRICES[model][0] + m.usage.output_tokens * PRICES[model][1]) / 1e6
            with lock:
                spent[0] += usd
            return rec | {"output": text, "stop_reason": m.stop_reason, "usd": round(usd, 6),
                          "input_tokens": m.usage.input_tokens, "output_tokens": m.usage.output_tokens}
        except Exception as e:
            return rec | {"error": repr(e)[:400]}

    with ThreadPoolExecutor(8) as ex:
        recs = list(ex.map(one, jobs))
    with (out / "outputs.jsonl").open("w", encoding="utf-8") as f:
        for r in recs:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"sent {sum('output' in r for r in recs)} of {len(recs)}; ${spent[0]:.3f}")
    return run_id


def report(run_id: str) -> None:
    out = TRIAL / run_id
    cfg = json.loads((out / "config.json").read_text())
    items = {it["item_id"]: it for it in map(json.loads, (out / "items.jsonl").open(encoding="utf-8"))}
    recs = [json.loads(line) for line in (out / "outputs.jsonl").open(encoding="utf-8")]
    rows = []
    for r in recs:
        it = items[r["item_id"]]
        base = {"model": r["model"], "item_id": r["item_id"], "sample": r["sample"], "book": it["book"],
                "page_id": it["page_id"], "damage_class": it["damage_class"], "n_damaged": it["n_damaged"],
                "usd": r.get("usd", 0.0), "output_tokens": r.get("output_tokens"), "stop_reason": r.get("stop_reason"),
                "error": r.get("error", "")}
        if "output" not in r:
            rows.append(base | {"reward": None})
            continue
        d = T.reward(it, r["output"])
        rows.append(base | {k: d[k] for k in ("reward", "reward_reading", "format_valid", "format_reason",
                                               "integrity_valid", "alignment_valid", "repaired_words",
                                               "damaged_correct_words", "extra_words", "case_accuracy",
                                               "exact_repair_rate", "scientific_name_damaged",
                                               "scientific_name_repairs")}
                    | {"output": r["output"]})
    rw = pd.DataFrame(rows)
    rw.to_csv(out / "rewards.csv", index=False)
    ok = rw[rw.reward.notna()]
    g = ok.groupby(["model", "item_id", "book", "damage_class"]).agg(
        k=("reward", "size"), mean=("reward", "mean"), std=("reward", lambda s: s.std(ddof=0)),
        min=("reward", "min"), max=("reward", "max"), pass_rate=("reward", lambda s: (s == 1.0).mean()),
        distinct=("reward", "nunique")).reset_index()
    g["has_signal"] = g["distinct"] > 1
    g.to_csv(out / "groups.csv", index=False)

    def tab(by):
        return g.groupby(by).agg(items=("item_id", "size"), signal_share=("has_signal", "mean"),
                                 mean_reward=("mean", "mean"), mean_std=("std", "mean"),
                                 pass_rate=("pass_rate", "mean"),
                                 all_pass=("pass_rate", lambda s: (s == 1).mean()),
                                 none_pass=("pass_rate", lambda s: (s == 0).mean())).round(3)
    cost = rw.groupby("model").agg(calls=("usd", "size"), usd=("usd", "sum"), out_tok=("output_tokens", "mean"),
                                   errors=("error", lambda s: (s != "").sum()))
    cost["usd_per_call"] = (cost.usd / cost.calls).round(5)
    cost["usd_per_page"] = (cost.usd / len(cfg["pages"])).round(4)
    cost["usd_per_item_k"] = (cost.usd / len(items)).round(4)
    fmt = ok.groupby("model").agg(format_invalid=("format_valid", lambda s: int((~s.astype(bool)).sum())),
                                  integrity_invalid=("integrity_valid", lambda s: int((~s.astype(bool)).sum())),
                                  stop_not_end_turn=("stop_reason", lambda s: int((s != "end_turn").sum())))
    reasons = ok[~ok.format_valid.astype(bool)].groupby(["model", "format_reason"]).size()
    lines = [f"# Task B trial `{run_id}`", "",
             f"Dev pages {', '.join(map(str, cfg['pages']))} ({len(items)} items); models {', '.join(cfg['models'])}; "
             f"K = {cfg['k']} samples per item; effort {cfg['effort']}; temperature {cfg['temperature']}; "
             f"prompt `{cfg['prompt_version']}`; {cfg['reward']}.", "",
             "**has_signal**: the K rewards of an item are not all equal, so GRPO's group-normalised advantage is "
             "not zero. These API models stand in for the small model to be trained; their signal share says "
             "whether the reward and item design can produce signal at all, not what the small model will see.", "",
             "## Cost", "", cost.round(4).to_markdown(), "",
             "## Format and stop reasons", "", fmt.to_markdown(), "",
             (reasons.to_frame("n").to_markdown() if len(reasons) else "No format failures."), "",
             "## Within-group signal per model", "", tab(["model"]).to_markdown(), "",
             "## By damage class", "", tab(["model", "damage_class"]).to_markdown(), "",
             "## By book", "", tab(["model", "book"]).to_markdown(), "",
             "## Pass-rate distribution (share of items)", "",
             pd.crosstab(g.model, pd.cut(g.pass_rate, [-0.01, 0, 0.1, 0.9, 0.99, 1.0],
                                         labels=["0", "(0, 0.1]", "(0.1, 0.9]", "(0.9, 1)", "1"]),
                         normalize="index").round(3).to_markdown(), "",
             "Items with a pass rate in (0.1, 0.9] are the plan's mid-difficulty band (plan 9).", ""]
    (out / "REPORT.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pages", default="pilot5", choices=["pilot5", "dev200"])
    ap.add_argument("--prompt", default=PROMPT_VERSION)
    ap.add_argument("--models", nargs="+", default=["claude-haiku-5-5", "claude-opus-5-5"])
    ap.add_argument("--k", type=int, default=8)
    ap.add_argument("--max-usd", type=float, default=4.0)
    ap.add_argument("--report")
    ap.add_argument("--dry-run", action="store_true", help="select items and print them; no API call")
    args = ap.parse_args()
    if args.report:
        report(args.report)
        return
    if args.dry_run:
        for it in (select_items() if args.pages == "pilot5" else select_dev200()):
            print(it["item_id"], it["book"], it["damage_class"], "|", it["input"][:70], "|", it["target"][:70])
        return
    report(run(args))


if __name__ == "__main__":
    main()
