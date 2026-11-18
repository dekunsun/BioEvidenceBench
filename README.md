# BioEvidenceBench

An exploratory evaluation of LLM information extraction on 19th- and early 20th-century
biodiversity literature from the [Biodiversity Heritage Library](https://www.biodiversitylibrary.org/).
It asks where the reliability of extracted scientific data is lost: in OCR, in extraction, in
evidence verification, in entity resolution, or in human review. It also asks where the next
unit of effort should go.

**Status: ready for labelling.** The data pipeline, CER analysis, sample (22 pages, split into
6 dev and 16 locked test pages) and annotation guide v0.1 are in. No model has been run, and there
is no gold set yet. V1 scope is in [`CLAUDE.md` section 4a](CLAUDE.md).

The project brief for contributors and Claude Code is in [`CLAUDE.md`](CLAUDE.md).

## What is here so far

| Step | Script | Output |
|---|---|---|
| Load the two English books from `finebooks/bhl-impact-gt`, check license, schema and the PageID join to `bhl-metadata` | `src/load_gt.py` | [`data/reports/01_dataset_check.md`](data/reports/01_dataset_check.md), `data/gt_pages.csv` |
| Fetch BHL legacy OCR for every text page | `src/fetch_legacy_ocr.py` | `data/text/legacy/` (not committed) + SHA-256 manifest |
| Modern OCR (dots.mocr) per page, from FineBooks' public output bucket | `src/fetch_modern_ocr.py` | `data/text/modern_dots-mocr/` (not committed) + manifest |
| Per-page CER of each text version vs the expert transcription | `src/compute_cer.py [--version modern_dots-mocr]` | [`02_cer_legacy.md`](data/reports/02_cer_legacy.md), [`02_cer_modern_dots-mocr.md`](data/reports/02_cer_modern_dots-mocr.md), `data/cer_*.csv` |
| TaxonFinder counts per page + proposed stratified sample | `src/propose_sample.py` | [`data/reports/03_sample_proposal.md`](data/reports/03_sample_proposal.md), `data/sample_proposal.csv` |
| Dev / locked-test split by page blocks | `src/split_sample.py` | `data/sample_split.csv` |
| Labelling guide and empty gold templates | — | [`ANNOTATION_GUIDE.md`](ANNOTATION_GUIDE.md), `gold/*_TEMPLATE.csv` |
| Read-only gold checker (offsets, field names) | `src/check_gold.py` | `gold/<file>.checked.csv` |

## Reproduce

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python src/load_gt.py           # ~30 s
python src/fetch_legacy_ocr.py  # ~30 s, 715 small files from BHL's S3 bucket
python src/fetch_modern_ocr.py  # ~10 s, one 5 MB Parquet file from FineBooks
python src/compute_cer.py       # ~10 s
python src/compute_cer.py --version modern_dots-mocr
python src/propose_sample.py    # ~1-3 min the first time (queries page_name on Hugging Face)
python src/split_sample.py
pytest -q
```

Page texts land in `data/text/` and big intermediate files in `data/cache/`. Both are git-ignored,
so the repo never redistributes page text; the scripts fetch it again.

## Data and licenses

| Source | What we use | License |
|---|---|---|
| [`finebooks/bhl-impact-gt`](https://huggingface.co/datasets/finebooks/bhl-impact-gt) | Expert transcriptions of Butler 1907 (341 pages) and Reeve 1849 (648 pages) | CC-BY 3.0. Attribute IMPACT / Biodiversity Heritage Library |
| [`finebooks/bhl-metadata`](https://huggingface.co/datasets/finebooks/bhl-metadata) | `item`, `title`, `page`, `page_name` tables | CC0 1.0 |
| [BHL open data on S3](https://github.com/gbhl/bhl-open-data) | Per-page legacy OCR | Both books are `NOT_IN_COPYRIGHT` in the BHL `item` table |
| [FineBooks OCR outputs](https://huggingface.co/buckets/finebooks/bhl-ocr-outputs) | Modern OCR: `rednote-hilab/dots.mocr` per-page output | MIT (per `manifest.json`) |

**Why the S3 bucket, not `biodiversitylibrary.org/itemtext/`?** It is BHL's own OCR, already split
per page, so we never slice a whole-book file. The BHL website also returns a Cloudflare bot
check to scripts running on cloud machines (seen 2026-11-18).

## First findings from the data (descriptive, two books only)

- All 989 English GT pages join to the BHL `page` table by `PageID` (0 unmatched).
- Legacy OCR CER is much higher in Reeve than in Butler. Case-insensitive, on pages with 200 or
  more characters, the median is **6.6% vs 2.0%**. Reeve has Latin diagnoses in italics and dense
  abbreviations, and its OCR errors hit exactly the fields we care about. On one page it reads
  `Species 2S3` for 282, `184.6, p. 113` for `1846, p. 112`, and `Hob.` for `Hab.`.
- **Book and OCR quality are confounded.** Reeve has only 2 low-CER pages (< 2%) and Butler only
  8 high-CER pages (≥ 10%). A pooled F1-vs-CER curve would largely compare the two books.
- **Modern OCR closes most of the gap on the same pages.** dots.mocr's median CER (pages with
  200+ characters, case-insensitive) is **1.3% for Reeve and 1.1% for Butler**, down from 6.6% and
  2.0%. It is lower than legacy OCR on 91% of pages. So each page now comes in a high-CER and a
  low-CER version, which separates OCR quality from the book.
- Modern OCR has its own failure mode: 35 pages have CER > 10% while missing < 5% of the words.
  They are re-ordered, not misread.
- Small capitals add about 3 CER points by themselves: the experts typed them as upper case and
  the OCR did not. CER bands therefore use the case-insensitive value.
- Index pages in Reeve list bare epithets under a genus heading (`ampullaceum, Philippi`).
  TaxonFinder finds few or no names on them.
- Missing `<ReadingOrder>` affects about 20% of Butler's text pages and none of Reeve's.

## Not yet verified

- FineBooks' reported claim that modern OCR output lacks word-level coordinates and so cannot
  replace ALTO workflows. We have not found that statement in the primary source. What we *can*
  see: the outputs FineBooks published for dots.mocr are Markdown with no coordinates, and the
  FineBooks harness calls its region diagnostics "global token-evidence proxies, not spatial
  attribution".

## Layout

```
CLAUDE.md      project brief (read automatically by Claude Code)
data/          page lists, CER table, sample proposal, reports (texts are fetched, not committed)
gold/          Gloria's gold labels (empty until labelling starts)
src/           scripts
results/       one folder per model run (none yet)
memo/          one-page Research-to-Product memo (later)
tests/         unit tests for the helpers
```
