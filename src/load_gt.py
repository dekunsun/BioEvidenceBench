"""Task 2: load the Butler and Reeve pages from finebooks/bhl-impact-gt and
check how they join to finebooks/bhl-metadata.

Outputs
  data/cache/gt_english.parquet        all English GT pages incl. text (not committed)
  data/gt_pages.csv                    one row per page, no text (committed)
  data/text/expert/<PageID>.txt        expert transcription, exactly as published
  data/text/expert_view/<PageID>.txt   same text with a character-offset ruler,
                                       for labelling by hand (see ANNOTATION_GUIDE.md)
  data/text/manifest_expert.csv        SHA-256 of every expert text file
  data/reports/01_dataset_check.md     what we checked and what we found

Run:  python src/load_gt.py
"""
from __future__ import annotations

import pandas as pd

from common import (CACHE, DATA, ENGLISH_BOOKS, GT_PARQUET, MD_ITEM, MD_PAGE,
                    MD_TITLE, REPORTS, TEXT, bhl_page_url, connect, sha256_text)


def offset_view(text: str) -> str:
    """Prefix every line with the character offset where it starts.

    The gold set stores mentions as [start, end) offsets into the expert
    `text` string (Python-style: 0-based, end exclusive). To find the offset
    of a word, add the line's starting offset to the word's column.
    Example:  "  1530 | Hab. Philippine Islands"  ->  'Philippine' starts at
    1530 + 5 = 1535.
    """
    out, pos = [], 0
    for line in text.split("\n"):
        out.append(f"{pos:>6} | {line}")
        pos += len(line) + 1  # +1 for the "\n" that split() removed
    return "\n".join(out) + "\n"


def main() -> None:
    con = connect()
    for d in (CACHE, REPORTS, TEXT / "expert", TEXT / "expert_view"):
        d.mkdir(parents=True, exist_ok=True)

    # 1. Schema of the GT file (cheap: reads only the Parquet footer).
    schema = con.sql(f"DESCRIBE SELECT * FROM '{GT_PARQUET}'").df()[["column_name", "column_type"]]

    # 2. Which books are English according to the BHL catalogue?
    books = con.sql(f"""
        WITH b AS (SELECT DISTINCT BarCode FROM '{GT_PARQUET}')
        SELECT i.BarCode, i.ItemID, i.TitleID, t.LanguageCode, i.Year,
               i.CopyrightStatus, i.LicenseType, i.RightsStatement, t.ShortTitle
        FROM b JOIN '{MD_ITEM}' i USING (BarCode)
               JOIN '{MD_TITLE}' t USING (TitleID)
        ORDER BY i.BarCode
    """).df()
    eng = set(books.loc[books.LanguageCode == "ENG", "BarCode"])
    if eng != set(ENGLISH_BOOKS):
        raise SystemExit(f"English books in catalogue {eng} != expected {set(ENGLISH_BOOKS)}")
    item_ids = books.loc[books.BarCode.isin(eng), "ItemID"].tolist()

    # 3. GT rows for the English books, joined to the page table.
    #    The BHL page export contains some exact duplicate rows, so we
    #    de-duplicate the page table before joining.
    con.sql(f"""
        CREATE TABLE pg AS
        SELECT DISTINCT PageID, ItemID, SequenceOrder, PageNumber, PageTypeName
        FROM '{MD_PAGE}' WHERE ItemID IN ({",".join(map(str, item_ids))})
    """)
    page_dupes = con.sql(
        "SELECT count(*) - count(DISTINCT PageID) FROM pg").fetchall()[0][0]
    gt = con.sql(f"""
        SELECT g.PageID, g.BarCode, g.file_name, g.xml_path,
               g.text,
               length(g.text)                          AS gt_chars,
               contains(g.xml, '<ReadingOrder')        AS has_reading_order,
               length(g.text) - length(replace(g.text, chr(65533), '')) AS n_illegible,
               p.ItemID, p.SequenceOrder, p.PageNumber, p.PageTypeName
        FROM '{GT_PARQUET}' g
        LEFT JOIN (SELECT PageID, any_value(ItemID) ItemID, any_value(SequenceOrder) SequenceOrder,
                          string_agg(DISTINCT PageNumber, ';') PageNumber,
                          string_agg(DISTINCT PageTypeName, ';') PageTypeName
                   FROM pg GROUP BY PageID) p USING (PageID)
        WHERE g.BarCode IN ({",".join(f"'{b}'" for b in sorted(eng))})
        ORDER BY g.BarCode, p.SequenceOrder
    """).df()

    unjoined = int(gt.ItemID.isna().sum())
    gt.to_parquet(CACHE / "gt_english.parquet", index=False)

    # 4. Write the expert texts exactly as published (no normalisation).
    manifest = []
    for r in gt.itertuples():
        if not r.text:
            continue
        (TEXT / "expert" / f"{r.PageID}.txt").write_text(r.text, encoding="utf-8")
        (TEXT / "expert_view" / f"{r.PageID}.txt").write_text(offset_view(r.text), encoding="utf-8")
        manifest.append({"page_id": r.PageID, "version": "expert", "chars": len(r.text),
                         "sha256": sha256_text(r.text),
                         "source": f"{GT_PARQUET} (row PageID={r.PageID})"})
    pd.DataFrame(manifest).to_csv(TEXT / "manifest_expert.csv", index=False)

    # 5. Committed page list (no text).
    gt["bhl_url"] = gt.PageID.map(bhl_page_url)
    cols = ["PageID", "BarCode", "ItemID", "SequenceOrder", "PageNumber", "PageTypeName",
            "gt_chars", "has_reading_order", "n_illegible", "bhl_url"]
    gt[cols].to_csv(DATA / "gt_pages.csv", index=False)

    # 6. Report.
    per_book = gt.assign(empty=gt.gt_chars == 0).groupby("BarCode").agg(
        pages=("PageID", "count"), distinct_pageids=("PageID", "nunique"),
        empty_text=("empty", "sum"),
        pages_with_illegible=("n_illegible", lambda s: int((s > 0).sum())),
        median_chars=("gt_chars", "median"))
    # Reading order is only meaningful on pages that have text.
    ro = gt[gt.gt_chars > 0].groupby("BarCode").has_reading_order.mean()
    per_book["text_pages_with_reading_order"] = (ro * 100).round(1).astype(str) + "%"
    types = (gt.groupby(["BarCode", "PageTypeName"]).size().unstack(0, fill_value=0)
             .sort_values(list(eng)[0], ascending=False))

    lines = [
        "# 01 Dataset check: bhl-impact-gt (English books) joined to bhl-metadata",
        "",
        "Generated by `src/load_gt.py`. Re-run it to refresh.",
        "",
        "## License",
        "",
        "- `finebooks/bhl-impact-gt`: **CC-BY 3.0** (dataset card). Attribute *IMPACT / Biodiversity Heritage Library*.",
        "  The transcriptions come from the IMPACT-BHL ground truth (github.com/impactcentre/groundtruth-bhl).",
        "- `finebooks/bhl-metadata`: **CC0 1.0** (dataset card).",
        "- Per-item rights from the `item` table are below. Both English books are `NOT_IN_COPYRIGHT`.",
        "- We do **not** commit page texts. Scripts fetch them into `data/text/` (git-ignored).",
        "",
        "## Schema of bhl-impact-gt `metadata.parquet`",
        "",
        schema.to_markdown(index=False),
        "",
        "`image` is not in the Parquet file. It is a separate WebP file named by `file_name`.",
        "We only need text, so we never download the images.",
        "",
        "## The six books and their rights (from bhl-metadata `item` + `title`)",
        "",
        books.drop(columns=["RightsStatement"]).to_markdown(index=False),
        "",
        "## Join check: GT `PageID` to bhl-metadata `page.PageID`",
        "",
        f"- English GT rows: **{len(gt)}**; distinct PageIDs: **{gt.PageID.nunique()}**.",
        f"- GT rows with no matching row in the `page` table: **{unjoined}**.",
        f"- Duplicate PageIDs inside the BHL `page` export for these two items, after `DISTINCT`: **{page_dupes}** "
        "(the raw export has some exact duplicate rows; we de-duplicate before joining).",
        "- `BarCode` = Internet Archive identifier for both books, as the dataset card says.",
        "",
        "## Per-book summary",
        "",
        per_book.to_markdown(),
        "",
        "- `empty_text`: plates and blank pages. Their `text` is `\"\"`; they are excluded from CER and sampling.",
        "- `text_pages_with_reading_order`: among pages with text, share whose PAGE XML has an explicit `<ReadingOrder>`. "
        "Pages without one fall back to document order, which can scramble text (dataset card).",
        "- `pages_with_illegible`: pages containing U+FFFD, which the transcribers used for *illegible glyph*.",
        "",
        "## BHL page types",
        "",
        types.to_markdown(),
        "",
    ]
    (REPORTS / "01_dataset_check.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
