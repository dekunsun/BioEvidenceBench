"""Build the error-analysis sheet for Gloria (PREREGISTRATION section 5): every false positive
and false negative of the main LLM in condition G1 on the test pages.

    python src/make_error_sheet.py
        -> results/error_analysis_test/error_analysis_opus_G1.xlsx (and a CSV per sheet)

One row per CASE, not per scorer row, so each thing is tagged once:
  sheet "gold_mentions"  one row per gold mention that is wrong in at least one text version.
                         A misread name is one false negative AND one false positive in the
                         scorer; here it is one row. The four version columns show what the
                         model did on each text: correct / misread (span found, text differs:
                         the value is shown) / missed.
  sheet "extra_outputs"  one row per model output with no gold mention behind it (or that
                         could not be placed on the expert text), merged across versions when
                         it lands on the same expert position.

Rows are sorted into groups by FACTS only (which versions are wrong), so similar cases sit
together and can be tagged in a batch. The tag columns (OCR-sensitive, extraction/reasoning,
ambiguous/mixed: more than one may apply) and the note are left EMPTY: the tags are Gloria's.
Reads only results and gold; writes nothing in gold/.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

from common import DATA, ROOT
from score import score_run_detail

RUN = "20261119-2052_claude-opus-5-5_test_batch"
GOLD = ROOT / "gold" / "gold_mentions_gloria_test.csv"
OUT = ROOT / "results" / "error_analysis_test"
VERSIONS = ["expert", "modern_dots-mocr", "modern_dots-mocr_plain", "legacy"]
VLABEL = {"expert": "专家转录", "modern_dots-mocr": "现代OCR", "modern_dots-mocr_plain": "现代OCR去格式",
          "legacy": "旧OCR"}
TAGS = ["OCR相关", "抽取或推理", "模糊或混合"]


def context(page_id: int, start: int, end: int, width: int = 45) -> str:
    t = (DATA / "sample" / "expert" / f"{page_id}.txt").read_text(encoding="utf-8")
    a, b = max(0, start - width), min(len(t), end + width)
    return (t[a:start] + "【" + t[start:end] + "】" + t[end:b]).replace("\n", " ")


def result(r) -> str:
    if r.value_ok:
        return "对"
    if r.lenient:
        return f"读错：{r.pred_value}"
    return "漏掉"


def gold_sheet(go: pd.DataFrame) -> pd.DataFrame:
    go = go[go.condition == "G1"]
    key = ["page_id", "book", "field", "start", "end", "text"]
    wide = go.assign(res=go.apply(result, axis=1)).pivot_table(
        index=key, columns="version", values="res", aggfunc="first").reset_index()
    wrong = wide[VERSIONS].ne("对")
    wide = wide[wrong.any(axis=1)].copy()
    w = wide[VERSIONS].ne("对")

    def group(r):
        bad = [v for v in VERSIONS if r[v] != "对"]
        if bad == ["legacy"]:
            return "A 只在旧OCR上错"
        if "expert" not in bad:
            return "B 专家转录对，现代OCR也错"
        if len(bad) == len(VERSIONS):
            return "C 所有版本都错（包括专家转录）"
        return "D 专家转录错，部分版本对"
    wide["分组"] = wide.apply(group, axis=1)
    wide["旧OCR上是"] = wide.legacy.map(lambda s: "读错" if s.startswith("读错") else ("漏掉" if s == "漏掉" else "对"))
    wide["上下文（专家转录，【】是金标准）"] = [context(p, s, e) for p, s, e in zip(wide.page_id, wide.start, wide.end)]
    wide = wide.rename(columns={v: VLABEL[v] for v in VERSIONS} | {"text": "金标准文字", "field": "字段"})
    wide = wide.sort_values(["分组", "旧OCR上是", "book", "page_id", "start"])
    cols = ["分组", "旧OCR上是", "book", "page_id", "字段", "金标准文字", "上下文（专家转录，【】是金标准）"] \
        + [VLABEL[v] for v in VERSIONS] + ["start", "end"]
    out = wide[cols].reset_index(drop=True)
    for t in TAGS:
        out[t] = ""
    out["备注"] = ""
    return out


def extra_sheet(po: pd.DataFrame, gold_all: pd.DataFrame) -> pd.DataFrame:
    po = po[(po.condition == "G1") & po.outcome.isin(["fp_no_gold", "fp_unaligned"])].copy()
    po["placed"] = po.m_start.notna()
    po["ms"] = po.m_start.fillna(-1).astype(int)
    po["me"] = po.m_end.fillna(-1).astype(int)
    rows = []
    for (pid, book, field, ms, me), d in po.groupby(["page_id", "book", "field", "ms", "me"]):
        if ms < 0:            # unaligned: one row per value
            for val, dv in d.groupby("value"):
                rows.append({"page_id": pid, "book": book, "字段": field, "模型输出": val,
                             "出现在哪些版本": "、".join(VLABEL[v] for v in VERSIONS if v in set(dv.version)),
                             "上下文（专家转录）": "（无法对齐到专家转录）", "start": "", "end": "",
                             "和你裁定的行的关系": ""})
            continue
        ex = gold_all[(gold_all.page_id == pid) & (gold_all.start < me) & (gold_all.end > ms)]
        rel = "; ".join(f"{r.field} {r.text!r} 你裁定为 {r.adjudication or '金标准'}" for r in ex.itertuples())
        rows.append({"page_id": pid, "book": book, "字段": field,
                     "模型输出": " / ".join(sorted(set(d.value))),
                     "出现在哪些版本": "、".join(VLABEL[v] for v in VERSIONS if v in set(d.version)),
                     "上下文（专家转录）": context(pid, ms, me), "start": ms, "end": me,
                     "和你裁定的行的关系": rel})
    out = pd.DataFrame(rows)
    n = out["出现在哪些版本"].str.count("、") + 1
    out.insert(0, "分组", ["E 四个版本都输出了" if k == 4 else "F 只在部分版本输出" for k in n])
    out.loc[out["上下文（专家转录）"].str.startswith("（无法"), "分组"] = "G 无法对齐到专家转录"
    out = out.sort_values(["分组", "字段", "book", "page_id"]).reset_index(drop=True)
    for t in TAGS:
        out[t] = ""
    out["备注"] = ""
    return out


def write_xlsx(sheets: dict[str, pd.DataFrame], path: Path, notes: list[str]) -> None:
    from openpyxl.styles import Alignment, Font, PatternFill
    from openpyxl.worksheet.datavalidation import DataValidation
    with pd.ExcelWriter(path, engine="openpyxl") as xw:
        pd.DataFrame({"怎么填": notes}).to_excel(xw, sheet_name="先看这里", index=False)
        for name, df in sheets.items():
            df.to_excel(xw, sheet_name=name, index=False)
        wb = xw.book
        wb["先看这里"].column_dimensions["A"].width = 120
        yellow = PatternFill("solid", fgColor="FFF2CC")
        for name, df in sheets.items():
            ws = wb[name]
            ws.freeze_panes = "A2"
            ws.auto_filter.ref = ws.dimensions
            for i, c in enumerate(df.columns, 1):
                letter = ws.cell(1, i).column_letter
                ws.cell(1, i).font = Font(bold=True)
                width = 60 if c.startswith("上下文") else 26 if c in VLABEL.values() or c in ("模型输出", "和你裁定的行的关系") \
                    else 30 if c == "备注" else 18 if c in ("分组", "金标准文字", "出现在哪些版本") else 11
                ws.column_dimensions[letter].width = width
                if c in TAGS or c == "备注":
                    ws.cell(1, i).fill = yellow
                if c in TAGS and len(df):
                    dv = DataValidation(type="list", formula1='"是"', allow_blank=True)
                    ws.add_data_validation(dv)
                    dv.add(f"{letter}2:{letter}{len(df) + 1}")
                if c.startswith("上下文"):
                    for r in range(2, len(df) + 2):
                        ws.cell(r, i).alignment = Alignment(wrap_text=True, vertical="top")


def main() -> None:
    d = score_run_detail(RUN, GOLD, "test")
    gold_all = pd.read_csv(GOLD, dtype=str, keep_default_na=False)
    gold_all["page_id"] = gold_all.page_id.astype(int)
    gold_all["start"], gold_all["end"] = gold_all.start.astype(int), gold_all.end.astype(int)
    g = gold_sheet(d["gold_outcomes"])
    e = extra_sheet(d["pred_outcomes"], gold_all)
    OUT.mkdir(parents=True, exist_ok=True)
    g.to_csv(OUT / "gold_mentions.csv", index=False)
    e.to_csv(OUT / "extra_outputs.csv", index=False)
    counts = lambda df: "；".join(f"{k} {v} 行" for k, v in df["分组"].value_counts().sort_index().items())
    notes = [
        f"模型：{RUN}，条件 G1（要求引用原文），16 页测试集。按预注册第 5 节，只分析这个配置的错误。",
        "一行是一个“错误案例”。同一个金标准提及在四个文字版本上的结果合并在一行，所以每个提及只标一次。",
        "表“金标准提及”：至少在一个版本上没被正确抽出的金标准提及。四个版本列：对 / 读错：模型给出的文字（位置找到了，文字不同）/ 漏掉。",
        f"   分组（只按事实分，不是归因）：{counts(g)}。",
        "表“多余输出”：模型输出了、但金标准里没有对应提及的内容；落在同一位置的输出跨版本合并。最后一列说明它是否落在你裁定为 excluded 等的行上。",
        f"   分组：{counts(e)}。",
        "要填的是黄色表头的列：OCR相关、抽取或推理、模糊或混合（下拉选“是”，可以多选），备注可选。归因列全部留空，没有预填。",
        "定义（CLAUDE.md / 预注册）：OCR相关 = 换了 OCR 输入结果就变了（只说明敏感，不证明是哪个字错）；抽取或推理 = 在专家转录上仍然错；"
        "模糊或混合 = 历史分类、标注本身有争议、版式加 OCR、阅读顺序缺失等。",
        "建议：先按分组和“旧OCR上是”筛选，同类的可以整段一起填。分组 A 里“读错”的行大多是同一类情况，可以成批处理，但请至少抽看几行确认。",
        "填完直接把这个 xlsx 发回。",
    ]
    write_xlsx({"金标准提及": g, "多余输出": e}, OUT / "error_analysis_opus_G1.xlsx", notes)
    print(f"gold_mentions: {len(g)} rows ({counts(g)})\nextra_outputs: {len(e)} rows ({counts(e)})")


if __name__ == "__main__":
    sys.exit(main())
