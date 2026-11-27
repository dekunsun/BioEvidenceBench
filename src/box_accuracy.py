"""How well do V3's boxes point at the right place on the scan? (exploratory, DEVIATIONS.md)

    python src/box_accuracy.py <V3 run id>

The expert transcription only has paragraph-level polygons, so the reference is the word boxes
in Internet Archive's hOCR (from BHL's legacy OCR; same scan, same pixel size; fetched once into
data/cache/hocr/<barcode>.html, not committed). The hOCR page for each test page is found by word
overlap with our legacy OCR text, not by index (IA's page index is not BHL's SequenceOrder - 1).

For each V3 mention whose value equals a gold value on that page (so we know what it should
point at), the anchor is the hOCR word that best matches the value's longest word (fuzzy, since
the legacy OCR may be damaged, ratio >= 0.7). If that word is printed more than once on the page,
the occurrence nearest to the model's box is used (lenient). Outcomes (lenient, as first reported):
  hit        the anchor word's centre lies inside the model's box
  near       no hit, but the box centre is within 1.5 line heights of the anchor word
  off        further away
  no_target  no hOCR word matches well enough (cannot judge)

The lenient `hit` does not penalise a box that is too big: a box over a whole line or paragraph
contains the word's centre too (found 2026-11-27, before scoring line-level OCR boxes). So each
judged mention also gets a span-level check: the target span is the anchor word plus the
neighbouring hOCR words on the same line that match the value's other words, in order; `iou` is the
intersection over union of the model's box and that span; `area_ratio` is box area / span area;
`strict_hit` = iou >= 0.5. Report strict_hit; keep `hit` only to compare with earlier numbers.
Writes results/vision_boxes/box_accuracy.csv and BOX_ACCURACY.md.
"""
from __future__ import annotations

import html
import json
import re
import sys
from collections import Counter
from difflib import SequenceMatcher

import pandas as pd

from common import DATA, ROOT
from score import load_gold, norm_value, page_text

HOCR = DATA / "cache" / "hocr"
OUT = ROOT / "results" / "vision_boxes"
PAGE_RE = re.compile(r'<div class="ocr_page" id="page_(\d+)" title="bbox 0 0 (\d+) (\d+);')
WORD_RE = re.compile(r'class="ocrx_word"[^>]*title="bbox (\d+) (\d+) (\d+) (\d+);[^"]*"[^>]*>([^<]*)<')


def hocr_pages(barcode: str) -> list[dict]:
    h = (HOCR / f"{barcode}.html").read_text(encoding="utf-8")
    starts = [(m.start(), int(m.group(2)), int(m.group(3))) for m in PAGE_RE.finditer(h)]
    pages = []
    for i, (s, w, hh) in enumerate(starts):
        seg = h[s: starts[i + 1][0] if i + 1 < len(starts) else len(h)]
        words = [(int(a), int(b), int(c), int(d), html.unescape(t).strip()) for a, b, c, d, t in WORD_RE.findall(seg)]
        pages.append({"w": w, "h": hh, "words": [x for x in words if x[4]]})
    return pages


def toks(s: str) -> Counter:
    return Counter(re.findall(r"[a-z]{4,}", s.lower()))


def best_page(pages: list[dict], legacy: str) -> dict:
    lt = toks(legacy)
    return max(pages, key=lambda p: sum((toks(" ".join(w[4] for w in p["words"])) & lt).values()))


def span_box(words: list, anchor: tuple, value: str) -> tuple:
    """Union of the anchor word and the words beside it on the same line that match the value's other
    words in order (fuzzy, ratio >= 0.7): the whole printed value, not only its longest word."""
    parts = [re.sub(r"\W", "", p.lower()) for p in re.findall(r"\w+", value)]
    if len(parts) <= 1:
        return anchor[:4]
    line = sorted([w for w in words if abs((w[1] + w[3]) / 2 - (anchor[1] + anchor[3]) / 2) < (anchor[3] - anchor[1]) * 0.6],
                  key=lambda w: w[0])
    i = line.index(anchor) if anchor in line else None
    if i is None:
        return anchor[:4]
    clean = [re.sub(r"\W", "", w[4].lower()) for w in line]
    k = max(range(len(parts)), key=lambda j: SequenceMatcher(None, parts[j], clean[i]).ratio())
    lo, hi = i, i
    for j in range(k - 1, -1, -1):  # value words before the anchor
        if lo - 1 >= 0 and SequenceMatcher(None, parts[j], clean[lo - 1]).ratio() >= 0.7:
            lo -= 1
        else:
            break
    for j in range(k + 1, len(parts)):  # value words after the anchor
        if hi + 1 < len(line) and SequenceMatcher(None, parts[j], clean[hi + 1]).ratio() >= 0.7:
            hi += 1
        else:
            break
    span = line[lo:hi + 1]
    return (min(w[0] for w in span), min(w[1] for w in span), max(w[2] for w in span), max(w[3] for w in span))


def iou(a: tuple, b: tuple) -> float:
    ix = max(0.0, min(a[2], b[2]) - max(a[0], b[0]))
    iy = max(0.0, min(a[3], b[3]) - max(a[1], b[1]))
    inter = ix * iy
    union = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - inter
    return inter / union if union > 0 else 0.0


def main() -> None:
    run = sys.argv[1]
    m = pd.read_csv(ROOT / "results" / run / "test_mentions.csv", keep_default_na=False)
    gold = load_gold(ROOT / "gold" / "gold_mentions_gloria_test.csv")
    gt = pd.read_parquet(DATA / "cache" / "gt_english.parquet", columns=["PageID", "BarCode"])
    bc = dict(zip(gt.PageID.astype(int), gt.BarCode))
    cache: dict[str, list] = {}
    rows = []
    for pid in sorted(m.page_id.unique()):
        b = bc[int(pid)]
        cache.setdefault(b, hocr_pages(b))
        pg = best_page(cache[b], page_text("legacy", int(pid)))
        W, H = pg["w"], pg["h"]
        line_h = pd.Series([w[3] - w[1] for w in pg["words"]]).median()
        gold_vals = Counter(norm_value(t) for t in gold[gold.page_id == pid].text)
        for r in m[m.page_id == pid].itertuples():
            v = norm_value(r.value)
            if gold_vals[v] <= 0 or not r.box:
                continue
            gold_vals[v] -= 1
            box = json.loads(r.box)
            x0, y0, x1, y1 = box[0] * W / 1000, box[1] * H / 1000, box[2] * W / 1000, box[3] * H / 1000
            key = max(re.findall(r"\w+", r.value), key=len, default="").lower()
            cands = [w for w in pg["words"]
                     if SequenceMatcher(None, key, re.sub(r"\W", "", w[4].lower())).ratio() >= 0.7]
            out = "no_target"
            dist = ov = ratio = None
            strict = None
            if cands and len(key) >= 3:
                bx, by = (x0 + x1) / 2, (y0 + y1) / 2
                t = min(cands, key=lambda w: ((w[0] + w[2]) / 2 - bx) ** 2 + ((w[1] + w[3]) / 2 - by) ** 2)
                tx, ty = (t[0] + t[2]) / 2, (t[1] + t[3]) / 2
                dist = ((tx - bx) ** 2 + (ty - by) ** 2) ** 0.5 / line_h
                out = "hit" if x0 <= tx <= x1 and y0 <= ty <= y1 else "near" if dist <= 1.5 else "off"
                sp = span_box(pg["words"], t, r.value)
                ov = iou((x0, y0, x1, y1), sp)
                sp_area = (sp[2] - sp[0]) * (sp[3] - sp[1])
                ratio = ((x1 - x0) * (y1 - y0)) / sp_area if sp_area > 0 else None
                strict = ov >= 0.5
            rows.append({"page_id": pid, "book": "Butler" if "butl" in b else "Reeve", "field": r.field,
                         "value": r.value, "outcome": out,
                         "distance_line_heights": None if dist is None else round(dist, 2),
                         "iou": None if ov is None else round(ov, 3),
                         "area_ratio": None if ratio is None else round(ratio, 2),
                         "strict_hit": strict})
    d = pd.DataFrame(rows)
    d.to_csv(OUT / "box_accuracy.csv", index=False)
    t = d.groupby("book").outcome.value_counts().unstack(fill_value=0)
    t["judged"] = t.drop(columns="no_target", errors="ignore").sum(axis=1)
    t["hit_rate"] = (t.get("hit", 0) / t.judged).round(3)
    t["hit_or_near"] = ((t.get("hit", 0) + t.get("near", 0)) / t.judged).round(3)
    j = d[d.outcome != "no_target"]
    t["strict_hit_rate"] = j.groupby("book").strict_hit.mean().round(3)
    t["median_iou"] = j.groupby("book").iou.median().round(2)
    t["median_area_ratio"] = j.groupby("book").area_ratio.median().round(2)
    t["lenient_hits_box_over_4x"] = j[(j.outcome == "hit") & (j.area_ratio > 4)].groupby("book").size()
    t["lenient_hits_box_over_4x"] = t["lenient_hits_box_over_4x"].fillna(0).astype(int)
    lines = ["# V3 box accuracy (exploratory)", "",
             f"Run `{run}`. Only mentions whose value equals a gold value on the page are judged. "
             "Reference: IA hOCR word boxes (legacy OCR), nearest matching occurrence (lenient). "
             "`hit` = target word centre inside the model's box; `near` = within 1.5 line heights "
             "(lenient: no penalty for a box that is too big). `strict_hit_rate` = share with IoU >= 0.5 "
             "against the box of the whole printed value (span-level, added 2026-11-27); "
             "`median_area_ratio` = model box area / value box area.", "",
             t.to_markdown(), "", "By field:", "",
             d.groupby("field").outcome.value_counts().unstack(fill_value=0).to_markdown(), ""]
    (OUT / "BOX_ACCURACY.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
