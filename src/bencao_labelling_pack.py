"""本草綱目 case: labelling workbook for the remaining pilot half-leaves (the author labels them alone).

    python src/bencao_labelling_pack.py   -> gold/labelling_bencao_remaining5.xlsx

Sheets: 说明 (how to fill), one 原文 sheet per half-leaf (scan-verified reference text, one manuscript
column per line), 标注 (one row per mention; page_id and field from drop-downs), 用时 (minutes per page).
Column order puts `text` before `qualifier`: in the 036-1b workbook the two were swapped (2026-11-24).
No row is pre-filled; offsets are computed later from line + text (src/bencao_inline_labels.py rules).
"""
from __future__ import annotations

from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font
from openpyxl.worksheet.datavalidation import DataValidation

ROOT = Path(__file__).resolve().parents[1]
PAGES = ["036-5a", "036-7b", "036-12b", "036-13a", "036-30a"]
COLS = ["page_id", "line", "field", "text", "qualifier", "restored_form", "normalization_type",
        "restoration_evidence", "scan_text", "notes"]
NOTES = [
    "《本草綱目》其余 5 个半叶标注表（规范 docs/notes/bencao_guide.md v0.3）",
    "",
    "1. 每页先自己独立标完；可以一次发一页，也可以 5 页一起发。发的时候说一句每页大概用了多少分钟（「用时」页可填可不填）。",
    "2. 「原文_xxx」页是核对过扫描的参考文本，一行 = 扫描上从右往左的一列；双行小注已按先右后左连成一行。",
    "3. 「标注」页每个提及一行：page_id、field 从下拉框选；line 写行号；text 从原文原样复制（第 D 列），不要改字。",
    "4. 位置不用填。同一行里同一个词出现几次就写几行，按阅读顺序排。",
    "5. 字段：taxon（药名、植物名、别名）、person（人名，含简称）、locality（地名）、cited_work（书名）、substance（矿物等，单独计分）。",
    "6. qualifier：釋名下的别名填 alias；其他情况可以空着（也可以像 036-1b 一样写你自己的分类，不影响评分）。",
    "7. 历史写法（第 10 条）：text 照原样；需要规范写法时填 restored_form、normalization_type（下拉）、restoration_evidence。",
    "8. v0.3 新规则：书名+篇名连写算一个书名（詩唐風）；「地名+药名」算一个药名（枹䍐草），里面的地名不再另标；",
    "   族群名指地方时算地名（西羌地名）；被换列切开的词算一个（第 2 列末「上」+ 第 3 列首「郡」= 上郡，text 写「上郡」即可）。",
    "9. 拿不准、需要专家的：照最佳判断标，notes 写「UNCLEAR: 原因」或「专家:」。",
]


def main() -> None:
    wb = Workbook()
    ws = wb.active
    ws.title = "说明"
    for n in NOTES:
        ws.append([n])
    ws.column_dimensions["A"].width = 130
    ws["A1"].font = Font(bold=True)
    for pb in PAGES:
        s = wb.create_sheet(f"原文_{pb}")
        s.append(["line", "text"])
        for i, line in enumerate((ROOT / "data" / "bencao" / "verified_plain" / f"{pb}.txt").read_text(encoding="utf-8").splitlines(), 1):
            s.append([i, line])
        s.column_dimensions["B"].width = 110
        for r in s.iter_rows(min_row=2):
            r[1].alignment = Alignment(wrap_text=True)
    t = wb.create_sheet("标注")
    t.append(COLS)
    n = 400
    for _ in range(n):
        t.append([None] * len(COLS))
    for col, values in (("A", ",".join(PAGES)), ("C", "taxon,person,locality,cited_work,substance"),
                        ("G", "glyph_variant,taboo_missing_stroke,taboo_substitution,interchangeable_usage")):
        dv = DataValidation(type="list", formula1=f'"{values}"', allow_blank=True)
        t.add_data_validation(dv)
        dv.add(f"{col}2:{col}{n + 1}")
    for c, w in zip("ABCDEFGHIJ", [10, 6, 12, 16, 12, 14, 22, 30, 12, 34]):
        t.column_dimensions[c].width = w
    u = wb.create_sheet("用时")
    u.append(["page_id", "大约分钟", "备注"])
    for pb in PAGES:
        u.append([pb, None, None])
    out = ROOT / "gold" / "labelling_bencao_remaining5.xlsx"
    wb.save(out)
    print(out)


if __name__ == "__main__":
    main()
