# BioEvidenceBench

An exploratory evaluation of LLM information extraction on 19th- and early 20th-century
biodiversity literature from the [Biodiversity Heritage Library](https://www.biodiversitylibrary.org/).
It asks where the reliability of extracted scientific data is lost: in OCR, in extraction, in
evidence verification, in entity resolution, or in human review. It also asks where the next
unit of effort should go.

**Status (2026-11-20): frozen, run and scored on the test pages.** All 22 sample pages are
labelled (6 dev, 16 locked test), a second labeller double-labelled 5 test pages, the plan and
gold were frozen (`FREEZE.json`), and only then were the test pages run and unsealed. Error
analysis and the memo are next. Scores on the
dev pages are pipeline checks, not results: the guide and the prompt were written from them.
Entity types are inspired by NHM's BHL prototype, but our scores are not comparable to NHM's
reported results. V1 scope is in [`CLAUDE.md` section 4a](CLAUDE.md); the analysis plan is
[`PREREGISTRATION.md`](PREREGISTRATION.md).

## Question

> When does improved OCR stop being the main bottleneck, and when do evidence verification and
> entity resolution become the limiting factors for trustworthy scientific data extraction?

"When" is something to measure; "there is no single threshold" is a valid answer. The answer is
meant to guide resource allocation: better OCR, better LLM extraction, automated verification,
or human review.

| | Sub-question | Comparison |
|---|---|---|
| RQ1 | How much does OCR quality change extraction accuracy? | the same page as legacy BHL OCR, modern OCR (dots.mocr), expert transcription |
| RQ2 | How much better is an LLM than a rule baseline? | gnfinder + regex vs Claude Opus 5.5 |
| RQ3 | Does requiring evidence reduce unsupported output, at what recall cost? | G0 (values only) vs G1 (line + verbatim quote per value) |
| RQ4 | Can model agreement plus checks prioritise human review? | shadow evaluation: Opus and Gemini 4 Carbon agree and checks pass → "proposed auto-accept"; nothing skips review |
| E4-lite | Where are names lost: before linking or at linking? | Butler taxa, plain GBIF name lookup vs gold links |

## Method

**Books and pages.** The two English works in FineBooks' expert-transcribed set: Butler, *Birds
of Great Britain and Ireland* vol. 2 (1907), and Reeve, *Conchologia iconica* vol. 5 (1849). 22
pages, sampled by stratum (entity-rich, low-density, no target names, poor OCR) across the range
of legacy-OCR character error rate (CER): 6 dev pages (3 per book) and 16 locked test pages
(Butler 7, Reeve 9). Book and CER are confounded (Reeve's legacy OCR is much worse), so every
result is reported per book and a pooled F1-vs-CER curve is descriptive only.

**Text versions.** `expert` (IMPACT/BHL transcription, the reference), `legacy` (BHL's own OCR),
`modern_dots-mocr` (FineBooks' public dots.mocr output, Markdown) and `modern_dots-mocr_plain`
(the same text with Markdown marks deleted, a formatting ablation). Gold offsets are in the expert
text; predictions on the other versions are mapped to it by character alignment.

**Gold labels.** A mention is a character span plus one field: `taxon`, `person`, `locality`,
`institution`, `date` (event dates only), and `vernacular` (scored separately, never in the primary
number). The [annotation guide](ANNOTATION_GUIDE.md) is versioned (v0.10, English and Chinese).
Gloria labelled every page herself before seeing any model output on it; each delivery is archived
unchanged in `gold/received/` before any comparison; every later change is decided by her and
logged in `gold/gold_changes_gloria.csv`. Rules decided on test pages went into the guide and
the gold but never into the prompt (`p4-guide-v0.6`), so scores are also reported with those rows
treated as optional. Known typos in the expert transcription are recorded in `scan_text` and
`data/transcription_errata.csv`. Gold size: dev 186 mentions, test 421 (Butler 189, Reeve 232).

**Agreement.** A second labeller labelled 5 test pages with a labeller copy of the guide (same
rules; examples taken from her own pages replaced by invented ones), without AI assistants or
access to the gold. Agreement = 2 × matched / (n₁ + n₂), per field, exact span and overlap.

**Extraction.** The model never rewrites source text: lines are numbered, the model returns a
value (G0) or a line plus a verbatim quote (G1), and code slices the value from the source. A quote
that does not match the source is logged as a silent correction. Two LLMs from different
providers (Claude Opus 5.5, batch; Gemini 4 Carbon, sync with the JSON schema enforced), one
prompt, every text version, G0 and G1. Test outputs are sealed when they arrive and opened only
after the freeze (`src/unseal.py` checks `src/freeze.py --verify`).

**Scoring and statistics.** One-to-one matching per field at three levels: lenient (overlap),
exact (same span) and value (overlap and same text after normalisation; the primary level,
because a well-placed misread name is wrong data). 1,000 page-bootstrap resamples per book,
paired for differences; verdicts against thresholds written in advance (PREREGISTRATION section
3). No multiple-comparison correction: this is an exploratory pilot and every comparison is
reported.

**Entity resolution.** Gloria resolved each of Butler's 29 distinct printed names to a current
name (Avibase first; `resolved` / `partial` / `ambiguous` / `unresolved`); `src/expand_links.py`
turns her names into GBIF backbone keys. The linker under test is a plain GBIF `species/match`
lookup with no hints. Subfamily names are not scored (the backbone has no such rank).

## Results (test pages, 2026-11-20)

Frozen before any test page was run (`FREEZE.json`); 16 locked test pages (Butler 7, Reeve 9);
Opus is the primary model, Gemini the second model for RQ4. Value F1 on `ALL_PRIMARY` with 95%
page-bootstrap intervals; verdicts against the rules in `PREREGISTRATION.md` section 3. Full
tables: `results/analysis_test_main/REPORT.md`, `results/linking_test/REPORT.md`.

| | Result |
|---|---|
| Agreement (5 pages, as delivered) | ALL_PRIMARY exact 0.90, overlap 0.95 (Butler 0.89 / 0.93, Reeve 0.90 / 0.96); lowest field: locality exact 0.75, mostly span edges. All 23 disagreements adjudicated "keep gold". `results/agreement_independent/` |
| RQ1 OCR | Opus G1 value F1, legacy → modern → expert: **Reeve 0.64 → 0.98 → 0.98**, Butler 0.60 → 0.95 → 0.98. Pre-registered (Reeve): legacy → modern +0.34 [0.25, 0.46], *supports* (≥ 0.10); modern → expert +0.005 [−0.015, 0.03], *supports* (< 0.05). Butler is descriptive: +0.36 and +0.03 [0.01, 0.06]. Almost all legacy-OCR loss is misread text inside a correctly found span (lenient F1 0.93–0.97). Butler's legacy-OCR taxon F1 is 0.20 although its page CER is low. Removing Markdown changes little (−0.015 to 0) |
| RQ2 baseline | On the expert text the LLM's recall is higher for taxon and person in both books and for Butler's localities (*supports*); Reeve's localities and institutions and Butler's dates are *inconclusive*. Taxon value F1: Butler 1.00 vs 0.64, Reeve 0.99 vs 0.54. The falsifier (rule ≥ LLM on taxa) did not occur. The gap is largest for person (+0.74 / +0.78 recall), not for institution |
| RQ3 evidence | Requiring evidence cost no recall (G1 − G0 between −0.015 and +0.007, all *supports*). But neither condition produced any unsupported output (0 in G0 and G1, both models), so the expected reduction could not be observed |
| RQ4 review prioritisation | Models agreed on 99–100% of predictions, leaving ≤ 2 unflagged per book and version: *too few to compare*. Errors inside the "proposed auto-accept" set: expert 3 (Butler) / 4 (Reeve), modern OCR 6 / 5, **legacy OCR 50 / 75**. Agreement is not correctness |
| E4-lite linking (Butler) | Pre-registered (Opus G1, expanded linker): of 34 gold-resolved names, 14 are lost at linking and 0 before it on the expert text (difference 0.41 [0.25, 0.60], *supports*); 13 vs 1 on modern OCR (0.35 [0.10, 0.55], *supports*). Link recall of a plain GBIF lookup is 0.59 even on the gold text: 8 matched only at genus, 3 wrong taxon, 3 no record. On legacy OCR, 0.12 |
| Sensitivity | Treating the 12 rows decided by guide rules added after the prompt as optional changes ALL_PRIMARY value F1 by at most 0.004 (`results/analysis_test_sensitivity_v0.6/`) |
| Error analysis | — (Gloria tags `discrepancies.csv`) |
| Cost | Test runs: Opus $1.50 (batch), Gemini $4.11 (sync). Total API spend about $15.4 |

**Reading for the main question (for these two books, with this linker):** once modern OCR is
used, extraction is within 0.03 of the expert transcription, and the largest remaining loss is at
entity resolution: a plain GBIF name lookup loses about four in ten names that extraction got
right. This is a pilot on 16 pages; it says where to look next, not a rule for BHL. The linker
is deliberately naive, so a better linker could change the second half of that sentence.

## Limitations (known in advance)

- 16 test pages from two books: intervals will be wide, and nothing generalises to "BHL".
- Book and OCR quality are confounded.
- One labeller for the gold; a second labeller on 5 pages only.
- Dev pages are not blind; only test pages are reported as results.
- BHL, the IMPACT transcriptions and PCAS are public and may be in the models' pre-training data.
- A GBIF match is a signal, not proof that the name is the taxon the text refers to.

## What is here so far

| Step | Script | Output |
|---|---|---|
| Load the two English books from `finebooks/bhl-impact-gt`, check license, schema and the PageID join to `bhl-metadata` | `src/load_gt.py` | [`data/reports/01_dataset_check.md`](data/reports/01_dataset_check.md), `data/gt_pages.csv` |
| Fetch BHL legacy OCR for every text page | `src/fetch_legacy_ocr.py` | `data/text/legacy/` (not committed) + SHA-256 manifest |
| Modern OCR (dots.mocr) per page, from FineBooks' public output bucket | `src/fetch_modern_ocr.py` | `data/text/modern_dots-mocr/` (not committed) + manifest |
| Per-page CER of each text version vs the expert transcription | `src/compute_cer.py [--version modern_dots-mocr]` | [`02_cer_legacy.md`](data/reports/02_cer_legacy.md), [`02_cer_modern_dots-mocr.md`](data/reports/02_cer_modern_dots-mocr.md), `data/cer_*.csv` |
| TaxonFinder counts per page + proposed stratified sample | `src/propose_sample.py` | [`data/reports/03_sample_proposal.md`](data/reports/03_sample_proposal.md), `data/sample_proposal.csv` |
| Dev / locked-test split by page blocks | `src/split_sample.py` | `data/sample_split.csv` |
| The 22 sample pages' expert transcriptions, committed for labelling (CC-BY 3.0) | `src/export_sample_texts.py` | [`data/sample/`](data/sample/) |
| Labelling guide and empty gold templates | — | [`ANNOTATION_GUIDE.md`](ANNOTATION_GUIDE.md), `gold/*_TEMPLATE.csv` |
| Read-only gold checker (offsets, field names) | `src/check_gold.py` | `gold/<file>.checked.csv` |
| Rule baseline (gnfinder v1.4.0 + regex) | `src/baseline_rules.py` | `results/<run>_rules-…/` |
| LLM extraction, with sealed test outputs | `src/run_extraction.py`, `src/unseal.py` | `results/<run>/` |
| Scoring: one-to-one matching, per field, page-bootstrap intervals | `src/score.py` | `scores_<split>.csv` |
| Run-to-run noise across repeated dev runs | `src/repeat_report.py` | `results/repeats_<name>/` |
| Pre-registered analyses: paired bootstrap, stage of loss, evidence counters, shadow evaluation | `src/analyze.py`, `src/analysis.py` | `results/analysis_<name>/` |
| Taxon linking (Butler): GBIF name lookup scored against the gold links, with cached responses | `src/link_taxa.py` | `results/linking_<name>/` |
| Gold links from Gloria's accepted names (exact, rank-checked GBIF key lookup) | `src/expand_links.py` | `gold/gold_links_gloria.csv` |
| Second labeller's pack | `src/make_labeller_pack.py` | a folder to send |
| Inter-annotator agreement | `src/agreement.py` | `results/agreement_<name>/` |
| Freeze before unsealing | `src/freeze.py` | `FREEZE.json` |

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

## Running the LLM extraction

The API key is read from the environment variable `EVAL_ANTHROPIC_API_KEY` (set it in the cloud
environment's settings; a new session picks it up). Test-page outputs are **sealed** until the gold
labels exist: see `src/run_extraction.py` and `src/unseal.py`.

```bash
# set-up in a fresh session (texts that are not committed)
python src/load_gt.py && python src/fetch_legacy_ocr.py && python src/fetch_modern_ocr.py
# 1. pilot on 5 dev pages (30 requests, open output), cap $5; prints cost per page
python src/run_extraction.py --pages dev5 --mode sync --max-usd 5
# 2. full run, 22 pages x 3 versions x G0/G1 = 132 requests, as a Message Batch (50% price)
python src/run_extraction.py --pages all --mode batch --estimate-from <pilot_run_id> --max-usd 15
python src/run_extraction.py --collect <run_id>
# 3. after the gold set is done
python src/freeze.py --ready && python src/unseal.py <run_id> --labeller gloria_test
```

**Second LLM: Gemini** (`--provider gemini`, key in `GEMINI_API_KEY`, Google Gen AI SDK
`google-genai`; the model defaults to `gemini-4-carbon`). Same system prompt, task texts, numbered
page text, JSON schemas and `PROMPT_VERSION`; records are written in the same format, so sealing,
`locate.py`, the scorer and `unseal.py` work unchanged. `src/gemini_backend.py` says what is sent
(schema via `response_json_schema`, thinking and temperature at the model default,
`max_output_tokens` 32,768 including thinking) and how token counts become dollars. The prices in
`gemini_backend.PRICES` are the rates valid until 2026-11-30 (they double on Dec 1): update them
before running later.

```bash
python src/run_extraction.py --provider gemini --pages dev5 --mode sync --max-usd 1
python src/run_extraction.py --provider gemini --pages dev --mode batch \
    --estimate-from <gemini_pilot_run_id> --max-usd 1
python src/run_extraction.py --collect <run_id>      # provider is read from config.json
```

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

## Learning notes

- [NHM Planetary Knowledge Base: the knowledge graph (AWS blog posts, 2024)](docs/notes/nhm_pkb_knowledge_graph.md), in Chinese: pipeline, data model, entity matching, and what an evaluation of each layer should measure.

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
gold/          gold labels, deliveries as received, change log, link tables
src/           scripts
results/       one folder per model run or analysis
memo/          one-page Research-to-Product memo (skeleton; filled from results)
tests/         unit tests for the helpers
```
