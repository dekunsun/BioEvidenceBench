"""Build the short-procedure linking sheets for Reeve's test-page taxa (as was done for Butler).

    python src/make_link_sheet.py

Writes, without filling any judgement column:
  gold/gold_links_gloria_reeve.csv            one row per taxon MENTION (page, offsets, text)
  gold/gold_links_gloria_reeve_names.xlsx/.csv one row per distinct printed name, for Gloria to fill:
      printed_rank, resolution_status, accepted_name, evidence_source (notes optional)
The helper columns (mentions, pages, context, search links) are facts and links only.
After she fills the names sheet, src/expand_links.py --book reeve copies her decisions to every
mention (to be added when the sheet comes back).
"""
from __future__ import annotations

import urllib.parse as up

import pandas as pd

from common import DATA, ROOT
from score import load_gold, page_text

GOLD = ROOT / "gold"


def main() -> None:
    split = pd.read_csv(DATA / "sample_split.csv").query("split == 'test' and book == 'Reeve'")
    g = load_gold(GOLD / "gold_mentions_gloria_test.csv")
    g = g[(g.field == "taxon") & g.page_id.isin(set(split.PageID))].sort_values(["page_id", "start"])
    rows = []
    for r in g.itertuples():
        t = page_text("expert", r.page_id)
        ctx = t[max(0, r.start - 60):r.end + 60].replace("\n", " ")
        rows.append({"page_id": r.page_id, "start": r.start, "end": r.end, "text": r.text,
                     "context (helper)": ctx})
    m = pd.DataFrame(rows)
    m.to_csv(GOLD / "gold_links_gloria_reeve.csv", index=False)

    m["name"] = m.text.str.replace("-\n", "", regex=False).str.replace("\n", " ", regex=False)
    names = m.groupby("name", sort=False).agg(mentions=("text", "size"),
                                              pages=("page_id", lambda s: " ".join(map(str, sorted(set(s))))),
                                              context=("context (helper)", "first")).reset_index()
    q = names.name.map(up.quote)
    out = pd.DataFrame({
        "name": names.name, "printed_rank": "", "resolution_status": "", "accepted_name": "",
        "evidence_source": "", "notes": "",
        "mentions (helper)": names.mentions, "pages (helper)": names.pages, "context (helper)": names.context,
        "molluscabase_search (helper)": "https://www.molluscabase.org/aphia.php?p=taxlist&tName=" + q,
        "gbif_search (helper)": "https://www.gbif.org/species/search?q=" + q,
        "bhl_page (helper)": "https://www.biodiversitylibrary.org/page/" + names.pages.str.split().str[0]})
    out.to_csv(GOLD / "gold_links_gloria_reeve_names.csv", index=False)

    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill
    from openpyxl.worksheet.datavalidation import DataValidation
    wb = Workbook()
    ws = wb.active
    ws.title = "names"
    ws.append(list(out.columns))
    for r in out.itertuples(index=False):
        ws.append(list(r))
    yellow, grey = PatternFill("solid", fgColor="FFF2CC"), PatternFill("solid", fgColor="EDEDED")
    widths = [28, 13, 16, 28, 15, 30, 9, 18, 70, 30, 30, 30]
    for i, c in enumerate(out.columns, 1):
        cell = ws.cell(1, i)
        cell.font = Font(bold=True)
        cell.fill = yellow if "(helper)" not in c else grey
        ws.column_dimensions[cell.column_letter].width = widths[i - 1]
        if "search" in c or "bhl_page" in c:
            for j in range(2, len(out) + 2):
                v = ws.cell(j, i).value
                ws.cell(j, i).hyperlink = v
                ws.cell(j, i).font = Font(color="0563C1", underline="single")
    n = len(out) + 1
    for col, opts in (("B", "species,subspecies,genus,subfamily,family"),
                      ("C", "resolved,partial,ambiguous,unresolved"),
                      ("E", "MolluscaBase,WoRMS,GBIF,other")):
        dv = DataValidation(type="list", formula1=f'"{opts}"', allow_blank=True)
        ws.add_data_validation(dv)
        dv.add(f"{col}2:{col}{n}")
    ws.freeze_panes = "B2"
    how = wb.create_sheet("how to fill")
    for line in [
        "和 Butler 那张一样：只填黄色表头的 4 列（notes 可选）。灰色列是辅助信息，不用改。",
        "printed_rank：两个词=species；一个首字母大写的词=genus；词尾 -IDÆ / -IDAE=family（下拉选择）。",
        "先点 molluscabase_search（MolluscaBase 是软体动物的专门名录，相当于鸟类的 Avibase）。看结果里 status 为 accepted 的名字，把今天的接受名填进 accepted_name，例如 Bulimulus rugiferus。不用抄编号，编号由脚本自动查。",
        "MolluscaBase 显示 unaccepted 时，页面上会写 'accepted as ...'：填那个接受名，notes 写 '书上的名字是同物异名'。",
        "resolution_status：resolved=定了；partial=种名只对到属；ambiguous=几个候选定不了（候选写 notes）；unresolved=查不到（accepted_name 留空）。",
        "每个名字最多约 3 分钟；定不了就填 ambiguous 或 unresolved，这是合法答案。",
        "缩写名（T. / B.）先看 context 列，前文会出现全名；还找不到就点 bhl_page 往前翻。",
        "填完把这个 xlsx 文件直接发回即可。",
    ]:
        how.append([line])
    how.column_dimensions["A"].width = 120
    wb.save(GOLD / "gold_links_gloria_reeve_names.xlsx")
    print(f"{len(m)} mentions, {len(out)} distinct names")


if __name__ == "__main__":
    main()
