"""Copy the expert transcriptions of the 22 sample pages into the repo, so
they can be read and labelled on GitHub without running Python.

Only these pages are committed (not the whole book). The text is the IMPACT-BHL
ground truth, CC-BY 3.0, see data/sample/ATTRIBUTION.md.

Outputs (committed)
  data/sample/expert/<PageID>.txt        exact expert text; gold offsets point into this
  data/sample/expert_view/<PageID>.txt   same text with each line's starting offset
  data/sample/manifest.csv               split, book, stratum, chars, SHA-256

Run:  python src/export_sample_texts.py     (after load_gt.py and split_sample.py)
"""
from __future__ import annotations

import pandas as pd

from common import DATA, TEXT, sha256_text

OUT = DATA / "sample"


def main() -> None:
    split = pd.read_csv(DATA / "sample_split.csv")
    for sub in ("expert", "expert_view"):
        (OUT / sub).mkdir(parents=True, exist_ok=True)
    rows = []
    for r in split.itertuples():
        text = (TEXT / "expert" / f"{r.PageID}.txt").read_text(encoding="utf-8")
        view = (TEXT / "expert_view" / f"{r.PageID}.txt").read_text(encoding="utf-8")
        (OUT / "expert" / f"{r.PageID}.txt").write_text(text, encoding="utf-8")
        (OUT / "expert_view" / f"{r.PageID}.txt").write_text(view, encoding="utf-8")
        rows.append({"page_id": r.PageID, "split": r.split, "book": r.book, "stratum": r.stratum,
                     "chars": len(text), "sha256": sha256_text(text), "bhl_url": r.bhl_url})
    # The two OCR versions of the same pages, exactly as fetched. BHL refreshes its OCR
    # (and NHM proposes to re-OCR all of BHL), so the legacy text could not be re-fetched later.
    for version in ("legacy", "modern_dots-mocr"):
        (OUT / version).mkdir(parents=True, exist_ok=True)
        for r in split.itertuples():
            text = (TEXT / version / f"{r.PageID}.txt").read_text(encoding="utf-8")
            (OUT / version / f"{r.PageID}.txt").write_text(text, encoding="utf-8")
            rows.append({"page_id": r.PageID, "split": r.split, "book": r.book, "stratum": r.stratum,
                         "chars": len(text), "sha256": sha256_text(text), "bhl_url": r.bhl_url,
                         "version": version})
    man = pd.DataFrame(rows)
    man["version"] = man.version.fillna("expert")
    man.to_csv(OUT / "manifest.csv", index=False)
    print(f"Wrote {len(rows)} pages to {OUT}")


if __name__ == "__main__":
    main()
