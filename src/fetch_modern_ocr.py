"""Fetch a modern open OCR model's output for our pages from FineBooks' public
output bucket, instead of running the model ourselves (no GPU needed).

FineBooks ran every model on its BHL OCR leaderboard over all 2,165
bhl-impact-gt pages and published the per-page output:
  hf://buckets/finebooks/bhl-ocr-outputs   (README, manifest.json, rows/<slug>/...)
We take `rows/<slug>/normalized.parquet`, whose `markdown` column is the text
FineBooks scored, and keep our English pages.

Default row: dots-mocr (rednote-hilab/dots.mocr). It had the lowest CER on the
board (FineBooks RESULTS.md, norm 2026-10-30a), and its outputs are MIT
licensed. Other rows can be fetched with --row (see manifest.json). Datalab rows
(surya-ocr25, chandra-ocr2, indra-ocr) carry use restrictions; read their
LICENSE first.

What the output looks like: Markdown, one paragraph per line, with
**bold**/*italic* kept, and NO coordinates of any kind. So this text version
can be grounded to the page and to a text span, not to a region of the scan.

Outputs
  data/text/modern_<row>/<PageID>.txt       the `markdown` field, as published (not committed)
  data/text/manifest_modern_<row>.csv       SHA-256, finish reason, model revision, licence

Run:  python src/fetch_modern_ocr.py [--row dots-mocr]
"""
from __future__ import annotations

import argparse
import json

import pandas as pd
import requests

from common import CACHE, TEXT, sha256_text

BUCKET = "https://huggingface.co/buckets/finebooks/bhl-ocr-outputs/resolve"


def download(path: str, dest) -> None:
    if dest.exists():
        return
    r = requests.get(f"{BUCKET}/{path}", timeout=120)
    r.raise_for_status()
    dest.write_bytes(r.content)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--row", default="dots-mocr")
    row = ap.parse_args().row

    (CACHE / "bucket").mkdir(parents=True, exist_ok=True)
    man_path = CACHE / "bucket" / "manifest.json"
    download("manifest.json", man_path)
    meta = json.loads(man_path.read_text())["rows"][row]
    pq = CACHE / "bucket" / f"{row}_normalized.parquet"
    download(meta["files"]["normalized"], pq)

    gt = pd.read_parquet(CACHE / "gt_english.parquet")
    want = set(gt.loc[gt.gt_chars > 0, "PageID"].astype(str))
    out = pd.read_parquet(pq, columns=["PageID", "markdown", "finish_reason", "error"])
    out = out[out.PageID.isin(want)]

    version = f"modern_{row}"
    (TEXT / version).mkdir(parents=True, exist_ok=True)
    recs = []
    for r in out.itertuples():
        text = r.markdown if isinstance(r.markdown, str) else ""
        (TEXT / version / f"{r.PageID}.txt").write_text(text, encoding="utf-8")
        recs.append({
            "page_id": int(r.PageID), "version": version, "chars": len(text),
            "sha256": sha256_text(text),
            # "length" = the model hit its token limit (usually a loop). FineBooks
            # excludes such pages from its board; we keep them and flag them.
            "finish_reason": r.finish_reason, "error": r.error if isinstance(r.error, str) else "",
            "model": meta["model"], "model_revision": meta.get("model_revision"),
            "licence": meta.get("licence"),
            "source": f"hf://buckets/finebooks/bhl-ocr-outputs/{meta['files']['normalized']}",
        })
    man = pd.DataFrame(recs)
    man.to_csv(TEXT / f"manifest_{version}.csv", index=False)
    missing = len(want) - len(man)
    print(f"{row} ({meta['model']}, licence {meta.get('licence')}): {len(man)} pages written, "
          f"{missing} missing, finish_reason counts {man.finish_reason.value_counts().to_dict()}")


if __name__ == "__main__":
    main()
