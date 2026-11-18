"""Task 3a: fetch BHL's legacy OCR for every English GT page that has text.

Source: BHL's open-data S3 bucket, one text file per page (see
common.legacy_ocr_url). We use it instead of
https://www.biodiversitylibrary.org/itemtext/<ItemID> because
  * it is already split per page, so there is no slicing step to get wrong;
  * the BHL website sits behind a Cloudflare bot check that blocks scripts
    from cloud machines (seen on 2026-11-18), while the S3 bucket does not.
It is BHL's own OCR text. Spot check: Reeve PageID 8967091 reads
"vvhich lost" and "Stillmgfleet" where the expert transcription has
"which lost" and "Stillingfleet". Note that BHL refreshes OCR weekly, so
we record the fetch time and a SHA-256 hash of every file.

Outputs
  data/text/legacy/<PageID>.txt      OCR text exactly as served (not committed)
  data/text/manifest_legacy.csv      URL, HTTP status, bytes, SHA-256, fetch time

Run:  python src/fetch_legacy_ocr.py          (skips pages already fetched)
"""
from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

import pandas as pd
import requests

from common import CACHE, TEXT, legacy_ocr_url, sha256_text

OUT = TEXT / "legacy"
WORKERS = 6          # be polite to the bucket
RETRIES = 4


def fetch(row) -> dict:
    url = legacy_ocr_url(int(row.ItemID), int(row.PageID), int(row.SequenceOrder))
    path = OUT / f"{row.PageID}.txt"
    rec = {"page_id": row.PageID, "version": "legacy", "source": url}
    if path.exists():
        text = path.read_text(encoding="utf-8")
        return rec | {"status": "cached", "chars": len(text), "sha256": sha256_text(text),
                      "fetched_at": None}
    for attempt in range(RETRIES):
        try:
            r = requests.get(url, timeout=30)
            if r.status_code == 200:
                # BHL serves UTF-8. Decode explicitly; never let requests guess.
                text = r.content.decode("utf-8")
                path.write_text(text, encoding="utf-8")
                return rec | {"status": 200, "chars": len(text), "sha256": sha256_text(text),
                              "fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds")}
            if r.status_code in (403, 404):
                return rec | {"status": r.status_code, "chars": None, "sha256": None,
                              "fetched_at": None}
        except requests.RequestException:
            pass
        time.sleep(2 ** attempt)
    return rec | {"status": "failed", "chars": None, "sha256": None, "fetched_at": None}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    gt = pd.read_parquet(CACHE / "gt_english.parquet")
    todo = gt[gt.gt_chars > 0]
    print(f"Fetching legacy OCR for {len(todo)} pages ...")
    with ThreadPoolExecutor(WORKERS) as pool:
        recs = list(pool.map(fetch, todo.itertuples()))
    man = pd.DataFrame(recs)

    # Keep the original fetch time for files fetched on an earlier run.
    old_path = TEXT / "manifest_legacy.csv"
    if old_path.exists():
        old = pd.read_csv(old_path).set_index("page_id")["fetched_at"]
        man["fetched_at"] = man.fetched_at.fillna(man.page_id.map(old))
    man.to_csv(old_path, index=False)
    print(man.status.value_counts().to_string())


if __name__ == "__main__":
    main()
