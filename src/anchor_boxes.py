"""Level 3 (image) grounding by local quote anchors (exploratory, DEVIATIONS.md).

A G1 extraction gives each value as a slice [start, end) of the text the model read. This script
finds where that slice sits on the scan, using an OCR engine that reports positions (OCRia-nano-1
through LiteParse, run locally on CPU) instead of aligning whole pages. Whole-page alignment breaks
when two readers order a page differently (two columns, tables, the two-line notes of the 本草綱目);
a local anchor does not care about page order:

  1. context = the value plus up to CONTEXT characters on each side, taken from the text the model read;
  2. every OCR line, and every pair of consecutive OCR lines (for values broken across lines), is scored
     against the context with rapidfuzz partial alignment;
  3. the best-scoring place is kept if its score >= threshold; inside it the value itself is aligned,
     and its box is interpolated from the line box by character position (OCRia-nano-1 reports one box
     per line, not per word, so the box granularity is `line_interp`);
  4. otherwise the value is NOT given the nearest box. It is marked
        text_verified_box_missing  (text evidence holds, no image anchor), or
        box_ambiguous              (another, different place scores within AMBIG_MARGIN of the best).

    python src/anchor_boxes.py nano <page_id> [<page_id> ...]         # run OCRia-nano-1, cache JSON
    python src/anchor_boxes.py tune <run_id> <version> [--split dev]   # dev only: threshold sweep vs hOCR

The threshold is chosen on dev pages only (`tune`) and frozen before any test page is scored.
OCRia-nano-1 weights: OCRia-nano-1 Model License (free for research, publishing allowed); LiteParse
Apache-2.0. The `lit` command comes from `pip install liteparse` + `lit models pull ocria-nano`;
set LIT=/path/to/lit if it is not on PATH. Cached outputs go to data/cache/nano/ (not committed).
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

from rapidfuzz import fuzz

CONTEXT = 15          # characters of context on each side of the value
AMBIG_MARGIN = 2.0    # a different place within this many points of the best -> ambiguous
DEFAULT_THRESHOLD = 65.0


@dataclass
class Item:
    text: str
    x: float
    y: float
    w: float
    h: float
    conf: float | None = None


def items_from_nano(page_json: dict) -> list[Item]:
    return [Item(t["text"], t["x"], t["y"], t["width"], t["height"], t.get("confidence"))
            for t in page_json["text_items"] if t.get("text", "").strip()]


def context_of(text: str, start: int, end: int, k: int = CONTEXT) -> tuple[str, int, int]:
    """Context string and the value's position inside it."""
    a, b = max(0, start - k), min(len(text), end + k)
    return text[a:b], start - a, end - a


def _candidates(items: list[Item]) -> list[tuple[str, list[tuple[int, int, int]]]]:
    """Single lines and pairs of consecutive lines. Each candidate keeps, per line, (item index,
    offset of that line's text inside the candidate string, length)."""
    out = []
    for i, it in enumerate(items):
        out.append((it.text, [(i, 0, len(it.text))]))
        if i + 1 < len(items):
            nxt = items[i + 1]
            out.append((it.text + " " + nxt.text, [(i, 0, len(it.text)), (i + 1, len(it.text) + 1, len(nxt.text))]))
    return out


def _interp(items: list[Item], parts: list[tuple[int, int, int]], ds: int, de: int) -> tuple:
    """Box of candidate characters [ds, de) from the line boxes, by character position."""
    boxes = []
    for idx, off, n in parts:
        lo, hi = max(ds, off), min(de, off + n)
        if hi <= lo or n == 0:
            continue
        it = items[idx]
        x0 = it.x + it.w * (lo - off) / n
        x1 = it.x + it.w * (hi - off) / n
        boxes.append((x0, it.y, x1, it.y + it.h))
    if not boxes:
        return None
    return (min(b[0] for b in boxes), min(b[1] for b in boxes), max(b[2] for b in boxes), max(b[3] for b in boxes))


def locate(text: str, start: int, end: int, items: list[Item], threshold: float = DEFAULT_THRESHOLD) -> dict:
    """Where on the page is text[start:end]? Returns status, score, box (OCR page coordinates)."""
    ctx, vs, ve = context_of(text, start, end)
    value = text[start:end]
    scored = []
    for cand, parts in _candidates(items):
        al = fuzz.partial_ratio_alignment(ctx, cand)
        if al is None:
            continue
        # partial_ratio aligns the shorter string inside the longer one, so a short OCR line that
        # matches only part of the context would score 100; weight by how much context is covered
        coverage = min(1.0, (al.src_end - al.src_start) / max(1, len(ctx)))
        scored.append((al.score * coverage, cand, parts, al))
    if not scored:
        return {"status": "text_verified_box_missing", "score": 0.0, "box": None, "granularity": None}
    scored.sort(key=lambda s: -s[0])
    best = scored[0]
    if best[0] < threshold:
        return {"status": "text_verified_box_missing", "score": round(best[0], 1), "box": None, "granularity": None}
    best_items = {p[0] for p in best[2]}
    for sc, _, parts, _ in scored[1:]:
        if sc < best[0] - AMBIG_MARGIN:
            break
        if not best_items & {p[0] for p in parts}:  # a different place, not an overlapping pair
            return {"status": "box_ambiguous", "score": round(best[0], 1), "box": None, "granularity": None}
    score, cand, parts, al = best
    # the value inside the matched context: align the value alone within the matched window
    win_lo = max(0, al.dest_start - CONTEXT)
    win_hi = min(len(cand), al.dest_end + CONTEXT)
    v_al = fuzz.partial_ratio_alignment(value, cand[win_lo:win_hi]) if value.strip() else None
    if v_al is not None and v_al.score >= threshold:
        ds, de = win_lo + v_al.dest_start, win_lo + v_al.dest_end
    else:  # fall back to the context alignment, scaled to the value's place in the context
        span = max(1, al.src_end - al.src_start)
        frac0, frac1 = (vs - al.src_start) / span, (ve - al.src_start) / span
        width = al.dest_end - al.dest_start
        ds = int(al.dest_start + max(0.0, frac0) * width)
        de = int(al.dest_start + min(1.0, frac1) * width)
    box = _interp(items, parts, ds, de)
    if box is None:
        return {"status": "text_verified_box_missing", "score": round(score, 1), "box": None, "granularity": None}
    return {"status": "boxed", "score": round(score, 1), "box": box, "granularity": "line_interp",
            "lines": [p[0] for p in parts]}


# ---------------------------------------------------------------- running OCRia-nano-1 (cached)

def nano_page(page_id: int) -> dict:
    from common import DATA
    cache = DATA / "cache" / "nano" / f"{page_id}.json"
    if cache.exists():
        return json.loads(cache.read_text(encoding="utf-8"))
    from PIL import Image
    img = DATA / "cache" / "images" / f"{page_id}.webp"
    cache.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as td:
        png = Path(td) / f"{page_id}.png"
        Image.open(img).convert("RGB").save(png)
        out = Path(td) / "out.json"
        subprocess.run([os.environ.get("LIT", "lit"), "parse", str(png), "--format", "json", "-o", str(out), "-q"],
                       check=True)
        d = json.loads(out.read_text(encoding="utf-8"))
    page = d["pages"][0]
    with Image.open(img) as im:
        page["image_width"], page["image_height"] = im.size
    cache.write_text(json.dumps(page, ensure_ascii=False), encoding="utf-8")
    return page


# ---------------------------------------------------------------- dev-only threshold sweep

def tune(run: str, version: str, split: str = "dev") -> None:
    import pandas as pd
    from box_accuracy import best_page, hocr_pages, iou, span_box
    from common import DATA, ROOT
    from score import load_gold, norm_value, page_text
    from difflib import SequenceMatcher
    import re
    if split != "dev":
        sys.exit("The threshold is tuned on dev pages only.")
    m = pd.read_csv(ROOT / "results" / run / "dev_mentions.csv", keep_default_na=False)
    m = m[(m.version == version) & (m.condition == "G1") & (m.status == "exact")]
    gold = load_gold(ROOT / "gold" / "gold_mentions_gloria.csv")
    gt = pd.read_parquet(DATA / "cache" / "gt_english.parquet", columns=["PageID", "BarCode"])
    bc = dict(zip(gt.PageID.astype(int), gt.BarCode))
    rows = []
    for pid in sorted(m.page_id.unique()):
        pid = int(pid)
        page = nano_page(pid)
        items = items_from_nano(page)
        text = page_text(version, pid)
        hp = best_page(hocr_pages(bc[pid]), page_text("legacy", pid))
        sx = hp["w"] / page["width"]          # nano page space -> hOCR pixels
        sy = hp["h"] / page["height"]
        gold_vals = {norm_value(t) for t in gold[gold.page_id == pid].text}
        for r in m[m.page_id == pid].itertuples():
            if norm_value(r.value) not in gold_vals:
                continue
            key = max(re.findall(r"\w+", r.value), key=len, default="").lower()
            cands = [w for w in hp["words"] if SequenceMatcher(None, key, re.sub(r"\W", "", w[4].lower())).ratio() >= 0.7]
            res = locate(text, int(r.start), int(r.end), items, threshold=0.0)
            row = {"page_id": pid, "value": r.value, "score": res["score"], "status0": res["status"],
                   "iou": None, "has_ref": bool(cands and len(key) >= 3)}
            if res["box"] is not None and row["has_ref"]:
                b = res["box"]
                bb = (b[0] * sx, b[1] * sy, b[2] * sx, b[3] * sy)
                cx, cy = (bb[0] + bb[2]) / 2, (bb[1] + bb[3]) / 2
                t = min(cands, key=lambda w: ((w[0] + w[2]) / 2 - cx) ** 2 + ((w[1] + w[3]) / 2 - cy) ** 2)
                row["iou"] = round(iou(bb, span_box(hp["words"], t, r.value)), 3)
            rows.append(row)
    d = pd.DataFrame(rows)
    out = ROOT / "results" / "level3_anchor"
    out.mkdir(parents=True, exist_ok=True)
    d.to_csv(out / f"dev_tune_{version}.csv", index=False)
    j = d[d.has_ref]
    sweep = []
    for th in range(40, 96, 5):
        boxed = j[(j.status0 == "boxed") & (j.score >= th)]
        sweep.append({"threshold": th, "judged": len(j), "boxed": len(boxed),
                      "coverage": round(len(boxed) / len(j), 3) if len(j) else None,
                      "strict_hit_among_boxed": round((boxed.iou >= 0.5).mean(), 3) if len(boxed) else None,
                      "wrong_box_rate": round((boxed.iou < 0.1).mean(), 3) if len(boxed) else None})
    s = pd.DataFrame(sweep)
    s.to_csv(out / f"dev_threshold_sweep_{version}.csv", index=False)
    print(f"{len(j)} dev values with an hOCR reference ({version}); ambiguous at any threshold: "
          f"{(j.status0 == 'box_ambiguous').sum()}")
    print(s.to_markdown(index=False))


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent))
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "nano":
        for p in sys.argv[2:]:
            pg = nano_page(int(p))
            print(p, len(pg["text_items"]), "lines")
    elif cmd == "tune":
        tune(sys.argv[2], sys.argv[3], *(sys.argv[5:6] if "--split" in sys.argv else []))
    else:
        print(__doc__)
