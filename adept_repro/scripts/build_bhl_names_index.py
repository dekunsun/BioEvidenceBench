"""
Build ADEPT's BHL names index (adept/.cache/bhl-names.parquet) with DuckDB.

Why not `adept assets bhl-names`?
  * Its download URL (www.biodiversitylibrary.org/data/hosted/data.zip, 2.45 GB) did
    answer from this container, but `create_bhl_names_index` reads pagename.txt
    (~217 M rows) into pandas. With 15 GB RAM and no swap that does not fit.
  * The same export tables are on the BHL open-data S3 bucket
    (s3://bhl-open-data/data/*.txt.gz), which DuckDB can stream from disk.

This script reproduces adept/assets.py:create_bhl_names_index step by step:
  pagename(PageID, NameConfirmed) LEFT JOIN page(PageID -> ItemID, SequenceOrder)
  -> item(ItemID -> TitleID) -> title(TitleID -> LanguageCode);
  keep LanguageCode == 'ENG'; drop LanguageCode; lower-case NameConfirmed.
Output columns and order: PageID, NameConfirmed, ItemID, SequenceOrder, TitleID.

BHLSearchTask loads the whole index into pandas at import time, which again does
not fit in 15 GB for all English pages. So we write:
  --full   the full English index (for the record / future use), and
  --subset an index restricted to the names ADEPT would query for the given taxa
           (taxon + WorldFlora synonyms, exactly as BHLSearchTask.search() does).
For those taxa, search() returns the same rows from the subset as from the full index.

Usage (ADEPT venv, duckdb installed):
  python adept_repro/scripts/build_bhl_names_index.py --data adept_repro/.assets/bhl-data \
      --full adept_repro/.assets/bhl-names-full.parquet \
      --subset vendor/ADEPT/adept/.cache/bhl-names.parquet \
      --taxa "Achillea millefolium" "Leersia hexandra"
"""
import argparse
from pathlib import Path

import duckdb


ITEM_COLS = ['ItemID', 'TitleID', 'ThumbnailPageID', 'BarCode', 'MARCItemID', 'CallNumber', 'VolumeInfo',
             'ItemURL', 'ItemTextURL', 'ItemPDFURL', 'ItemImagesURL', 'LocalID', 'Year', 'InstitutionName',
             'ZQuery', 'CreationDate', 'CopyrightStatus', 'RightsStatement', 'LicenseType', 'RightsHolder']
TITLE_COLS = ['TitleID', 'MARCBibID', 'MARCLeader', 'FullTitle', 'ShortTitle', 'PublicationDetails', 'CallNumber',
              'StartYear', 'EndYear', 'LanguageCode', 'TL2Author', 'TitleURL', 'CreationDate']


def tsv(path: Path, cols: list[str]) -> str:
    # BHL exports are tab separated, with a UTF-8 BOM and stray quote characters.
    # all_varchar + quote='' mirrors pandas' tolerant default closely enough
    # for the integer id columns we use.
    return (f"read_csv('{path}', delim='\t', header=true, quote='', escape='', all_varchar=true, "
            f"names={cols!r}, null_padding=true, ignore_errors=true)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", type=Path, required=True)
    ap.add_argument("--full", type=Path, required=True)
    ap.add_argument("--subset", type=Path)
    ap.add_argument("--taxa", nargs="*", default=[])
    args = ap.parse_args()

    con = duckdb.connect()
    con.execute("SET memory_limit='8GB'; SET preserve_insertion_order=false;")
    d = args.data
    if not args.full.exists():
        con.execute(f"""
        COPY (
          SELECT TRY_CAST(n.PageID AS BIGINT) AS PageID,
                 lower(n.NameConfirmed)        AS NameConfirmed,
                 TRY_CAST(p.ItemID AS BIGINT)  AS ItemID,
                 TRY_CAST(p.SequenceOrder AS BIGINT) AS SequenceOrder,
                 TRY_CAST(i.TitleID AS BIGINT) AS TitleID
          FROM {tsv(d/'pagename.txt.gz', ['NameBankID','NameConfirmed','PageID','CreationDate'])} n
          LEFT JOIN {tsv(d/'page.txt.gz', ['PageID','ItemID','SequenceOrder','Year','Volume','Issue','PagePrefix','PageNumber','PageTypeName','CreationDate'])} p
                 ON n.PageID = p.PageID
          LEFT JOIN {tsv(d/'item.txt.gz', ITEM_COLS)} i
                 ON p.ItemID = i.ItemID
          LEFT JOIN {tsv(d/'title.txt.gz', TITLE_COLS)} t
                 ON i.TitleID = t.TitleID
          WHERE t.LanguageCode = 'ENG'
        ) TO '{args.full}' (FORMAT parquet, COMPRESSION zstd)
        """)
    n = con.execute(f"SELECT count(*), count(DISTINCT NameConfirmed), count(DISTINCT PageID) FROM '{args.full}'").fetchone()
    print(f"full English index: {n[0]:,} rows, {n[1]:,} distinct names, {n[2]:,} pages -> {args.full}")

    if args.subset and args.taxa:
        from adept.worldflora import WorldFlora  # same synonym source as BHLSearchTask
        wf = WorldFlora()
        names = set()
        for taxon in args.taxa:
            names.add(taxon.lower())
            names |= {s.lower() for s in (wf.get_related_names(taxon) or [])}
        con.execute("CREATE TEMP TABLE q(name VARCHAR)")
        con.executemany("INSERT INTO q VALUES (?)", [[x] for x in sorted(names)])
        args.subset.parent.mkdir(parents=True, exist_ok=True)
        con.execute(f"COPY (SELECT f.* FROM '{args.full}' f JOIN q ON f.NameConfirmed = q.name) "
                    f"TO '{args.subset}' (FORMAT parquet)")
        m = con.execute(f"SELECT count(*) FROM '{args.subset}'").fetchone()[0]
        print(f"subset for {args.taxa}: {len(names)} query names, {m:,} rows -> {args.subset}")


if __name__ == "__main__":
    main()
