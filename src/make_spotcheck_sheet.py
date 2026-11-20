"""Spot-check sheet for the whole-book run (exploratory, DEVIATIONS.md).

    python src/make_spotcheck_sheet.py <opus book run> <haiku book run> [--n 140]
    python src/make_spotcheck_sheet.py --score        # after Gloria returns the filled sheet

Pages: the book pages outside the 22-page sample (no gold there). Every Opus mention gets the
RQ4 tier with Haiku as the second model (analysis.flag_auto_accept: same page and field,
overlapping characters, clean evidence, type check), plus the cheap OCR-junk signal. Strata:
  A  tier 0 (both models agree, checks pass): "proposed auto-accept"
  B  Opus only, or a check failed (tiers 1-3)
  C  Haiku extracted it and Opus did not: a sample of what Opus may have missed
A random sample per stratum (seed fixed) is shuffled into one sheet; the stratum is NOT shown
(kept in the key file) so the checker is not primed. These are MODEL outputs to verify against
the scan, never gold labels (CLAUDE.md rule 1); the sheet lives in results/, not gold/.
Writes results/book_spotcheck/spotcheck_sheet.xlsx (+ .csv), spotcheck_key.csv, strata.csv.
With --score: precision per stratum with a Wilson interval, and a whole-book precision estimate
weighted by stratum size.
"""
from __future__ import annotations

import argparse
import math
import re
import sys

import pandas as pd

from analysis import flag_auto_accept
from common import ROOT
from review_signals import ocr_junk

OUT = ROOT / "results" / "book_spotcheck"
SEED = 20261120
SIZES = {"A": 70, "B": 40, "C": 30}
VERDICTS = "correct,boundary,wrong_field,not_a_mention,misread,unsure"


def load(run: str) -> pd.DataFrame:
    m = pd.read_csv(ROOT / "results" / run / "mentions.csv", keep_default_na=False)
    m = m[m.split == "book"].copy()
    m["version"], m["outcome"] = "modern_dots-mocr", ""
    m["src_start"] = pd.to_numeric(m.start, errors="coerce")
    m["src_end"] = pd.to_numeric(m.end, errors="coerce")
    return m.reset_index(drop=True)


def readable(x: str) -> str:
    """For the checker's eyes only: dots.mocr writes Markdown (*italic*, **bold**, ### headings,
    | tables) and HTML tables (<td>...</td>). Turn table cells into ' | ', rows into ' / ', and
    drop the other markup. The model saw the raw text; values are sliced from it unchanged."""
    x = re.sub(r"</t[dh]>\s*<t[dh][^>]*>", " | ", x)
    x = re.sub(r"</tr>\s*<tr[^>]*>", " / ", x)
    x = re.sub(r"<[^>]*>|<[^>]*$|^[^<]*>", " ", x)        # whole tags, and tags cut at the edges
    x = re.sub(r"\*+|#{2,}\s*|(?<!\w)_|_(?!\w)", "", x)
    x = re.sub(r"\s*\|\s*(\|\s*)+", " | ", x)
    return re.sub(r"\s+", " ", x).strip()


def context(pid: int, s, e, raw: bool = False) -> str:
    t = (ROOT / "data" / "text" / "modern_dots-mocr" / f"{pid}.txt").read_text(encoding="utf-8")
    if pd.isna(s):
        return ""
    s, e = int(s), int(e)
    left, mid, right = t[max(0, s - 120):s], t[s:e], t[e:e + 120]
    if raw:
        return (left + " [[" + mid + "]] " + right).replace("\n", " ")
    left, right = readable(left)[-90:], readable(right)[:90]
    return f"{left} [[{readable(mid)}]] {right}"


def build_pool(opus_run: str, haiku_run: str) -> pd.DataFrame:
    opus, haiku = load(opus_run), load(haiku_run)
    fo = flag_auto_accept(opus, haiku)
    fh = flag_auto_accept(haiku, opus)           # Haiku mentions that Opus has no counterpart for
    fo["junk"] = fo.value.map(ocr_junk)
    fo["stratum"] = ["A" if t == 0 and not j else "B" for t, j in zip(fo.tier, fo.junk)]
    c = fh[~fh.agree].copy()
    c["stratum"], c["junk"] = "C", c.value.map(ocr_junk)
    return pd.concat([fo.assign(model="opus"), c.assign(model="haiku")], ignore_index=True)


def page_types() -> dict:
    gt = pd.read_parquet(ROOT / "data" / "cache" / "gt_english.parquet", columns=["PageID", "PageTypeName"])
    return dict(zip(gt.PageID.astype(int), gt.PageTypeName.fillna("")))


def make(a) -> None:
    pool = build_pool(a.opus, a.haiku)
    (OUT).mkdir(parents=True, exist_ok=True)
    (OUT / "runs.txt").write_text(f"{a.opus}\n{a.haiku}\n", encoding="utf-8")
    sizes = pool.stratum.value_counts().to_dict()
    picks = []
    for s, n in SIZES.items():
        d = pool[pool.stratum == s]
        picks.append(d.sample(min(n, len(d)), random_state=SEED))
    smp = pd.concat(picks).sample(frac=1, random_state=SEED).reset_index(drop=True)
    smp["item"] = range(1, len(smp) + 1)
    smp["context"] = [context(p, s, e) for p, s, e in zip(smp.page_id, smp.src_start, smp.src_end)]
    smp["context_raw"] = [context(p, s, e, raw=True) for p, s, e in zip(smp.page_id, smp.src_start, smp.src_end)]
    smp["bhl_page"] = "https://www.biodiversitylibrary.org/page/" + smp.page_id.astype(str)
    OUT.mkdir(parents=True, exist_ok=True)
    sheet = pd.DataFrame({"item": smp.item, "page_id": smp.page_id, "book": smp.book, "field": smp.field,
                          "value": smp.value, "context": smp.context, "verdict": "", "correct_field": "",
                          "notes": "", "review_seconds": "", "bhl_page": smp.bhl_page})
    sheet.to_csv(OUT / "spotcheck_sheet.csv", index=False)
    smp[["item", "stratum", "model", "tier", "junk", "page_id", "field", "value", "status", "context_raw"]].to_csv(
        OUT / "spotcheck_key.csv", index=False)
    pd.DataFrame([{"stratum": k, "mentions_in_book": v, "sampled": int((smp.stratum == k).sum())}
                  for k, v in sorted(sizes.items())]).to_csv(OUT / "strata.csv", index=False)

    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Font, PatternFill
    from openpyxl.worksheet.datavalidation import DataValidation
    wb = Workbook()
    ws = wb.active
    ws.title = "check"
    ws.append(list(sheet.columns))
    for r in sheet.itertuples(index=False):
        ws.append(list(r))
    yellow, grey = PatternFill("solid", fgColor="FFF2CC"), PatternFill("solid", fgColor="EDEDED")
    widths = {"item": 6, "page_id": 10, "book": 8, "field": 11, "value": 26, "context": 90, "verdict": 14,
              "correct_field": 13, "notes": 30, "review_seconds": 9, "bhl_page": 40}
    for i, col in enumerate(sheet.columns, 1):
        cell = ws.cell(1, i)
        cell.font = Font(bold=True)
        cell.fill = yellow if col in ("verdict", "correct_field", "notes", "review_seconds") else grey
        ws.column_dimensions[cell.column_letter].width = widths[col]
    n = len(sheet) + 1
    for j in range(2, n + 1):
        ws.cell(j, 6).alignment = Alignment(wrap_text=True, vertical="top")
        ws.cell(j, 11).hyperlink = ws.cell(j, 11).value
        ws.cell(j, 11).font = Font(color="0563C1", underline="single")
    for col, opts in (("G", VERDICTS), ("H", "taxon,vernacular,person,locality,institution,date")):
        dv = DataValidation(type="list", formula1=f'"{opts}"', allow_blank=True)
        ws.add_data_validation(dv)
        dv.add(f"{col}2:{col}{n}")
    ws.freeze_panes = "E2"
    how = wb.create_sheet("how to fill")
    for line in [
        "这是模型在整本书（样本 22 页以外）上的抽取结果，抽样检查。不是金标准，不会进 gold/。",
        "每行：value 是模型抽到的值，context 里 [[ ]] 标出它在 dots.mocr 文本中的位置。点 bhl_page 看扫描页核对。",
        "context 已去掉排版符号（*斜体*、**粗体**、### 标题、表格标签），表格的格子用 | 隔开、行用 / 隔开，只为好读；模型看到的是带符号的原文，抽到的值本身不含这些符号。",
        "verdict（下拉）：correct=按标注指南 v0.10 这是一个该抽的提及，类型和边界都对；boundary=是提及但边界不对；"
        "wrong_field=是提及但类型错（在 correct_field 选对的类型）；not_a_mention=按指南不该抽；"
        "misread=OCR 把字读错了，值和扫描页不一致；unsure=拿不准（notes 写原因）。",
        "review_seconds 可选：大概用了几秒。用来估算人工复核每条的成本。",
        "顺序已打乱，看不到模型是否一致，这是故意的（避免先入为主）。",
        "填完把 xlsx 直接发回即可。",
    ]:
        how.append([line])
    how.column_dimensions["A"].width = 130
    wb.save(OUT / "spotcheck_sheet.xlsx")
    print(pd.read_csv(OUT / "strata.csv").to_string(index=False))
    print(f"{len(sheet)} items -> {OUT / 'spotcheck_sheet.xlsx'}")


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return float("nan"), float("nan")
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return round(c - h, 3), round(c + h, 3)


def score() -> None:
    """Precision per stratum and a whole-book estimate. Scope (Gloria, 2026-11-20, GUIDE_ADDENDUM.md):
    pages BHL types as `Index` are out of scope, so outputs there are dropped before scoring and the
    stratum sizes are recounted without them (a page-type filter would remove them before extraction).
    `unsure` rows are left out. Both the all-pages and the in-scope tables are written."""
    filled = sorted((OUT / "received").glob("*.xlsx"))
    if not filled:
        sys.exit(f"Put the returned sheet in {OUT / 'received'} first.")
    s = pd.read_excel(filled[-1], sheet_name="check").fillna("")
    k = pd.read_csv(OUT / "spotcheck_key.csv")
    types = page_types()
    d = s.merge(k[["item", "stratum", "model"]], on="item")
    d["index_page"] = d.page_id.map(lambda p: types.get(int(p)) == "Index")
    opus_run, haiku_run = (OUT / "runs.txt").read_text().split()
    pool = build_pool(opus_run, haiku_run)
    pool["index_page"] = pool.page_id.map(lambda p: types.get(int(p)) == "Index")
    lines = ["# Whole-book spot-check (exploratory)", "",
             f"Checked by Gloria against the scans: {int((d.verdict != '').sum())} of {len(k)} shuffled rows "
             f"(sheet `{filled[-1].name}`). `unsure` rows are left out of precision.", ""]
    for label, keep_index in (("All pages (as sampled)", True), ("In scope: `Index` pages excluded", False)):
        dd = d if keep_index else d[~d.index_page]
        pp = pool if keep_index else pool[~pool.index_page]
        size = pp.stratum.value_counts()
        dd = dd[dd.verdict.isin(VERDICTS.split(",")) & (dd.verdict != "unsure")]
        rows = []
        for g, x in dd.groupby("stratum"):
            ok = int((x.verdict == "correct").sum())
            lo, hi = wilson(ok, len(x))
            rows.append({"stratum": g, "checked": len(x), "correct": ok, "precision": round(ok / len(x), 3),
                         "lo": lo, "hi": hi, "mentions_in_book": int(size.get(g, 0)),
                         **{v: int((x.verdict == v).sum()) for v in VERDICTS.split(",")[1:-1]}})
        t = pd.DataFrame(rows)
        ab = t[t.stratum.isin(["A", "B"])]
        whole = (ab.precision * ab.mentions_in_book).sum() / ab.mentions_in_book.sum()
        unsure = int(((d if keep_index else d[~d.index_page]).verdict == "unsure").sum())
        lines += [f"## {label}", "", t.to_markdown(index=False), "",
                  f"Opus precision, weighted by stratum size (A+B): {whole:.3f}; `unsure` rows left out: {unsure}. "
                  "Stratum C is what Haiku found and Opus did not: `correct` there are Opus misses.", ""]
    n_idx = int(pool[(pool.model == "opus") & pool.index_page].shape[0])
    lines += [f"Opus mentions on `Index` pages (removed by the scope rule): {n_idx} of "
              f"{int((pool.model == 'opus').sum())} outside the sample.", ""]
    secs = pd.to_numeric(s.review_seconds, errors="coerce").dropna()
    if len(secs):
        lines += [f"Review time, {len(secs)} timed rows: median {secs.median():.0f} s per item "
                  f"(range {secs.min():.0f}-{secs.max():.0f}).", ""]
    (OUT / "REPORT.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("opus", nargs="?")
    ap.add_argument("haiku", nargs="?")
    ap.add_argument("--score", action="store_true")
    a = ap.parse_args()
    score() if a.score else make(a)
