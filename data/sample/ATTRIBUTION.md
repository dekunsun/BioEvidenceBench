# Attribution and licence

The files in `expert/` and `expert_view/` are expert transcriptions of 22 pages from:

- Butler, A. G. (1907). *Birds of Great Britain and Ireland*, vol. 2. BHL item 35947.
- Reeve, L. A. (1849). *Conchologia iconica*, vol. 5. BHL item 35904.

They come from the **IMPACT-BHL ground truth**, produced by the IMPACT Centre of Competence and
BHL-Europe (2011–2012), <https://github.com/impactcentre/groundtruth-bhl>, as redistributed by
FineBooks in [`finebooks/bhl-impact-gt`](https://huggingface.co/datasets/finebooks/bhl-impact-gt).

Licence: **CC-BY 3.0**, <https://creativecommons.org/licenses/by/3.0/>.
Attribution: IMPACT / Biodiversity Heritage Library.

The text is unchanged from the dataset's `text` field (checked by SHA-256 in `manifest.csv`).
The `expert_view/` files add only a line-offset prefix for labelling. Page scans:
<https://www.biodiversitylibrary.org/page/{PageID}>. Both books are public domain
(`NOT_IN_COPYRIGHT` in the BHL item table).

## OCR versions of the same pages

- `legacy/`: BHL's OCR text for these pages, fetched 2026-11-18 from the BHL open-data bucket
  (`https://bhl-open-data.s3.amazonaws.com/ocr/...`). Both books are `NOT_IN_COPYRIGHT` in the BHL
  item table. Source: Biodiversity Heritage Library.
- `modern_dots-mocr/`: output of `rednote-hilab/dots.mocr` on the same page images, as published by
  FineBooks in `hf://buckets/finebooks/bhl-ocr-outputs` (row `dots-mocr`, licence MIT per its
  `manifest.json`).

`manifest.csv` holds the SHA-256 of every file; they equal the input hashes recorded in the
extraction runs under `results/`.

## Plate images (added 2026-11-24)

- `docs/assets/overview/reeve_plate17.jpg` and `reeve_plate17_fig102.png`: Reeve, *Conchologia iconica*
  vol. 5 (1849), *Bulimus* plate XVII, figure 102 = *Bulimus chilensis* (the species of README figure 1).
  Internet Archive item `conchologiaiconi05reev`, image n77 (the plate before text pages n78–n79).
  Published 1849; public domain by age.
