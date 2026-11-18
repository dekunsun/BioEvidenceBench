"""Shared paths, URLs and small helpers used by every script in src/.

Nothing in here talks to a model. Everything is plain data plumbing.
"""
from __future__ import annotations

import hashlib
import re
import unicodedata
from pathlib import Path

import duckdb

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
REPORTS = DATA / "reports"   # small markdown reports, committed
CACHE = DATA / "cache"       # large intermediate Parquet files, NOT committed
TEXT = DATA / "text"         # page texts (expert / legacy / modern), NOT committed

# ---------------------------------------------------------------------------
# Public data sources
# ---------------------------------------------------------------------------
# Expert transcriptions (IMPACT-BHL ground truth, CC-BY 3.0). Text only; the
# images live in a separate folder of the same repo and are not downloaded.
GT_PARQUET = "hf://datasets/finebooks/bhl-impact-gt/metadata.parquet"

# BHL catalogue metadata (CC0). One folder of Parquet shards per BHL table.
MD = "hf://datasets/finebooks/bhl-metadata/data"
MD_ITEM = f"{MD}/item/*.parquet"
MD_TITLE = f"{MD}/title/*.parquet"
MD_PAGE = f"{MD}/page/*.parquet"
MD_PAGE_NAME = f"{MD}/page_name/*.parquet"

# The two English works in bhl-impact-gt. These are the core experiment.
# (load_gt.py re-derives this from the catalogue language code and stops if
# the two disagree, so this list is a check, not an assumption.)
ENGLISH_BOOKS = {
    "birdsofgreatbrit02butl": "Butler 1907, Birds of Great Britain and Ireland v.2",
    "conchologiaiconi05reev": "Reeve 1849, Conchologia iconica v.5",
}
BOOK_SHORT = {"birdsofgreatbrit02butl": "Butler", "conchologiaiconi05reev": "Reeve"}


def legacy_ocr_url(item_id: int, page_id: int, seq: int) -> str:
    """Per-page BHL OCR on BHL's own open-data S3 bucket.

    This is the same OCR text BHL serves on its website, already split into
    one file per page, so we never have to slice a whole-book text file.
    Pattern documented at https://github.com/gbhl/bhl-open-data
    """
    return (
        "https://bhl-open-data.s3.amazonaws.com/ocr/"
        f"item-{item_id:06d}/item-{item_id:06d}-{page_id:08d}-{seq:04d}.txt"
    )


def bhl_page_url(page_id: int) -> str:
    """Human-facing BHL page viewer (open it in a browser to see the scan)."""
    return f"https://www.biodiversitylibrary.org/page/{page_id}"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def connect() -> duckdb.DuckDBPyConnection:
    """DuckDB connection that can read hf:// paths directly."""
    con = duckdb.connect()
    # httpfs is auto-loaded for hf:// in recent DuckDB; loading it explicitly
    # gives a clearer error on old versions.
    con.sql("INSTALL httpfs; LOAD httpfs;")
    return con


def sha256_text(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


_QUOTES = str.maketrans({
    "‘": "'", "’": "'", "‚": "'", "‛": "'",
    "“": '"', "”": '"', "„": '"', "‟": '"',
    "—": "-", "–": "-",
})
_WS = re.compile(r"\s+")


def normalize_for_cer(s: str) -> str:
    """Light normalisation applied to BOTH texts before computing CER.

    Why: we want CER to measure misread characters, not typographic
    conventions the expert transcribers chose to keep.
      * NFKC folds ligatures (fl -> fl) and long-s (U+017F -> s).
      * Curly quotes and dashes become ASCII.
      * Any run of whitespace (spaces, line breaks) becomes one space,
        because legacy OCR and the transcription break lines differently.
    Case and punctuation are kept: they matter for names and dates.
    """
    s = unicodedata.normalize("NFKC", s).translate(_QUOTES)
    return _WS.sub(" ", s).strip()


def collapse_ws(s: str) -> str:
    """Whitespace-only normalisation, for the stricter 'raw' CER."""
    return _WS.sub(" ", s).strip()
