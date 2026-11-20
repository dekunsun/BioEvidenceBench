"""Task B, step 4: build every training, development and in-book test unit of the five training
books (Cuvier is never touched), report alignment and damage per book, and draw the alignment
audit sample.

    python src/rl_task_b_build.py

Writes
  data/cache/taskb/units/{train,dev,intest}.jsonl   all units (regenerable; not committed)
  rl/env/task_b_ocr_repair/build/STATS.md            per-book statistics (committed)
  rl/env/task_b_ocr_repair/build/stats_*.csv
  rl/env/task_b_ocr_repair/build/audit_sample.csv    100 pairs for Claude's audit
  rl/env/task_b_ocr_repair/build/audit_gloria.xlsx   30 of them for Gloria, without Claude's verdicts
  rl/env/task_b_ocr_repair/build/piscium_long_s.csv  pages of Piscium querelae with and without ſ
No model is called.
"""
from __future__ import annotations

import hashlib
import json
import random
import re

import pandas as pd

import rl_task_b as T
from common import CACHE, ROOT

OUT = ROOT / "rl" / "env" / "task_b_ocr_repair" / "build"
UNITS = CACHE / "taskb" / "units"
SEED = 20261120
SPECIAL = re.compile(r"[æœÆŒſâêîôûàèìòùáéíóúäëïöüçß]")


def failure_flags(u: dict) -> list[str]:
    """Heuristic tags for the audit and the statistics (not used by the reward)."""
    f = []
    if u.get("coverage", 1) < 0.9:
        f.append("missing text")
    if not 0.6 <= u.get("span_ratio", 1) <= 1.6:
        f.append("span length off")
    if u.get("input_had_linebreak"):
        f.append("crosses OCR line break")
    if u["target"].rstrip().endswith(("-", "‐")):
        f.append("hyphen at line end")
    n_in, n_ref = len(T.words(u.get("input", ""))), u.get("n_words", 0)
    if n_in > n_ref:
        f.append("OCR splits words")
    if n_in < n_ref:
        f.append("OCR merges words")
    if SPECIAL.search(u["target"]):
        f.append("special characters")
    return f


def bucket(sim: float) -> str:
    return "<0.3" if sim < 0.3 else "0.3-0.5" if sim < 0.5 else "0.5-0.8" if sim < 0.8 else "0.8-1.0"


def damage_bin(n: int) -> str:
    return "0" if n == 0 else "1" if n == 1 else "2-5" if n <= 5 else ">5"


def main() -> None:
    splits = pd.read_csv(ROOT / "rl" / "env" / "task_b_ocr_repair" / "splits.csv")
    use = splits[splits.split.isin(["train", "dev", "intest"])]
    UNITS.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)
    rows, missing = [], []
    files = {s: (UNITS / f"{s}.jsonl").open("w", encoding="utf-8") for s in ("train", "dev", "intest")}
    for r in use.itertuples():
        try:
            units = T.line_pairs(int(r.PageID))
        except Exception as e:                       # no legacy OCR for this page, or no text
            missing.append({"page_id": r.PageID, "book": r.book, "error": repr(e)[:120]})
            continue
        for u in units:
            u.update({"book": r.book, "split": r.split, "block": r.block})
            u["flags"] = failure_flags(u)
            u["sim_bucket"] = bucket(u.get("similarity", 0.0)) if u.get("input") else "no text"
            if u.get("valid"):
                files[r.split].write(json.dumps(u, ensure_ascii=False) + "\n")
            rows.append({k: u.get(k) for k in ("book", "split", "page_id", "line_no", "valid", "why_invalid",
                                                "similarity", "sim_bucket", "coverage", "span_ratio", "n_words",
                                                "n_damaged", "n_name_damaged", "input", "target")}
                        | {"flags": "; ".join(u["flags"])})
    for f in files.values():
        f.close()
    d = pd.DataFrame(rows)
    d.to_csv(UNITS / "all_units_index.csv", index=False)

    v = d[d.valid == True]  # noqa: E712
    per_book = d.groupby("book").agg(pages=("page_id", "nunique"), lines=("line_no", "size"),
                                     valid=("valid", "sum")).assign(valid_share=lambda x: (x.valid / x.lines).round(3))
    sims = pd.crosstab(d.book, d.sim_bucket, margins=True)
    dmg = pd.crosstab(v.book, v.n_damaged.map(damage_bin), normalize="index").round(3)
    dmg_n = pd.crosstab(v.book, v.n_damaged.map(damage_bin), margins=True)
    names = v.groupby("book").agg(lines_with_damaged_name=("n_name_damaged", lambda s: int((s > 0).sum())))
    # what lowering the similarity floor from 0.5 to 0.3 added
    gain = d[(d.valid == True) & (d.similarity < 0.5)].groupby("book").size().rename("valid_only_at_0.3")  # noqa: E712
    flags = (d.assign(flag=d.flags.str.split("; ")).explode("flag").query("flag != ''")
             .pipe(lambda x: pd.crosstab(x.book, x.flag)))
    per_split = pd.crosstab(v.book, v.split)
    for name, t in [("per_book", per_book), ("similarity", sims), ("damage_share", dmg), ("damage_counts", dmg_n),
                    ("names", names), ("threshold_gain", gain.to_frame()), ("flags", flags), ("splits", per_split)]:
        t.to_csv(OUT / f"stats_{name}.csv")
    pd.DataFrame(missing).to_csv(OUT / "missing_pages.csv", index=False)

    # Piscium: is the long s used consistently?
    pis = splits[splits.book == "Piscium"].PageID.astype(int)
    pl = pd.DataFrame([{"page_id": p, "chars": len(T.expert_text(p)), "long_s": T.expert_text(p).count("ſ"),
                        "plain_s": T.expert_text(p).count("s")} for p in pis])
    pl.to_csv(OUT / "piscium_long_s.csv", index=False)

    # audit sample: 100 pairs, low-confidence and special characters first, every book represented
    rng = random.Random(SEED)
    pool = d[d.input.fillna("") != ""].copy()
    want = {"0.3-0.5": 35, "<0.3": 10, "0.5-0.8": 30, "0.8-1.0": 25}
    picked = []
    for b, n in want.items():
        sub = pool[pool.sim_bucket == b]
        sub = sub.sort_values(["book", "page_id", "line_no"])
        books = sorted(sub.book.unique())
        per = max(1, n // max(1, len(books)))
        take = []
        for bk in books:
            s2 = sub[sub.book == bk]
            spec = s2[s2.flags.str.contains("special")]
            cand = list(spec.index) + list(s2.index.difference(spec.index))
            take += rng.sample(cand[:max(per * 3, per)], min(per, len(cand)))
        rest = list(sub.index.difference(take))
        take += rng.sample(rest, max(0, min(n - len(take), len(rest))))
        picked += take[:n]
    audit = pool.loc[picked, ["book", "split", "page_id", "line_no", "similarity", "sim_bucket", "valid",
                              "flags", "input", "target"]].reset_index(drop=True)
    audit.insert(0, "audit_id", [f"A{i + 1:03d}" for i in range(len(audit))])
    for c in ("claude_verdict", "claude_failure_type", "claude_note"):
        audit[c] = ""
    audit.to_csv(OUT / "audit_sample.csv", index=False)
    g_ids = rng.sample(list(audit.index), 30)
    ga = audit.loc[sorted(g_ids), ["audit_id", "book", "page_id", "line_no", "input", "target"]].copy()
    ga["page_url"] = ga.page_id.map(lambda p: f"https://www.biodiversitylibrary.org/page/{p}")
    for c in ("aligned_correctly (yes/no/partly)", "failure_type", "note"):
        ga[c] = ""
    ga.to_excel(OUT / "audit_gloria.xlsx", index=False)

    digest = {s: hashlib.sha256((UNITS / f"{s}.jsonl").read_bytes()).hexdigest() for s in ("train", "dev", "intest")}
    lines = ["# Task B step 4: units, alignment and damage per book", "",
             f"Built by `src/rl_task_b_build.py` with Reward v1.1 rules. Cuvier (held-out book) not touched; "
             f"the 38 excluded pages not used. Pages without legacy OCR: {len(missing)}.", "",
             "Unit files (not committed; regenerate with the script) and their SHA-256:", ""]
    lines += [f"- `{s}.jsonl`: {int((v.split == s).sum())} valid units, `{h[:16]}…`" for s, h in digest.items()]
    lines += ["", "## Alignment per book", "", per_book.to_markdown(), "",
              "## Similarity buckets (all lines, valid or not)", "", sims.to_markdown(), "",
              "Lines that are valid only because the similarity floor is 0.3, not 0.5:", "",
              gain.to_frame().to_markdown(), "",
              "## Damaged words per valid line (share)", "", dmg.to_markdown(), "",
              "Counts:", "", dmg_n.to_markdown(), "",
              "## Lines with a damaged scientific-name word", "", names.to_markdown(), "",
              "## Heuristic flags (all lines)", "", flags.to_markdown(), "",
              "## Valid units per split", "", per_split.to_markdown(), "",
              "## Long s in *Piscium querelae*", "",
              f"{int((pl.long_s > 0).sum())} of {len(pl)} pages contain ſ; pages without ſ have median "
              f"{int(pl[pl.long_s == 0].chars.median()) if (pl.long_s == 0).any() else 0} characters "
              f"(pages with ſ: {int(pl[pl.long_s > 0].chars.median())}). See `piscium_long_s.csv`.", ""]
    (OUT / "STATS.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
