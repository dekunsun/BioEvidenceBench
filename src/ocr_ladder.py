"""How much of the gold survives each OCR model? An OCR-quality ladder on our 22 pages,
from FineBooks' public per-page outputs of every model on its BHL leaderboard. No LLM call.

    python src/ocr_ladder.py

For every OCR row in hf://buckets/finebooks/bhl-ocr-outputs (plus BHL's legacy OCR) and every
sample page, it computes
  page CER     case-insensitive, after the same normalisation as compute_cer.py
  word miss    share of the expert text's words the OCR does not contain
and for every gold mention (dev and test gold, `excluded` rows left out)
  preserved    the OCR text at the mention's place equals the gold text after the scorer's
               value normalisation (score.norm_value); the place is found by the scorer's own
               character alignment (score.char_map), exactly as for entity-span CER
  missing      the mention's place is not in the OCR text at all (a dropped block)
Preservation is an upper bound for what an extractor that never rewrites the source can get
right at value level: a misread name cannot be extracted correctly.

Exploratory (DEVIATIONS.md): decided after the test pages were unsealed. Texts are read from
FineBooks' bucket into data/cache/ and never committed; outputs carry numbers, the gold mention
text, and the few characters of OCR text at each mention's place (short quotes of public-domain
pages; the Datalab rows' outputs are under a modified OpenRAIL-M licence: quoted for evaluation only).
Writes results/ocr_ladder/{pages,mentions,summary}.csv and REPORT.md.
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import requests
from rapidfuzz.distance import Levenshtein

from common import CACHE, DATA, ROOT, normalize_for_cer, strip_markdown
from score import char_map, map_span, norm_value

BUCKET = "https://huggingface.co/buckets/finebooks/bhl-ocr-outputs/resolve"
OUT = ROOT / "results" / "ocr_ladder"
PRIMARY = ["taxon", "person", "locality", "institution", "date"]
_LIG = str.maketrans({"æ": "ae", "œ": "oe"})


def folded(s: str) -> str:
    """norm_value, then the two ligatures spelled out. Many modern OCR models write `TURDIDAE`
    for the printed `TURDIDÆ`: a change of letters the scorer does not accept, but one a reader
    (and a name database) would. Reported beside the strict measure, never instead of it."""
    return norm_value(s).translate(_LIG)


def bucket_file(path: str, dest: Path) -> Path:
    if not dest.exists():
        r = requests.get(f"{BUCKET}/{path}", timeout=300)
        r.raise_for_status()
        dest.write_bytes(r.content)
    return dest


def texts_for(row: str, meta: dict, pages: set[int]) -> dict[int, tuple[str, str]]:
    """{PageID: (markdown, finish_reason)} for our pages."""
    pq = bucket_file(meta["files"]["normalized"], CACHE / "bucket" / f"{row}_normalized.parquet")
    import pyarrow.parquet as papq
    have = set(papq.read_schema(pq).names)
    d = pd.read_parquet(pq, columns=[c for c in ("PageID", "markdown", "finish_reason") if c in have])
    if "finish_reason" not in d.columns:
        d["finish_reason"] = ""          # e.g. kraken / tesseract rows: not a token-generating model
    d = d[d.PageID.astype(int).isin(pages)]
    return {int(r.PageID): (r.markdown if isinstance(r.markdown, str) else "", str(r.finish_reason))
            for r in d.itertuples()}


def load_gold() -> pd.DataFrame:
    parts = []
    for f in ("gold_mentions_gloria.csv", "gold_mentions_gloria_test.csv"):
        g = pd.read_csv(ROOT / "gold" / f, dtype=str, keep_default_na=False)
        if "scan_text" not in g.columns:
            g["scan_text"] = ""
        parts.append(g)
    g = pd.concat(parts, ignore_index=True)
    g = g[(g.field != "none") & (g.adjudication != "excluded")].copy()
    g["page_id"], g["start"], g["end"] = g.page_id.astype(int), g.start.astype(int), g.end.astype(int)
    return g


def main() -> None:
    (CACHE / "bucket").mkdir(parents=True, exist_ok=True)
    rows = json.loads(bucket_file("manifest.json", CACHE / "bucket" / "manifest.json").read_text())["rows"]
    split = pd.read_csv(DATA / "sample_split.csv")
    book_of = dict(zip(split.PageID.astype(int), split.book))
    split_of = dict(zip(split.PageID.astype(int), split.split))
    pages = set(book_of)
    gold = load_gold()
    expert = {p: (DATA / "sample" / "expert" / f"{p}.txt").read_text(encoding="utf-8") for p in pages}

    sources = {"legacy (BHL)": ({p: ((DATA / "sample" / "legacy" / f"{p}.txt").read_text(encoding="utf-8"), "")
                                 for p in pages}, "BHL legacy OCR", "")}
    for row, meta in rows.items():
        print("fetching", row)
        sources[row] = (texts_for(row, meta, pages), meta.get("model", ""), meta.get("licence", ""))
    # Rows we produced ourselves (not in FineBooks' bucket): Mistral OCR through OpenRouter,
    # src/fetch_mistral_ocr_openrouter.py (exploratory; Mistral version not reported by OpenRouter).
    local = {"mistral-ocr (OpenRouter)": ("modern_mistral-ocr-openrouter", "Mistral OCR via OpenRouter file-parser",
                                          "Mistral / OpenRouter terms")}
    for name, (version, model, licence) in local.items():
        d = DATA / "text" / version
        if d.exists():
            sources[name] = ({p: ((d / f"{p}.txt").read_text(encoding="utf-8"), "") for p in pages
                              if (d / f"{p}.txt").exists()}, model, licence)

    page_rows, ment_rows = [], []
    for name, (texts, model, licence) in sources.items():
        for p in sorted(pages):
            raw, finish = texts.get(p, ("", "missing"))
            ocr = strip_markdown(raw) if name != "legacy (BHL)" else raw
            ref_n, ocr_n = normalize_for_cer(expert[p]).lower(), normalize_for_cer(ocr).lower()
            page_rows.append({"ocr": name, "model": model, "licence": licence, "page_id": p, "book": book_of[p],
                              "split": split_of[p], "finish_reason": finish,
                              "page_cer": round(Levenshtein.distance(ocr_n, ref_n) / max(len(ref_n), 1), 4)})
            cmap = char_map(expert[p], raw)
            for gm in gold[gold.page_id == p].itertuples():
                aligned = sum(cmap[i] >= 0 for i in range(gm.start, min(gm.end, len(cmap))))
                span = map_span(cmap, gm.start, gm.end)
                missing = span is None or aligned < 0.5 * (gm.end - gm.start)
                sub = "" if missing else raw[span[0]:span[1]]
                ok = bool((not missing) and (norm_value(sub) == norm_value(gm.text)
                                             or (gm.scan_text and norm_value(sub) == norm_value(gm.scan_text))))
                ok_f = bool((not missing) and (folded(sub) == folded(gm.text)
                                               or (gm.scan_text and folded(sub) == folded(gm.scan_text))))
                ment_rows.append({"ocr": name, "page_id": p, "book": book_of[p], "split": split_of[p],
                                  "field": gm.field, "start": gm.start, "end": gm.end, "gold_text": gm.text,
                                  "ocr_text": sub, "preserved": ok, "preserved_folded": ok_f,
                                  "missing": missing})
    pg, mt = pd.DataFrame(page_rows), pd.DataFrame(ment_rows)

    def summ(by):
        prim = mt[mt.field.isin(PRIMARY)]
        a = pg.groupby(by).agg(pages=("page_id", "nunique"), median_page_cer=("page_cer", "median"),
                               mean_page_cer=("page_cer", "mean"),
                               looped_pages=("finish_reason", lambda s: int((s == "length").sum())))
        b = prim.groupby(by).agg(mentions=("preserved", "size"), preserved=("preserved", "mean"),
                                 preserved_folded=("preserved_folded", "mean"), missing=("missing", "mean"))
        out = a.join(b).reset_index()
        for f in PRIMARY + ["vernacular"]:
            s = mt[mt.field == f].groupby(by).preserved.mean().rename(f"preserved_{f}")
            out = out.merge(s.reset_index(), on=by, how="left")
        return out.round(4)

    summary = summ(["ocr", "book"]).sort_values(["book", "preserved"], ascending=[True, False])
    OUT.mkdir(parents=True, exist_ok=True)
    pg.to_csv(OUT / "pages.csv", index=False)
    mt.to_csv(OUT / "mentions.csv", index=False)
    summary.to_csv(OUT / "summary.csv", index=False)
    meta_rows = pd.DataFrame([{"ocr": k, "model": v[1], "licence": v[2]} for k, v in sources.items()])
    meta_rows.to_csv(OUT / "ocr_models.csv", index=False)

    show = ["ocr", "median_page_cer", "preserved", "preserved_folded", "missing", "preserved_taxon", "preserved_person",
            "preserved_locality", "looped_pages"]
    lines = ["# OCR ladder: how much of the gold survives each OCR model (exploratory)", "",
             "22 sample pages (6 dev + 16 test), all FineBooks leaderboard rows plus BHL legacy OCR. "
             "`preserved` = share of primary gold mentions whose text survives intact at their place "
             "(an upper bound for value-level extraction when values are sliced from the source); "
             "`missing` = the place is not in the OCR text at all. No LLM call. Decided after the test "
             "pages were unsealed: exploratory, see DEVIATIONS.md.", ""]
    for book in ("Butler", "Reeve"):
        lines += [f"## {book}", "", summary[summary.book == book][show].to_markdown(index=False), ""]
    (OUT / "REPORT.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
