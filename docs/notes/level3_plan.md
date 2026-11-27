# Level 3 (image) grounding: plan (draft, to be frozen before any route runs on test pages)

Status 2026-11-27: draft written with the author. Exploratory (`DEVIATIONS.md`): the 16 test pages
were unsealed for the text study; the **boxes** are new and have not been looked at by any route.

## Question

When an extracted value is right, can we also say where it is printed on the scan, reliably and
cheaply? This turns a claim the study could not test (the preprint's "image coordinates should come
from OCR word boxes"; FineBooks' reported point that modern OCR lacks word positions, unverified)
into a measurement.

## Four routes

| Route | Text (decides value F1) | Coordinates | Real-world case |
| --- | --- | --- | --- |
| 1 | Opus 5.5 reads the image (V3, existing run) | Opus draws 0–1000 boxes | one model does everything |
| 2 | OCRia-1 (4B) | OCRia-1 `ocria_grounding` (Heron layout + attention) | a document VLM's own grounding |
| 3 | OCRia-1 (4B) | OCRia-nano-1 line boxes + local quote anchors | new photographs with no coordinates (本草綱目, British Library items) |
| 4 | dots.mocr (frozen Opus G1 outputs) | BHL legacy hOCR word boxes + local quote anchors | the 64 million BHL pages that already have hOCR |

## Gold boxes (plan A, the author)

- All 350 primary-field gold mentions on the 16 test pages (Butler 137, Reeve 213).
- Drawn by hand on the **blank** scan with `src/make_box_labelling_tool.py`. No OCR, model or hOCR box
  is shown or pre-filled (no anchoring). The only text shown is the author's own gold.
- A value broken across lines gets one box per line segment (1..k boxes per mention).
- Flags: `not_found`, `unsure`. Seconds per mention are recorded.
- The delivered CSV is archived unchanged in `gold/received/`, then copied to
  `gold/gold_boxes_gloria_test.csv`. The assistant does not review the boxes.
- hOCR is **not** a reference any more: route 4 uses it, and it misses the worst names (15 taxon
  mentions were `no_target` in the V3 check because legacy OCR broke the italic Latin names).

## Metrics (fixed before running)

Overlap between a predicted box set P and a gold box set G is the **union IoU**: area(∪P ∩ ∪G) /
area(∪P ∪ ∪G), computed on the pixel grid. A box is right when union IoU ≥ 0.5.

1. **Grounded value F1**: denominator all 350 gold mentions; a prediction is a true positive only if
   field, value and box are all right. What a curator receives as usable value + location.
2. **Controlled box hit rate**: one fixed extraction output (the frozen Opus G1 test run on
   `modern_dots-mocr`, `results/20261119-2052_claude-opus-5-5_test_batch`), coordinate source swapped
   (route 2 grounding, route 3 nano anchors, route 4 hOCR anchors). Compares the coordinate layers
   alone. (Route 1 cannot be held to the same text and is reported under metric 1 only.)
3. For each route: coverage (share of values given a box), strict hit among boxed (IoU ≥ 0.5),
   **wrong-box rate** (boxed with IoU < 0.1: a confident wrong location is worse than none),
   honest-degradation rate (`text_verified_box_missing`, `box_ambiguous`), box granularity
   (word / line_interp / block), seconds and dollars per page.

Reported per book (Butler, Reeve) with a page-level bootstrap over the 16 pages, and separately for:
the mentions hOCR could not match (former `no_target`), damaged names (gold name not intact in the
legacy OCR), and values broken across lines.

Sensitivity: (a) gold boxes tightened to the ink inside them by a fixed grey-level rule (no OCR
model); (b) without the values broken across lines.

## Matcher settings (chosen on dev pages only, then frozen)

`src/anchor_boxes.py`: context 15 characters each side; scores weighted by how much of the context
is covered; ambiguity margin 2 points; **threshold 65**. Rule decided before looking at test pages:
the lowest threshold whose wrong-box rate is ≤ 3% on dev for both legacy and modern text
(dev sweep vs hOCR, `results/level3_anchor/dev_threshold_sweep_*.csv`: at 65, coverage 0.94 / 0.84,
wrong-box rate 0.030 / 0.008 for modern / legacy text). The dev reference is hOCR, so these dev
numbers only set the threshold; they are not results.

Finding while building: OCRia-nano-1 through LiteParse reports **one box per text line**, not per
word, with a line-level confidence. Inside a line the value's box is interpolated by character
position (`line_interp`), which limits how tight route 3 boxes can be.

## Cost and approvals

Route 1 exists ($0). Route 3 nano runs on CPU ($0). Route 4 uses cached hOCR ($0). OCRia-1 text on 22
pages and `ocria_grounding` need a GPU (RunPod, about $1 together; GPU spend so far $5.93 of $20), plus
an Opus G1 run on OCRia-1 text (about $0.3). Paid runs only with the author's go-ahead.
OCRia-1 / nano licences allow research use and publishing results.

## Order

1. The author draws the gold boxes (about 40–60 minutes) → archived.
2. This plan and the scorer are frozen (hashes recorded).
3. Routes run once; scored once.
