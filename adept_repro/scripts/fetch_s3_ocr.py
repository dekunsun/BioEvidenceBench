"""
Fill ADEPT's local OCR archive (adept/.cache/bhl-ocr-archive/) from the BHL
open-data S3 bucket, for exactly the pages ADEPT's BHLSearchTask will ask for.

Why: `adept assets bhl-ocr` downloads the full BHL OCR export from Figshare
(44.5 GB for the 2025-03-03 version ADEPT defaults to; 46.7 GB for the
2026-11-15 version) and the BHL page-text API is behind a Cloudflare challenge
from this container. The S3 bucket holds the same per-page OCR files:
    s3://bhl-open-data/ocr/item-<ItemID:06>/item-<ItemID:06>-<PageID:08>-<Seq:04>.txt
ADEPT's BHLTextTask.archive_get_text() reads
    <BHL_OCR_ARCHIVE_PATH>/<ItemID:06>-<PageID:08>-<Seq:04>.txt
so we only rename. No ADEPT code is changed by this step.

Pages are selected with ADEPT's own BHLSearchTask.search() (taxon + WorldFlora
synonyms against the names index), so the archive holds what ADEPT would read.
Pages missing from S3 are logged; ADEPT would then fall back to the (blocked) API.

Usage (ADEPT venv):
  python adept_repro/scripts/fetch_s3_ocr.py --taxa "Leersia hexandra" --log adept_repro/outputs/s3_fetch_leersia.csv
  python adept_repro/scripts/fetch_s3_ocr.py --pages pages.csv   # columns PageID,ItemID,SequenceOrder
"""
import argparse
import csv
import hashlib
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import requests

S3 = "https://bhl-open-data.s3.amazonaws.com"


def s3_key(item_id: int, page_id: int, seq: int) -> str:
    return f"ocr/item-{item_id:06d}/item-{item_id:06d}-{page_id:08d}-{seq:04d}.txt"


def fetch(row, archive: Path, session: requests.Session):
    item_id, page_id, seq = int(row["ItemID"]), int(row["PageID"]), int(row["SequenceOrder"])
    target = archive / f"{item_id:06d}-{page_id:08d}-{seq:04d}.txt"
    key = s3_key(item_id, page_id, seq)
    if target.exists():
        data = target.read_bytes()
        return {"PageID": page_id, "ItemID": item_id, "SequenceOrder": seq, "s3_key": key,
                "status": "cached", "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}
    for attempt in range(4):  # the container's proxy occasionally drops a connection
        try:
            r = session.get(f"{S3}/{key}", timeout=60)
            break
        except requests.RequestException:
            if attempt == 3:
                raise
            time.sleep(2 ** attempt)
    if r.status_code != 200:
        return {"PageID": page_id, "ItemID": item_id, "SequenceOrder": seq, "s3_key": key,
                "status": f"http_{r.status_code}", "bytes": 0, "sha256": ""}
    target.write_bytes(r.content)
    return {"PageID": page_id, "ItemID": item_id, "SequenceOrder": seq, "s3_key": key,
            "status": "ok", "bytes": len(r.content), "sha256": hashlib.sha256(r.content).hexdigest()}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--taxa", nargs="*", default=[])
    ap.add_argument("--pages", type=Path, help="CSV with PageID,ItemID,SequenceOrder")
    ap.add_argument("--log", type=Path, required=True)
    ap.add_argument("--workers", type=int, default=16)
    args = ap.parse_args()

    from adept.config import BHL_OCR_ARCHIVE_PATH

    rows = []
    if args.taxa:
        from adept.tasks.description.bhl.search import BHLSearchTask
        for taxon in args.taxa:
            df = BHLSearchTask(taxon=taxon).search()
            print(f"{taxon}: {len(df)} name occurrences, {df.PageID.nunique()} pages")
            rows += df[["PageID", "ItemID", "SequenceOrder"]].drop_duplicates().to_dict("records")
    if args.pages:
        with args.pages.open() as f:
            rows += list(csv.DictReader(f))

    session = requests.Session()
    with ThreadPoolExecutor(args.workers) as ex:
        results = list(ex.map(lambda r: fetch(r, BHL_OCR_ARCHIVE_PATH, session), rows))

    args.log.parent.mkdir(parents=True, exist_ok=True)
    with args.log.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(results[0].keys()) if results else ["PageID"])
        w.writeheader()
        w.writerows(results)
    statuses = {}
    for r in results:
        statuses[r["status"]] = statuses.get(r["status"], 0) + 1
    print(f"{len(results)} pages -> {BHL_OCR_ARCHIVE_PATH}: {statuses}")


if __name__ == "__main__":
    main()
