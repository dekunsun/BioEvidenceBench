"""Exploratory (DEVIATIONS.md): the released SFT repair model inside the extraction pipeline.

    python src/sft_repair_pipeline.py build      # legacy OCR lines of the 22 sample pages -> line file for the pod
    python src/sft_repair_pipeline.py assemble   # pod output -> repaired pages, page CER, name preservation
    python src/sft_repair_pipeline.py report     # + Opus G1 value F1 on the 16 test pages, against the other routes

Question (Gloria, 2026-11-21, item 4): if BHL's legacy OCR is first repaired line by line with the released
research checkpoint (`rl-sft-ocr-repair-v1`, Qwen3-0.6B SFT seed 2), how much of the extraction loss does it
recover, compared with re-OCR (dots.mocr) and with Opus repairing while it extracts (G2)?

Rules fixed before the run (results/sft_repair_pipeline/PLAN.md):
- every line of the legacy OCR page with at least 15 characters and 2 words is repaired; shorter lines are kept
  as they are (the training data had no such lines);
- context = the nearest non-empty OCR line above and below on the same page, as in training;
- prompt `repair_v3`, thinking off, greedy decoding (temperature 0), at most 128 new tokens;
- the answer goes through the fixed clean-up (`format_cleanup`); if it is empty or its length is outside
  0.5-1.5x the OCR line, the OCR line is kept (a pipeline needs a safe fallback); how often is reported;
- page structure (line breaks, blank lines) is kept, only line contents change;
- extraction: the frozen G1 prompt `p4-guide-v0.6`, Claude Opus 5.5, batch, the 16 test pages, scored by
  score.py against the frozen test gold; the test pages were unsealed on 2026-11-20, so this is exploratory.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd
import rapidfuzz.distance.Levenshtein as Lev

from common import DATA, ROOT, normalize_for_cer

VERSION = "legacy_sft-repair"
LINES = ROOT / "rl" / "training" / "data" / "legacy_sample_lines.jsonl"
OUT = ROOT / "results" / "sft_repair_pipeline"
MIN_CHARS, MIN_WORDS = 15, 2


def build() -> None:
    split = pd.read_csv(DATA / "sample_split.csv")
    rows = []
    for r in split.itertuples():
        pid = int(r.PageID)
        lines = (DATA / "sample" / "legacy" / f"{pid}.txt").read_text(encoding="utf-8").split("\n")
        filled = [i for i, l in enumerate(lines) if l.strip()]
        for i, l in enumerate(lines):
            t = l.strip()
            if not t:
                continue
            before = [lines[j].strip() for j in filled if j < i]
            after = [lines[j].strip() for j in filled if j > i]
            rows.append({"item_id": f"{pid}-{i}", "page_id": pid, "line_idx": i, "book": r.book, "split": r.split,
                         "input": t, "prev": before[-1] if before else "(none)", "next": after[0] if after else "(none)",
                         "repair": len(t) >= MIN_CHARS and len(t.split()) >= MIN_WORDS})
    LINES.parent.mkdir(parents=True, exist_ok=True)
    with LINES.open("w", encoding="utf-8") as f:
        for x in rows:
            f.write(json.dumps(x, ensure_ascii=False) + "\n")
    d = pd.DataFrame(rows)
    print(len(d), "lines,", int(d.repair.sum()), "to repair, pages", d.page_id.nunique())


def assemble(pod_out: Path) -> None:
    sys.path.insert(0, str(ROOT / "src"))
    from score import char_map, map_span, norm_value
    rep = {r["item_id"]: r for r in map(json.loads, pod_out.open(encoding="utf-8"))}
    split = pd.read_csv(DATA / "sample_split.csv")
    dest = DATA / "text" / VERSION
    dest.mkdir(parents=True, exist_ok=True)
    gold = pd.concat([pd.read_csv(ROOT / "gold" / f) for f in ("gold_mentions_gloria.csv", "gold_mentions_gloria_test.csv")])
    gold = gold[gold.get("adjudication", pd.Series(index=gold.index, dtype=str)).fillna("") != "excluded"]
    gold["scan_text"] = gold.get("scan_text", pd.Series(index=gold.index, dtype=str)).fillna("")
    page_rows, ment_rows = [], []
    for r in split.itertuples():
        pid = int(r.PageID)
        legacy = (DATA / "sample" / "legacy" / f"{pid}.txt").read_text(encoding="utf-8")
        lines = legacy.split("\n")
        for i, l in enumerate(lines):
            x = rep.get(f"{pid}-{i}")
            if x is not None:
                lines[i] = x["final"]
        repaired = "\n".join(lines)
        (dest / f"{pid}.txt").write_text(repaired, encoding="utf-8")
        expert = (DATA / "sample" / "expert" / f"{pid}.txt").read_text(encoding="utf-8")
        ref = normalize_for_cer(expert).lower()
        for name, text in (("legacy (BHL)", legacy), ("legacy + SFT repair", repaired)):
            page_rows.append({"version": name, "page_id": pid, "book": r.book, "split": r.split,
                              "page_cer": round(Lev.distance(normalize_for_cer(text).lower(), ref) / max(len(ref), 1), 4)})
            cmap = char_map(expert, text)
            for gm in gold[gold.page_id == pid].itertuples():
                span = map_span(cmap, gm.start, gm.end)
                aligned = sum(cmap[k] >= 0 for k in range(gm.start, min(gm.end, len(cmap))))
                missing = span is None or aligned < 0.5 * (gm.end - gm.start)
                sub = "" if missing else text[span[0]:span[1]]
                ok = (not missing) and (norm_value(sub) == norm_value(gm.text)
                                        or (gm.scan_text and norm_value(sub) == norm_value(gm.scan_text)))
                ment_rows.append({"version": name, "page_id": pid, "book": r.book, "split": r.split, "field": gm.field,
                                  "gold_text": gm.text, "text_at_place": sub, "preserved": bool(ok)})
    pg, mt = pd.DataFrame(page_rows), pd.DataFrame(ment_rows)
    OUT.mkdir(parents=True, exist_ok=True)
    pg.to_csv(OUT / "pages.csv", index=False)
    mt.to_csv(OUT / "mentions.csv", index=False)
    prim = mt[mt.field.isin(["taxon", "person", "locality", "institution", "date"])]
    s = pg.groupby(["version", "book"]).page_cer.median().rename("median_page_cer").to_frame() \
        .join(prim.groupby(["version", "book"]).preserved.mean().rename("names_and_values_preserved")) \
        .join(prim[prim.field == "taxon"].groupby(["version", "book"]).preserved.mean().rename("taxa_preserved"))
    lines = pd.DataFrame(rep.values())
    stats = {"lines": len(lines), "repaired_lines": int(lines.repair.sum()),
             "changed": int((lines.final != lines.input).sum()),
             "fallback_kept_ocr": int(lines.fallback.sum()) if "fallback" in lines else None}
    s.round(4).to_csv(OUT / "summary.csv")
    (OUT / "line_stats.json").write_text(json.dumps(stats, indent=1))
    print(s.round(4).to_string())
    print(stats)


RUN = "20261121-sftrepair_claude-opus-5-5_test_G1"
FROZEN = "20261119-2052_claude-opus-5-5_test_batch"       # G1 on legacy and dots.mocr (frozen test run)
GOLD = ROOT / "gold" / "gold_mentions_gloria_test.csv"


def _f1(tp, fp, fn) -> float:
    return 2 * tp / max(1, 2 * tp + fp + fn)


def report(n_boot: int = 10000) -> None:
    """Value F1 (ALL_PRIMARY, G1) of the repaired text against legacy and dots.mocr, plus a paired page
    bootstrap of repaired - legacy per book; Opus G2 on legacy is copied from results/exploratory_conditions."""
    import numpy as np
    from score import score_run_detail
    parts, pages = [], []
    for run in (FROZEN, RUN):
        d = score_run_detail(run, GOLD, "test")
        s, bp = d["summary"], d["by_page"]
        keep = lambda x: x[(x.condition == "G1") & (x.field == "ALL_PRIMARY")
                           & x.version.isin(["legacy", "modern_dots-mocr", VERSION])]
        parts.append(keep(s))
        bp = bp[(bp.condition == "G1") & bp.field.isin(["taxon", "person", "locality", "institution", "date"])
                & bp.version.isin(["legacy", VERSION])]
        pages.append(bp.groupby(["book", "version", "page_id"], as_index=False)[["value_tp", "value_fp", "value_fn"]].sum())
    s, bp = pd.concat(parts), pd.concat(pages)
    rows = [{"route": v, "book": r.book, "value_F1": r.value_F1, "lo": r.value_F1_lo, "hi": r.value_F1_hi,
             "value_P": r.value_P, "value_R": r.value_R}
            for v, r in ((r.version, r) for r in s.itertuples())]
    g2 = pd.read_csv(ROOT / "results" / "exploratory_conditions" / "position_scores.csv")
    for r in g2[g2.condition.isin(["G2 · legacy", "G2 [haiku-5-5] · legacy"])].itertuples():
        rows.append({"route": "opus_G2_on_legacy" if "haiku" not in r.condition else "haiku_G2_on_legacy",
                     "book": r.book, "value_F1": r.value_F1, "lo": r.value_F1_lo, "hi": r.value_F1_hi})
    tab = pd.DataFrame(rows)
    rng = np.random.default_rng(20261121)
    diffs = []
    for book, g in bp.groupby("book"):
        a = g[g.version == "legacy"].set_index("page_id")[["value_tp", "value_fp", "value_fn"]]
        b = g[g.version == VERSION].set_index("page_id")[["value_tp", "value_fp", "value_fn"]].loc[a.index]
        A, B = a.to_numpy(), b.to_numpy()
        point = _f1(*B.sum(0)) - _f1(*A.sum(0))
        boots = []
        for _ in range(n_boot):
            i = rng.integers(0, len(A), len(A))
            boots.append(_f1(*B[i].sum(0)) - _f1(*A[i].sum(0)))
        lo, hi = np.percentile(boots, [2.5, 97.5])
        diffs.append({"book": book, "pages": len(A), "repaired_minus_legacy": round(point, 3),
                      "lo": round(lo, 3), "hi": round(hi, 3)})
    dif = pd.DataFrame(diffs)
    tab.round(3).to_csv(OUT / "extraction.csv", index=False)
    dif.to_csv(OUT / "extraction_diff.csv", index=False)
    print(tab.round(3).to_string(index=False))
    print(dif.to_string(index=False))


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "build":
        build()
    elif cmd == "assemble":
        assemble(Path(sys.argv[2]))
    elif cmd == "report":
        report()
