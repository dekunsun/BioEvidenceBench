"""Task B, step 4: build every training, development and in-book test unit of the five training
books (Cuvier is never touched), report alignment and damage per book, and draw the alignment
audit sample.

    python src/rl_task_b_build.py               # stage 1 (align all pages, ~30 min) + stage 2
    python src/rl_task_b_build.py --stats-only  # stage 2 only, from the saved units (seconds)

Stage 1 aligns every content page of split v2 (`splits_v2.csv`) and writes all its lines, valid
or not, to data/cache/taskb/units/all_units.jsonl. Stage 2 applies the split and the exclusion
list and writes
  data/cache/taskb/units/{train,dev,intest}.jsonl   usable units (regenerable; not committed)
  data/cache/taskb/units/set_aside.jsonl            every line not used, with page, line and reason
  rl/env/task_b_ocr_repair/build/STATS.md            per-book statistics (committed)
  rl/env/task_b_ocr_repair/build/stats_*.csv, set_aside_summary.csv
  rl/env/task_b_ocr_repair/build/audit_sample.csv    100 pairs for Claude's audit
  rl/env/task_b_ocr_repair/build/audit_gloria.xlsx   30 of them for Gloria, without Claude's verdicts
  rl/env/task_b_ocr_repair/build/piscium_long_s.csv  pages of Piscium querelae with and without ſ
No model is called.

Exclusions (Gloria, 2026-11-20): engraved imprints and plate captions whose OCR AND expert
transcription are both unreliable are set aside from task B v1 (`exclusions.csv`, one row per
line, with the reason). Plate captions that align reliably and whose reference reads normally stay.
Badly damaged OCR alone is never a reason to exclude a line.
"""
from __future__ import annotations

import hashlib
import json
import random
import re
import sys

import pandas as pd

import rl_task_b as T
from common import CACHE, ROOT

ENV = ROOT / "rl" / "env" / "task_b_ocr_repair"
OUT = ENV / "build"
UNITS = CACHE / "taskb" / "units"
SPLITS = ENV / "splits_v2.csv"
EXCLUSIONS = ENV / "exclusions.csv"
# Round 1 of the alignment audit used seed 20261120 on the build before the MUFI and case fixes
# (kept in build/audit_round1/); round 2 draws a fresh sample from the fixed build so the fixes are
# not checked on the pairs that found them.
AUDIT_SEED = 20261121
SPECIAL = re.compile(r"[æœÆŒſâêîôûàèìòùáéíóúäëïöüçß]")
SPLIT_NAMES = ("train", "dev", "intest")


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
    if u.get("n_case_only"):
        f.append("case-only words")
    return f


def bucket(sim: float) -> str:
    return "<0.3" if sim < 0.3 else "0.3-0.5" if sim < 0.5 else "0.5-0.8" if sim < 0.8 else "0.8-1.0"


def damage_bin(n: int) -> str:
    return "0" if n == 0 else "1" if n == 1 else "2-5" if n <= 5 else ">5"


def why_no_lines(pid: int) -> str:
    """Why a page gave no unit (all such pages so far: plates, blank pages, short captions)."""
    if not T.expert_text(pid).strip():
        return "expert transcription empty (plate or blank page)"
    if not T.legacy_text(pid).strip():
        return "legacy OCR empty"
    return "only lines under 15 characters or 2 words (caption)"


# ---------------------------------------------------------------- stage 1
def align_all(pages: pd.DataFrame) -> None:
    """Align every page and keep every line, valid or not (slow: about 30 minutes)."""
    with (UNITS / "all_units.jsonl").open("w", encoding="utf-8") as fh:
        for r in pages.itertuples():
            pid = int(r.PageID)
            try:
                units = T.line_pairs(pid)
                why = "" if units else why_no_lines(pid)
            except Exception as e:                   # recorded, never silently dropped
                units, why = [], "error " + repr(e)[:120]
            if why:
                fh.write(json.dumps({"page_id": pid, "no_lines": why}, ensure_ascii=False) + "\n")
            for u in units:
                fh.write(json.dumps(u, ensure_ascii=False) + "\n")


# ---------------------------------------------------------------- stage 2
def assemble(split: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    info = split.set_index("PageID")
    excl = pd.read_csv(EXCLUSIONS) if EXCLUSIONS.exists() else pd.DataFrame(columns=["page_id", "line_no", "reason"])
    excl_reason = {(int(a), int(b)): c for a, b, c in zip(excl.page_id, excl.line_no, excl.reason)}
    rows, missing = [], []
    files = {s: (UNITS / f"{s}.jsonl").open("w", encoding="utf-8") for s in SPLIT_NAMES}
    aside = (UNITS / "set_aside.jsonl").open("w", encoding="utf-8")
    for line in (UNITS / "all_units.jsonl").open(encoding="utf-8"):
        u = json.loads(line)
        pid = u["page_id"]
        if pid not in info.index or info.at[pid, "split"] not in SPLIT_NAMES:
            continue
        book, sp, block = info.at[pid, "book"], info.at[pid, "split"], int(info.at[pid, "block"])
        if "no_lines" in u:
            missing.append({"page_id": pid, "book": book, "split": sp, "error": u["no_lines"]})
            continue
        u.update({"book": book, "split": sp, "block": block})
        u["flags"] = failure_flags(u)
        u["sim_bucket"] = bucket(u.get("similarity", 0.0)) if u.get("input") else "no text"
        if u.get("valid") and T.mixed_script_words(u["target"]):   # rules added after stage 1 ran
            u.update(valid=False, why_invalid="mixed-script word in reference")
        if u.get("valid") and T.LEADERS.search(u["target"]):
            u.update(valid=False, why_invalid="index/contents line with leader dots")
        u["set_aside"] = excl_reason.get((pid, u["line_no"]), "") if u.get("valid") else u.get("why_invalid", "")
        (files[sp] if u.get("valid") and not u["set_aside"] else aside).write(json.dumps(u, ensure_ascii=False) + "\n")
        rows.append({k: u.get(k) for k in ("book", "split", "page_id", "line_no", "valid", "why_invalid", "set_aside",
                                            "similarity", "sim_bucket", "coverage", "span_ratio", "n_words",
                                            "n_damaged", "n_damaged_reading", "n_case_only", "n_name_damaged", "input", "target")}
                    | {"flags": "; ".join(u["flags"])})
    for f in [*files.values(), aside]:
        f.close()
    d = pd.DataFrame(rows)
    d["usable"] = d.valid.astype(bool) & (d.set_aside.fillna("") == "")
    d.to_csv(UNITS / "all_units_index.csv", index=False)
    return d, pd.DataFrame(missing, columns=["page_id", "book", "split", "error"])


def reason_group(s: str) -> str:
    if not s:
        return ""
    if s.startswith("excluded:"):
        return s
    parts = [re.sub(r" [\d.]+$", "", p) for p in s.split("; ")]
    return " + ".join(sorted(set(parts)))


def main() -> None:
    split = pd.read_csv(SPLITS)
    UNITS.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)
    if "--stats-only" not in sys.argv:
        align_all(split[split.split.isin(SPLIT_NAMES)])
    d, missing = assemble(split)

    v = d[d.usable]
    per_book = d.groupby("book").agg(pages=("page_id", "nunique"), lines=("line_no", "size"),
                                     valid=("valid", "sum"), usable=("usable", "sum")) \
        .assign(usable_share=lambda x: (x.usable / x.lines).round(3))
    sims = pd.crosstab(d.book, d.sim_bucket, margins=True)
    dmg = pd.crosstab(v.book, v.n_damaged.map(damage_bin), normalize="index").round(3)
    dmg_n = pd.crosstab(v.book, v.n_damaged.map(damage_bin), margins=True)
    words = v.groupby("book").agg(words=("n_words", "sum"), damaged=("n_damaged", "sum"),
                                  damaged_reading=("n_damaged_reading", "sum"),
                                  case_only=("n_case_only", "sum"),
                                  lines_with_damaged_name=("n_name_damaged", lambda s: int((s > 0).sum())))
    words["case_only_mismatch_rate"] = (words.case_only / words.words).round(4)
    words["damaged_rate"] = (words.damaged / words.words).round(4)
    words["damaged_rate_reading"] = (words.damaged_reading / words.words).round(4)   # ſ ≡ s
    gain = d[d.usable & (d.similarity < 0.5)].groupby("book").size().rename("usable_only_at_0.3")
    ex = d.assign(flag=d["flags"].fillna("").str.split("; ")).explode("flag").reset_index(drop=True)
    flags = pd.crosstab(ex.book, ex.flag).drop(columns="", errors="ignore")
    per_split = pd.crosstab(v.book, v.split, margins=True)
    aside = d[~d.usable].assign(reason=lambda x: x.set_aside.fillna("").map(reason_group))
    aside_sum = pd.crosstab(aside.reason, aside.book, margins=True)
    for name, t in [("per_book", per_book), ("similarity", sims), ("damage_share", dmg), ("damage_counts", dmg_n),
                    ("words", words), ("threshold_gain", gain.to_frame()), ("flags", flags), ("splits", per_split)]:
        t.to_csv(OUT / f"stats_{name}.csv")
    aside_sum.to_csv(OUT / "set_aside_summary.csv")
    missing.to_csv(OUT / "missing_pages.csv", index=False)

    # Piscium: is the long s used consistently?
    pis = split[split.book == "Piscium"].PageID.astype(int)
    pl = pd.DataFrame([{"page_id": p, "chars": len(T.expert_text(p)), "long_s": T.expert_text(p).count("ſ"),
                        "plain_s": T.expert_text(p).count("s")} for p in pis])
    pl.to_csv(OUT / "piscium_long_s.csv", index=False)

    if audit_is_recorded():
        print("audit_sample.csv already holds verdicts: the audit is a record and is not redrawn")
    else:
        draw_audit(d)
    write_stats(split, d, missing, v, per_book, sims, dmg, dmg_n, words, gain, flags, per_split, aside_sum, pl)


def audit_is_recorded() -> bool:
    f = OUT / "audit_sample.csv"
    return f.exists() and pd.read_csv(f).claude_verdict.fillna("").astype(str).str.len().gt(0).any()


def draw_audit(d: pd.DataFrame) -> None:
    # audit sample: 100 pairs over similarity buckets (low-confidence buckets weighted up), every book
    # represented, drawn uniformly within book x bucket. Pairs audited in round 1 are left out, so
    # round 2 is an independent check of the fixed build. (Round 1 drew from a fixed window with
    # special characters first, which made the two rounds overlap by 34 pairs.)
    rng = random.Random(AUDIT_SEED)
    r1_path = OUT / "audit_round1" / "audit_sample_round1_claude.csv"
    r1 = set(zip(*pd.read_csv(r1_path)[["page_id", "line_no"]].values.T)) if r1_path.exists() else set()
    pool = d[(d.input.fillna("") != "") & ~pd.Series(list(zip(d.page_id, d.line_no)), index=d.index).isin(r1)].copy()
    want = {"0.3-0.5": 35, "<0.3": 10, "0.5-0.8": 30, "0.8-1.0": 25}
    picked = []
    for b, n in want.items():
        sub = pool[pool.sim_bucket == b].sort_values(["book", "page_id", "line_no"])
        books = sorted(sub.book.unique())
        per = max(1, n // max(1, len(books)))
        take = []
        for bk in books:
            cand = list(sub[sub.book == bk].index)
            take += rng.sample(cand, min(per, len(cand)))
        rest = list(sub.index.difference(take))
        take += rng.sample(rest, max(0, min(n - len(take), len(rest))))
        picked += take[:n]
    audit = pool.loc[picked, ["book", "split", "page_id", "line_no", "similarity", "sim_bucket", "valid", "usable",
                              "set_aside", "flags", "input", "target"]].reset_index(drop=True)
    audit.insert(0, "audit_id", [f"B{i + 1:03d}" for i in range(len(audit))])
    vcols = ("claude_verdict", "claude_failure_type", "claude_note")
    for c in vcols:
        audit[c] = ""
    old_path = OUT / "audit_sample.csv"
    if old_path.exists():                  # keep verdicts already written for the same sample
        old = pd.read_csv(old_path)
        if list(zip(old.page_id, old.line_no)) == list(zip(audit.page_id, audit.line_no)):
            for c in vcols:
                if c in old:
                    audit[c] = old[c].fillna("").values
    audit.to_csv(old_path, index=False)
    g_ids = rng.sample(list(audit.index), 30)
    ga = audit.loc[sorted(g_ids), ["audit_id", "book", "page_id", "line_no", "input", "target"]].copy()
    ga["page_url"] = ga.page_id.map(lambda p: f"https://www.biodiversitylibrary.org/page/{p}")
    for c in ("aligned_correctly (yes/no/partly)", "failure_type", "note"):
        ga[c] = ""
    howto = pd.DataFrame({"说明": [
        "每行是一对：target = 专家转录的一行；input = 对齐程序找到的旧 OCR 片段。",
        "请判断：input 是不是 target 这一行的 OCR（同一处文字），而不是 OCR 好不好。",
        "yes = 同一行（OCR 错得再多也算 yes）；partly = 只对上一部分（缺词、多了相邻行或另一栏的词）；no = 不是同一行。",
        "failure_type 可写：wrong line / column / missing words / extra words / leaders (点线和页码) / reference error (专家转录本身有错) / other。",
        "需要时点 page_url 看 BHL 原页扫描。可以只看拿不准的行。",
        "这 30 对里有一半是程序接受的、一半是拒绝的；表里不显示程序的决定和 Claude 的判断，请独立判断。"]})
    with pd.ExcelWriter(OUT / "audit_gloria.xlsx") as xw:
        ga.to_excel(xw, sheet_name="pairs", index=False)
        howto.to_excel(xw, sheet_name="说明", index=False)



def write_stats(split, d, missing, v, per_book, sims, dmg, dmg_n, words, gain, flags, per_split, aside_sum, pl) -> None:
    digest = {s: hashlib.sha256((UNITS / f"{s}.jsonl").read_bytes()).hexdigest() for s in SPLIT_NAMES}
    why_missing = missing.error.str.replace(r" \(.*", "", regex=True).value_counts()
    lines = ["# Task B step 4: units, alignment and damage per book", "",
             "Built by `src/rl_task_b_build.py` under Reward v1.2 rules (case-only words neutral, MUFI "
             "ligatures folded, references with U+FFFD or unidentified private-use characters invalid, lines with a mixed "
             "Latin/Cyrillic word or leader dots set aside) "
             "and split v2 (`../SPLIT_V2.md`). Cuvier (held-out book) not touched; the 38 excluded pages "
             f"not used. Content pages that gave no line: {len(missing)} "
             f"({', '.join(f'{k}: {n}' for k, n in why_missing.items()) or 'none'}; `missing_pages.csv`).", "",
             "**Coverage is not accuracy.** `usable` counts lines that passed the automatic checks; whether "
             "they are paired correctly is measured by the audits (`audit_round1/`, `audit_sample.csv`).", "",
             "Unit files (not committed; regenerate with the script) and their SHA-256:", ""]
    lines += [f"- `{s}.jsonl`: {int((v.split == s).sum())} usable units, `{h[:16]}…`" for s, h in digest.items()]
    lines += ["", "## Lines per book", "", per_book.to_markdown(), "",
              "## Lines not used, by reason", "",
              "Every one is kept with page, line, input, target and reason in `set_aside.jsonl` (cache) "
              "for a later hard-case set.", "", aside_sum.to_markdown(), "",
              "## Similarity buckets (all lines; similarity ignores case)", "", sims.to_markdown(), "",
              "Usable lines with similarity 0.3-0.5 (would be rejected under a 0.5 floor):", "",
              gain.to_frame().to_markdown(), "",
              "## Damaged and case-only words (usable lines)", "",
              "Case-only words are neutral in Reward v1.2: not damaged, not penalised for case.", "",
              words.to_markdown(), "",
              "## Damaged words per usable line (share)", "", dmg.to_markdown(), "",
              "Counts:", "", dmg_n.to_markdown(), "",
              "## Heuristic flags (all lines)", "", flags.to_markdown(), "",
              "## Usable units per split", "", per_split.to_markdown(), "",
              "## Long s in *Piscium querelae*", "",
              f"{int((pl.long_s > 0).sum())} of {len(pl)} pages contain ſ. The pages without it are blank "
              "pages, the title page, a modern bookplate and an all-caps dedication (capital S has no long "
              "form): the transcription uses ſ consistently. See `piscium_long_s.csv`.", ""]
    (OUT / "STATS.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
