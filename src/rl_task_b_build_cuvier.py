"""Task B: build the held-out book (Cuvier) with the automatic rules of the in-book build.

    python src/rl_task_b_build_cuvier.py

Cuvier, *Histoire naturelle des poissons*, t. 10 (1835; BHL item 25923, language FRE in the BHL
metadata) is the held-out book of split v2: never used for training, development or the alignment
audits. This builds its units once, when the module-7b test protocol is frozen
(`rl/training/configs/TEST_PROTOCOL.md`).

Same code and rules as `rl_task_b_build.py`: `rl_task_b.line_pairs` (alignment, validity), then
mixed-script words, leader-dot lines and unrecoverable deletions set aside, recoverable deletions
kept and marked, context = the nearest OCR line above and below. What the in-book build had and
Cuvier does not: no manual exclusions and no reference-typo check against the scan (nobody has
read the book), so Cuvier may keep a few lines the in-book rules would have set aside by hand.

Writes data/cache/taskb/units/cuvier.jsonl (usable), cuvier_set_aside.jsonl, cuvier_all_units.jsonl
(not committed: regenerable), and rl/env/task_b_ocr_repair/build/STATS_CUVIER.md with counts only.
It prints counts, never text.
"""
from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor

import pandas as pd

import rl_task_b as T
from rl_task_b_build import OUT, SPLITS, UNITS, bucket, failure_flags, reason_group, why_no_lines


def align(pid: int) -> list[dict]:
    try:
        units = T.line_pairs(pid)
        why = "" if units else why_no_lines(pid)
    except Exception as e:  # noqa: BLE001 (recorded, never dropped silently)
        units, why = [], "error " + repr(e)[:120]
    return [{"page_id": pid, "no_lines": why}] if why else units


def main() -> None:
    split = pd.read_csv(SPLITS)
    pages = split[split.book == "Cuvier"].PageID.astype(int).tolist()
    assert len(pages) == 516
    with ThreadPoolExecutor(8) as ex:               # legacy OCR is fetched from BHL page by page
        results = list(ex.map(align, pages))
    all_u = [u for us in results for u in us]
    with (UNITS / "cuvier_all_units.jsonl").open("w", encoding="utf-8") as f:
        for u in all_u:
            f.write(json.dumps(u, ensure_ascii=False) + "\n")

    by_page: dict[int, list[tuple[int, str]]] = {}
    for x in all_u:
        if "line_no" in x and (x.get("input") or "").strip():
            by_page.setdefault(x["page_id"], []).append((x["line_no"], x["input"]))

    def context(pid: int, ln: int) -> tuple[str, str]:
        lines = sorted(by_page.get(pid, []))
        before = [t for n, t in lines if n < ln]
        after = [t for n, t in lines if n > ln]
        return (before[-1] if before else "", after[0] if after else "")

    rows, missing = [], []
    ok_f = (UNITS / "cuvier.jsonl").open("w", encoding="utf-8")
    aside_f = (UNITS / "cuvier_set_aside.jsonl").open("w", encoding="utf-8")
    for u in all_u:
        pid = u["page_id"]
        if "no_lines" in u:
            missing.append({"page_id": pid, "error": u["no_lines"]})
            continue
        u.update({"book": "Cuvier", "split": "heldout_book", "block": -1})
        u["flags"] = failure_flags(u)
        u["sim_bucket"] = bucket(u.get("similarity", 0.0)) if u.get("input") else "no text"
        if u.get("valid") and T.mixed_script_words(u["target"]):
            u.update(valid=False, why_invalid="mixed-script word in reference")
        if u.get("valid") and T.LEADERS.search(u["target"]):
            u.update(valid=False, why_invalid="index/contents line with leader dots")
        u["recoverable_deletion"] = []
        if u.get("valid"):
            rec, unrec = T.classify_deletions(u["target"], u["input"], *context(pid, u["line_no"]))
            u["recoverable_deletion"] = rec
            if rec:
                u["flags"].append("recoverable deletion")
            if unrec:
                u.update(valid=False, why_invalid="unrecoverable deletion (word not in OCR or context)")
        u["set_aside"] = "" if u.get("valid") else u.get("why_invalid", "")
        (ok_f if u.get("valid") else aside_f).write(json.dumps(u, ensure_ascii=False) + "\n")
        rows.append({k: u.get(k) for k in ("page_id", "line_no", "valid", "why_invalid", "sim_bucket", "n_words",
                                            "n_damaged", "n_name_damaged")})
    ok_f.close()
    aside_f.close()
    d = pd.DataFrame(rows)
    v = d[d.valid.astype(bool)]
    why = d[~d.valid.astype(bool)].why_invalid.fillna("").map(reason_group).value_counts()
    md = ["# Cuvier (held-out book): build statistics", "",
          "*`src/rl_task_b_build_cuvier.py`; counts only, no text was displayed.*", "",
          f"- Pages: {len(pages)}; pages without units: {len(missing)}",
          f"- Lines aligned: {len(d)}; usable: {len(v)} on {v.page_id.nunique()} pages",
          f"- Usable lines with a damaged word: {int((v.n_damaged > 0).sum())}; with a damaged name word: "
          f"{int((v.n_name_damaged > 0).sum())}; words {int(v.n_words.sum())}, damaged {int(v.n_damaged.sum())}", "",
          "Set aside (reason, lines):", "", why.to_frame("lines").to_markdown(), "",
          "Pages without units:", "",
          pd.DataFrame(missing).error.str[:60].value_counts().to_frame("pages").to_markdown() if missing else "none", ""]
    (OUT / "STATS_CUVIER.md").write_text("\n".join(md), encoding="utf-8")
    print("\n".join(md))


if __name__ == "__main__":
    main()
