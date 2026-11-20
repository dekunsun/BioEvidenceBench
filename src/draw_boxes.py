"""Draw the V3 (image-only) mentions with their boxes on the page scans: a Level 3 grounding
demo without any OCR (exploratory, DEVIATIONS.md).

    python src/draw_boxes.py <V3 run id> [page_id ...]

Writes results/vision_boxes/<page_id>.png (scan + one box per mention, coloured by field, with
the value as the model transcribed it) and results/vision_boxes/boxes.csv. Also reports, per
page, how many boxed values match a gold mention's text (value level, like the bag scoring):
a box is only a claim about where the value is; looking at the picture is the check.
"""
from __future__ import annotations

import json
import sys
from collections import Counter

import pandas as pd
from PIL import Image, ImageDraw, ImageFont

from common import ROOT
from score import load_gold, norm_value

OUT = ROOT / "results" / "vision_boxes"
IMAGES = ROOT / "data" / "cache" / "images"
# categorical palette (dataviz skill reference palette, slots 1-6), one colour per field
COLOUR = {"taxon": "#2a78d6", "person": "#eb6834", "locality": "#1baf7a", "date": "#eda100",
          "institution": "#e87ba4", "vernacular": "#008300"}


def main() -> None:
    run = sys.argv[1]
    m = pd.read_csv(ROOT / "results" / run / "test_mentions.csv", keep_default_na=False)
    pages = [int(p) for p in sys.argv[2:]] or sorted(m.page_id.unique())
    gold = load_gold(ROOT / "gold" / "gold_mentions_gloria_test.csv")
    OUT.mkdir(parents=True, exist_ok=True)
    rows = []
    try:
        font = ImageFont.truetype("DejaVuSans.ttf", 22)
    except OSError:
        font = ImageFont.load_default()
    for pid in pages:
        im = Image.open(next(IMAGES.glob(f"{pid}.*"))).convert("RGB")
        w, h = im.size
        draw = ImageDraw.Draw(im)
        gold_vals = Counter(norm_value(t) for t in gold[gold.page_id == pid].text)
        for r in m[m.page_id == pid].itertuples():
            box = json.loads(r.box) if r.box else None
            ok = gold_vals[norm_value(r.value)] > 0
            if ok:
                gold_vals[norm_value(r.value)] -= 1
            rows.append({"page_id": pid, "field": r.field, "value": r.value, "box": r.box, "value_in_gold": ok})
            if not box or len(box) != 4:
                continue
            x0, y0, x1, y1 = (box[0] * w / 1000, box[1] * h / 1000, box[2] * w / 1000, box[3] * h / 1000)
            c = COLOUR.get(r.field, "#52514e")
            draw.rectangle([x0, y0, x1, y1], outline=c, width=4)
            draw.text((x0, max(0, y0 - 24)), f"{r.field[:3]}: {r.value}"[:40], fill=c, font=font)
        im.thumbnail((1400, 1400))
        im.save(OUT / f"{pid}.png")
    d = pd.DataFrame(rows)
    d.to_csv(OUT / "boxes.csv", index=False)
    print(d.groupby("page_id").agg(boxes=("box", lambda s: (s != "").sum()), values=("value", "size"),
                                   value_in_gold=("value_in_gold", "mean")).round(3))


if __name__ == "__main__":
    main()
