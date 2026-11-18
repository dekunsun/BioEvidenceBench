"""Task 4: join TaxonFinder name counts per page and PROPOSE a stratified
sample of ~24 pages (12 per book) for Gloria to approve.

Nothing here is a label. The signals below are *proxies* used only to make
sure the sample contains different kinds of pages:

  n_names        distinct TaxonFinder names on the page (bhl-metadata
                 page_name). TaxonFinder ran on the LEGACY OCR, so pages
                 with bad OCR tend to have fewer names found. It is a
                 page-level list, with no positions and no localities.
  latin_hint     rough count of Latin-looking binomials in the expert text
  place_hint     rough count of locality cues in the expert text
                 ("Hab.", "Island", "in/at/near/from <Capitalised word>")
  date_hint      years 1600-1913 and month names in the expert text
  cer_nocase     legacy-OCR CER from compute_cer.py

Strata (per book; a page may qualify for several, it is listed under one):
  poor_ocr      cer_nocase >= 10% and word_miss >= 5% (really misread, not
                just re-ordered)                                    3 pages
  entity_rich   n_names >= max(3, 75th percentile of the book's pages that
                have any name)                                      4 pages
  low_density   n_names 1-2                                         3 pages
  no_entities   n_names = 0 and no Latin, place or date hint        2 pages
Within each stratum we take pages at evenly spaced CER ranks, so each
stratum spans its book's CER range instead of clustering. Ties and repeats
are broken deterministically, so re-running gives the same proposal.

Pool: English pages with >= 200 expert characters (shorter pages make CER
unstable and hold almost nothing to extract), minus index and contents
pages. Those are lists of names with dot leaders and page numbers; they
would dominate the entity-rich and poor-OCR strata, and they defeat the
proxies (Reeve's indexes list bare epithets such as "ampullaceum,
Philippi", so TaxonFinder finds 0 names on a page full of species).
They are kept in page_signals.csv with is_list_page = True.

Outputs
  data/cache/page_name_english.parquet   (not committed)
  data/page_signals.csv                  every pool page with its signals
  data/sample_proposal.csv               the 24 proposed pages + reserves
  data/reports/03_sample_proposal.md     the proposal, for approval

Run:  python src/propose_sample.py
"""
from __future__ import annotations

import re

import numpy as np
import pandas as pd

from common import CACHE, DATA, MD_PAGE_NAME, REPORTS, bhl_page_url, connect

PER_BOOK = {"poor_ocr": 3, "entity_rich": 4, "low_density": 3, "no_entities": 2}
ORDER = ["poor_ocr", "entity_rich", "low_density", "no_entities"]  # fill order
RESERVES = 2          # extra candidates per stratum per book, in case one is rejected
MIN_CHARS = 200

_STOP = {"The", "This", "That", "These", "Those", "It", "In", "A", "An", "He", "She", "They",
         "We", "When", "Where", "As", "At", "On", "Of", "If", "But", "And", "Its", "His",
         "Their", "There", "Here", "Some", "Many", "Mr", "Mrs", "Dr", "Plate", "Species", "Fig"}
_LATIN = re.compile(r"\b([A-Z][a-z]+)\.? ([a-z]{3,}(?:us|um|a|ae|is|es|ii|i|orum|arum|ensis|oides|ata|ina|ella|ica))\b")
_PLACE = re.compile(r"\bHab\.|\bHabitat\b|\b(?:Island|Islands|Isle|Isles|coast|County|shire|River|Bay|Lake|Mountains?)\b"
                    r"|\b(?:in|at|near|from) [A-Z][a-z]{2,}")
_DATE = re.compile(r"\b1[6-9]\d\d\b|\b(?:January|February|March|April|May|June|July|August|"
                   r"September|October|November|December|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sept?|Oct|Nov|Dec)\.?\b")


_LEADER = re.compile(r"(?:\.\s*){2,}|(?:-\s*){3,}|\u2026")   # ". . ." or "- - -" leaders
_LIST_HEAD = re.compile(r"^\W*(?:INDEX|CONTENTS|LIST OF)\b", re.M)


def is_list_page(text: str, page_type: str | None) -> bool:
    """Index / table-of-contents pages: most lines are 'name .... page'."""
    if page_type and ("Index" in page_type or "Contents" in page_type):
        return True
    lines = [l for l in text.split("\n") if l.strip()]
    leader_share = sum(bool(_LEADER.search(l)) for l in lines) / max(len(lines), 1)
    return leader_share > 0.3 or (bool(_LIST_HEAD.search(text[:300])) and leader_share > 0.1)


def latin_hint(t: str) -> int:
    return sum(1 for g, _ in _LATIN.findall(t) if g not in _STOP)


def page_name_counts(page_ids: list[int]) -> pd.DataFrame:
    path = CACHE / "page_name_english.parquet"
    if not path.exists():
        print("Querying page_name on Hugging Face (about 2-3 minutes, cached afterwards) ...")
        con = connect()
        ids = ",".join(map(str, page_ids))
        con.sql(f"""
            COPY (SELECT DISTINCT PageID, NameConfirmed, NameBankID
                  FROM '{MD_PAGE_NAME}'
                  WHERE PageID BETWEEN {min(page_ids)} AND {max(page_ids)}  -- lets DuckDB skip row groups
                    AND PageID IN ({ids}))
            TO '{path}' (FORMAT parquet)
        """)
    names = pd.read_parquet(path)
    agg = names.groupby("PageID").agg(
        n_names=("NameConfirmed", "nunique"),
        names_sample=("NameConfirmed", lambda s: "; ".join(sorted(s)[:6])))
    return agg.reset_index()


def pick_spread(cands: pd.DataFrame, k: int, taken: set[int]) -> list[int]:
    """Pick k pages at evenly spaced CER ranks, skipping pages already taken."""
    c = cands[~cands.PageID.isin(taken)].sort_values(["cer_nocase", "PageID"]).reset_index(drop=True)
    if len(c) <= k:
        return c.PageID.tolist()
    chosen: list[int] = []
    for pos in np.linspace(0, len(c) - 1, k):
        # nearest unused rank to the target position
        for off in sorted(range(len(c)), key=lambda i: abs(i - pos)):
            pid = int(c.PageID[off])
            if pid not in chosen:
                chosen.append(pid)
                break
    return chosen


def main() -> None:
    gt = pd.read_parquet(CACHE / "gt_english.parquet")
    cer = pd.read_csv(DATA / "cer_legacy.csv")
    pool = gt.merge(cer[["PageID", "book", "cer_nocase", "word_miss", "cer_band"]], on="PageID")
    pool = pool[pool.gt_chars >= MIN_CHARS].copy()
    pool["is_list_page"] = [is_list_page(t, pt) for t, pt in zip(pool.text, pool.PageTypeName)]

    pool = pool.merge(page_name_counts(gt.PageID.tolist()), on="PageID", how="left")
    pool["n_names"] = pool.n_names.fillna(0).astype(int)
    pool["names_sample"] = pool.names_sample.fillna("")
    pool["latin_hint"] = pool.text.map(latin_hint)
    pool["place_hint"] = pool.text.map(lambda t: len(_PLACE.findall(t)))
    pool["date_hint"] = pool.text.map(lambda t: len(_DATE.findall(t)))

    # Stratum membership (a page can be in several).
    rich_cut = {b: max(3, int(np.percentile(d.n_names[(d.n_names > 0) & ~d.is_list_page], 75)))
                for b, d in pool.groupby("book")}
    pool["is_poor_ocr"] = (pool.cer_nocase >= 0.10) & (pool.word_miss >= 0.05)
    pool["is_entity_rich"] = pool.n_names >= pool.book.map(rich_cut)
    pool["is_low_density"] = pool.n_names.between(1, 2)
    pool["is_no_entities"] = ((pool.n_names == 0) & (pool.latin_hint == 0)
                              & (pool.place_hint == 0) & (pool.date_hint == 0))
    pool["bhl_url"] = pool.PageID.map(bhl_page_url)

    sig_cols = ["PageID", "book", "SequenceOrder", "PageNumber", "PageTypeName", "gt_chars",
                "cer_nocase", "word_miss", "cer_band", "n_names", "latin_hint", "place_hint",
                "date_hint", "is_poor_ocr", "is_entity_rich", "is_low_density", "is_no_entities",
                "names_sample", "bhl_url"]
    sig_cols.insert(sig_cols.index("is_poor_ocr"), "is_list_page")
    pool[sig_cols].sort_values(["book", "SequenceOrder"]).to_csv(DATA / "page_signals.csv", index=False)
    n_list = pool.groupby("book").is_list_page.sum().to_dict()
    pool = pool[~pool.is_list_page]

    rows, avail = [], []
    for book, d in pool.groupby("book"):
        taken: set[int] = set()
        for stratum in ORDER:
            cands = d[d[f"is_{stratum}"]]
            avail.append({"book": book, "stratum": stratum, "candidates": len(cands),
                          "wanted": PER_BOOK[stratum]})
            main_pick = pick_spread(cands, PER_BOOK[stratum], taken)
            taken |= set(main_pick)
            reserve = pick_spread(cands, RESERVES, taken)
            taken |= set(reserve)
            for role, ids in (("proposed", main_pick), ("reserve", reserve)):
                for pid in ids:
                    rows.append({"PageID": pid, "stratum": stratum, "role": role})
    prop = pd.DataFrame(rows).merge(pool[sig_cols], on="PageID")
    prop["also_qualifies_for"] = prop.apply(
        lambda r: ", ".join(s for s in ORDER if s != r.stratum and r[f"is_{s}"]), axis=1)
    prop["approved"] = ""   # for Gloria: y / n
    out_cols = ["role", "book", "stratum", "PageID", "SequenceOrder", "PageNumber", "cer_nocase",
                "cer_band", "word_miss", "n_names", "latin_hint", "place_hint", "date_hint",
                "also_qualifies_for", "names_sample", "bhl_url", "approved"]
    prop = prop[out_cols].sort_values(["role", "book", "stratum", "cer_nocase"],
                                      key=lambda s: s.map({"proposed": 0, "reserve": 1}) if s.name == "role" else s)
    prop.to_csv(DATA / "sample_proposal.csv", index=False)

    main_set = prop[prop.role == "proposed"]
    avail = pd.DataFrame(avail)
    bands = pd.crosstab(main_set.book, main_set.cer_band).reindex(columns=["low", "medium", "high"], fill_value=0)
    pool_bands = pd.crosstab(pool.book, pool.cer_band).reindex(columns=["low", "medium", "high"], fill_value=0)
    show = ["book", "stratum", "PageID", "PageNumber", "cer_nocase", "n_names", "place_hint",
            "date_hint", "also_qualifies_for", "bhl_url"]
    lines = [
        "# 03 Proposed stratified sample — **awaiting Gloria's approval**",
        "",
        "Generated by `src/propose_sample.py`. Nothing here is a label: the signals are proxies used only",
        "to make sure the sample mixes different kinds of pages. To approve, fill the `approved` column",
        "(y/n) in `data/sample_proposal.csv`; swap any rejected page for a `reserve` page from the same",
        "book and stratum.",
        "",
        f"Pool: {len(pool)} English pages with at least {MIN_CHARS} expert characters, after removing",
        f"index/contents pages {n_list} (lists of names; see the docstring for why).",
        f"Entity-rich cut-off (distinct TaxonFinder names): {rich_cut}.",
        "",
        "## Candidates available per stratum",
        "",
        avail.pivot(index="stratum", columns="book", values="candidates").loc[ORDER].to_markdown(),
        "",
        "## Proposed pages (24)",
        "",
        main_set[show].to_markdown(index=False),
        "",
        "## CER coverage",
        "",
        "Proposed sample:",
        "",
        bands.to_markdown(),
        "",
        "Whole pool, for comparison:",
        "",
        pool_bands.to_markdown(),
        "",
        "## Caveats Gloria should weigh before approving",
        "",
        "1. **Book and OCR quality are confounded.** Butler is mostly low/medium CER; Reeve is almost",
        "   entirely medium/high. Neither book alone covers all three CER bands. A pooled F1-vs-CER plot",
        "   would partly compare *books* (birds prose vs Latin shell descriptions) rather than OCR quality.",
        "   Suggestion: plot each book separately and treat the cross-book comparison as descriptive only.",
        "   The modern-OCR and expert versions of the *same* page are the cleaner test of RQ1, because",
        "   they hold the page constant.",
        "2. **TaxonFinder counts are biased by OCR.** `n_names` was computed on the legacy OCR, so a page",
        "   that is rich in names but badly OCR'd can look 'low density'. That is one reason the strata",
        "   overlap and why `latin_hint` (computed on the expert text) is shown next to it.",
        "3. **'No entities' is a guess.** It means no TaxonFinder name and no Latin, place or date cue in",
        "   the expert text. Butler pages can still name birds in English (\"the Hedge-Sparrow\"). Whether",
        "   vernacular names count as `taxon` is an open question in `ANNOTATION_GUIDE.md`.",
        "4. **Index pages are a finding in their own right.** Reeve's indexes list bare epithets under a",
        "   genus heading, and TaxonFinder found few or no names on them. They are excluded here, but they",
        "   are a good stress test for the rule baseline later.",
        "5. Pages shorter than 200 characters (most plate captions in Reeve) are excluded. If you want",
        "   plate-caption pages as their own stratum, lower `MIN_CHARS`.",
        "",
    ]
    (REPORTS / "03_sample_proposal.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
