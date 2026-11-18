# BioEvidenceBench: project brief for Claude Code

> 中文说明：这是给 Claude Code 的项目背景说明。放在代码仓库根目录，命名为 `CLAUDE.md`，Claude Code 每次启动都会自动读取。完整的项目方案见 Claude 文档《BioEvidenceBench 项目落地方案》。

## 1. Who this is for and why it exists

The owner is Gloria (Dekun) Sun. She has about 10 years of product operations experience, most recently at TikTok Shop, where she worked on CRM, attribution, and risk-tiered content review. She holds a materials science master's degree, is studying for an MCIT at Penn part-time, and runs ai4s.fyi, a site tracking AI for Science. She is applying for Research-to-Product, technical program, and scientific product operations roles at frontier AI labs (Google DeepMind first).

This project has three goals, in priority order:
1. **Build hands-on evals experience**: one complete evaluation, from task definition and labeling guidelines to a gold set, metrics, ablations, and error analysis.
2. **Produce a Research-to-Product story**: use data to answer a resource-allocation question, and write it up as a one-page decision memo.
3. **Have something concrete to discuss** with researchers, including at Deep Matters 2026 in London (Nov 26, 2026).

Keep the code simple and well documented. Gloria is comfortable with SQL and some Python; explain non-obvious steps in comments and the README.

## 2. Background (what we learned before starting)

- **Biodiversity Heritage Library (BHL)**: the largest open-access library of biodiversity literature, about 64 million scanned pages. Its text is OCR from old print and has many errors. BHL lost Smithsonian hosting at the start of 2026 and is now funded by member dues, grants, and donations.
- **Cal Academy context**: Gloria volunteers (remotely) with the California Academy of Sciences Scientific Computing team on CAS Lens, a collections site that links specimens to people, expeditions, and literature, including the Academy's Proceedings (PCAS) on BHL. **Do not use any Cal Academy internal data or credentials in this project.** Everything here must use public data.
- **Plazi** extracts taxonomic treatments and material citations from literature with journal-specific templates (GoldenGATE), sends occurrences to GBIF, and only routinely QCs holotype citations. Its 2026 Disentis Roadmap says biodiversity literature is well suited to AI but integration into LLMs is bottlenecked.
- **Natural History Museum, London (NHM)** has an AI & Innovation team with an "AI for BHL" project (OCR, LLMs, annotation workflows, knowledge extraction). One of the team's stated aims is a knowledge base linking collections and literature.
- **FineBooks** (Hugging Face + EleutherAI) is re-OCRing BHL with open models. It published an OCR leaderboard (14 open models), an expert-transcribed ground-truth set, and a Parquet copy of BHL's metadata. FineBooks reportedly says modern OCR is competitive on text accuracy, but its plain-text/Markdown output lacks word-level page coordinates, so it can't directly replace ALTO XML workflows. **This claim is not yet verified against the original source.**
- **Methodological reference**: Lei, Docherty & Cooper (2024), "Materials science in the era of large language models: a perspective," Digital Discovery. Case Study 2 used GPT-3.5/GPT-4 (text) and GPT-4V (images) to find and label micrographs from captions and abstracts in 382 papers (842 micrographs). They compared against **two keyword/regex baselines** (the more aggressive one produced many false positives). Humans labeled in a custom GUI **before** seeing model output. With GPT-4 plus abstracts, micrograph detection sensitivity and specificity were above 90% and material/instrument accuracy above 80%. Caveats: they did **not** study OCR; the GPT-4V stage had no full confusion matrix (its "no false positives" came from inspecting the final dataset). **Our project borrows their evaluation method but studies a different question. Never describe it as a direct extension of their experiment.**

## 3. The research question

> **When does improved OCR stop being the main bottleneck, and when do evidence verification and entity resolution become the limiting factors for trustworthy scientific data extraction?**

The goal is **not** to show that historical literature is harder than modern papers. The answer should guide resource allocation: should the next investment go to better OCR, better LLM extraction, more automated verification, or human reviewers? Either outcome is a useful result.

Sub-questions:
- **RQ1**: How much does OCR quality (legacy OCR vs modern OCR vs expert transcription) change extraction accuracy?
- **RQ2**: How much better is LLM extraction than a simple rule/dictionary baseline?
- **RQ3**: Does requiring verifiable evidence (source positions) reduce hallucination, and at what cost to recall? What level can each output be traced to: page, text span, or page-image coordinates?
- **RQ4**: Can model agreement and deterministic checks help prioritize human review without compromising a predefined reliability target? (Evaluated as a **shadow evaluation**: records are only *flagged* as "proposed auto-accept"; nothing actually skips review in V1.)

Plot extraction F1 against each page's legacy-OCR character error rate (CER) to look for the point below which better OCR stops helping (RQ1). This is an **exploratory pilot with page-level uncertainty estimates**, not a formal benchmark.

## 4. Experimental design

**Two separate datasets. Never pool their results.**
- **Core controlled experiment**: the two English works in FineBooks' expert-transcribed set: Butler, *Birds of Great Britain and Ireland*, vol. 2 (1907, 341 pages) and Reeve, *Conchologia iconica*, vol. 5 (1849, 648 pages). These are birds and shells, **not botany**. Each page gets three text versions: legacy BHL OCR, modern OCR, expert transcription.
- **External domain case**: 5–10 PCAS botany pages (e.g., Eastwood 1898). No expert transcription; compare legacy vs modern OCR with a few labels Gloria makes against the scans. Report separately.

| Dimension | Conditions |
|---|---|
| Ground truth | Gloria labels 20–30 pages independently, **before** seeing any model output, using a written labeling guide |
| OCR | Legacy OCR (BHL) · modern open OCR model · expert transcription |
| Baseline | Rule/dictionary extraction · LLM extraction |
| Evidence grounding | No evidence required · must return verifiable source positions |
| Error analysis | OCR-sensitive · extraction/reasoning · ambiguous/mixed |
| Human review | Review everything · shadow evaluation of risk-based prioritization |

Keep the core matrix small. Use 2 LLMs. Run the context ablation (single page vs page + title + previous page) only on the best configuration.

**Page sampling (stratified, ~24 pages, half from each book)**: first compute each candidate page's legacy-OCR CER against the expert transcription. Then sample about 8 entity-rich pages, 6 low-density pages, 4 pages with no target entities (to measure false positives), and 6 poor-OCR pages (strata may overlap). Cover low, medium, and high CER. `page_name` can help find candidate pages, but its names are auto-detected, it has no localities, and it cannot prove what a page contains.

**V1 scope: entity extraction + evidence grounding only.** Relation extraction (which locality belongs to which species) and entity resolution (historical name → database ID) are V2, or a qualitative look at ~5 pages. The annotation unit is a **mention**: a character span in the expert transcription plus a field type. Outputs on legacy/modern OCR are mapped to expert-transcription positions by character alignment before scoring; unaligned outputs are counted separately.

**Extraction schema** (per mention): field type is one of `taxon`, `locality`, `date`, `collector` (optional). In the evidence-required condition, every output carries its position in the numbered input text, for example:

```json
{"taxon": {"line": 12, "start": 4, "end": 22},
 "locality": {"line": 13, "start": 0, "end": 18},
 "date": {"line": 13, "start": 30, "end": 41},
 "collector": null}
```

**Critical design rule: the model never rewrites source text.** Number the input lines; the model returns line and character positions only; code slices the text from the source. This keeps every output traceable and stops the model from silently "fixing" OCR errors.

**Rule/dictionary baseline**: scientific names from TaxonFinder (the `page_name` table in bhl-metadata); localities and dates via regex/gazetteer-style patterns. Keep it simple and documented.

**Deterministic checks**: date parses to a plausible year/date; the cited span actually contains a value of the right type. GBIF name matching belongs to the entity-resolution layer: log it as a separate signal only; a GBIF match does not prove the name is the taxon the text refers to.

**Shadow evaluation (RQ4)**: flag a mention as "proposed auto-accept" if both LLMs extract it and the deterministic checks pass. **Do not skip review in V1.** Score the flagged set against the gold set: actual precision, errors inside it, mentions both models missed, and review workload if reviewers worked in priority order. Two models can share the same bias (e.g., both guess the same plausible but wrong name from a misread OCR string), so agreement is not correctness. 20–30 pages with zero observed errors still cannot show 95% accuracy; conclusions are about prioritization, not about safely skipping review.

**Evidence grounding, three levels**: Level 1 page (correct BHL PageID) and Level 2 text span (correct character range in that text version) are evaluated fully. Level 3 image (map back to the region on the scan) is demonstrated on a few pages only: expert transcription via its PAGE XML region polygons, legacy OCR via hOCR. A correct Level 2 span only proves the model pointed at some input text; if the OCR is wrong, a precise span does not fix the scientific error.

**Error analysis, three groups, multi-cause allowed**: OCR-sensitive (result changes when the OCR input changes; note that switching to expert transcription also changes paragraph order and line breaks, so this shows sensitivity, not proof of a character error) · extraction/reasoning (still wrong on expert transcription) · ambiguous/mixed (historical taxonomy, annotation inconsistency, layout plus OCR, missing reading order on ~19% of ground-truth pages). Don't force each error into a single cause.

## 4a. V1 scope after the design review (2026-11-18). Where this conflicts with sections 3-5, this wins.

Ship fast: the lean V1 below, no fixed delivery dates. Everything else is V2.

**Main question: unchanged** (Gloria, 2026-11-18): *When does improved OCR stop being the main bottleneck, and when do evidence verification and entity resolution become the limiting factors for trustworthy scientific data extraction?* Treat "when" as something to measure, not a promise that one threshold exists; "no single threshold" is a valid answer.

**Do not build an OCR benchmark.** FineBooks already scores 26 OCR models on these pages, and NHM (Hiris Gu) has re-run the benchmark with Mistral OCR 3, the model NHM plans to use (Rod Page, BHL forum, 2026-08-12). Our contribution is what happens *downstream* of OCR.

**Modern OCR source**: FineBooks' public per-page outputs, `hf://buckets/finebooks/bhl-ocr-outputs` (`src/fetch_modern_ocr.py`). Default row `dots-mocr` (lowest CER on the board, MIT licence). Its output is Markdown with one paragraph per line and no coordinates. Other rows of the same bucket give more OCR-quality levels *for the same page*, which is the cleanest way to vary CER while holding the page constant.

**In V1**
- **E1 OCR**: legacy OCR vs modern OCR (dots.mocr) vs expert transcription. Besides page CER, measure **entity-span CER** (CER inside gold spans) and **entity preservation** (gold name survives intact). Add **controlled perturbation** of the expert text, using the character confusions observed in real legacy OCR; report it separately from natural OCR.
- **E2 extraction**: mention-level rule baseline run on the same text (gnfinder for names, regex for localities and dates); `page_name` (TaxonFinder) is a page-level baseline only. Two LLMs from different families.
- **E3 evidence**: G0 (extraction only, code aligns values to the source afterwards) vs G1 (same schema plus evidence). In G1 the model returns `line` + a **verbatim quote**; code finds the quote in that line and slices the value from the source. A quote that does not match the source exactly is logged as a *silent correction*. Metrics: invalid evidence rate, unsupported claim rate, incorrect normalisation rate (not "hallucination rate", which is zero by construction when values are sliced).
- **E4-lite entity resolution**: Butler taxon mentions only. Gold link type per mention: exact / synonym / fuzzy / higher_rank / none / ambiguous, plus GBIF usage key. GBIF match is a signal, not proof.
- **RQ4**: shadow evaluation plus a **risk-coverage curve**. No review is skipped.
- **Dev / locked test split** (`data/sample_split.csv`). Prompts, checks and thresholds are tuned on dev only. Write `PREREGISTRATION.md` (analysis plan and what would falsify each hypothesis) before touching the test set.
- Report per book. Book and CER are confounded (Reeve has 2 low-CER pages, Butler 8 high-CER pages), so pooled F1-vs-CER is descriptive only.
- Disclose contamination risk: BHL, PCAS and the IMPACT transcriptions are all public and may be in pre-training data.

**Next steps (handoff, 2026-11-18)**: the extraction pipeline is built and tested offline (`src/prompts.py`, `src/locate.py`, `src/run_extraction.py`, `src/unseal.py`). Gloria approved Claude Opus 5.5 and a total budget of $15–30. Order: (1) fetch texts, (2) pilot `--pages dev5 --mode sync --max-usd 5`, report cost per page, (3) full `--pages all --mode batch` with the pilot as `--estimate-from` and `--max-usd 15`, (4) never open or print sealed test outputs; Gloria labels next. The prompt uses ANNOTATION_GUIDE v0.1 defaults; if she changes them, bump `PROMPT_VERSION` and re-run. A second LLM from another provider is still to be chosen (needs its own key).

**V2**: relation extraction, real human-review timing study with a reviewer who did not label gold, vision-language end-to-end baseline, multilingual books, a larger sample.

## 5. Metrics

- Per-field, mention-level precision, recall, F1 (exact and lenient match), with the number of gold mentions per field (dates may be sparse in Reeve)
- Extraction F1 as a function of page CER (RQ1)
- False positives on pages with no target entities
- Hallucination rate: output values not present in the source
- Grounding accuracy at Level 1 and Level 2; Level 3 on demo pages only
- Shadow evaluation: share flagged, precision of the flagged set, errors inside it, mentions both models missed, review workload in priority order
- Human review minutes per page; API cost per page
- 95% bootstrap intervals resampled by page, **reported per book**. Pages within a book are not independent, and two books can't estimate cross-book generalization. Never claim a best configuration for all of BHL.

## 6. Data sources (all public)

| Source | Use | Notes |
|---|---|---|
| `finebooks/bhl-impact-gt` (Hugging Face) | Expert transcription (OCR ground truth); region-level coordinates | 6 works, 1708–1913, 2,165 pages; only Butler 1907 and Reeve 1849 are English. CC-BY 3.0 (attribute IMPACT / BHL). One row per page: `image`, `text`, `markdown`, `docling`, `xml` (PAGE XML with region polygons), `PageID`, `BarCode`. No word-level coordinates; no legacy OCR included; ~19% of pages lack explicit reading order. |
| `finebooks/bhl-metadata`, config `page_name` | Rule baseline (TaxonFinder) for names; candidate-page finder | 216,874,371 name occurrences, 4,142,825 distinct names; page-level only, no positions, no localities; auto-detected on legacy OCR. Metadata is CC0. Use the `item` table's copyright fields to check rights. |
| BHL legacy OCR | Legacy OCR condition | Not in bhl-impact-gt; fetch by PageID/ItemID from `https://www.biodiversitylibrary.org/itemtext/<ItemID>` or Internet Archive `<identifier>_djvu.txt`, then slice to selected pages. |
| Internet Archive hOCR | Word-level coordinates (RQ3) | Corresponds to legacy OCR text only. |
| One open OCR model from the FineBooks BHL OCR leaderboard | Modern OCR condition | Pick one that runs locally or cheaply. |
| ~5 PCAS botany pages (3rd series Botany, vol. 1, 1897–1900; e.g., Eastwood 1898, San Nicolas Island) | Domain case study | No expert transcription; compare legacy vs modern OCR only. |

Prefer DuckDB reading Parquet directly from Hugging Face for metadata queries.

## 7. Repository layout

```
bhl-extraction-eval/
  CLAUDE.md            this brief
  README.md            project summary and results
  ANNOTATION_GUIDE.md  labeling guide, versioned
  data/                selected page IDs and the three text versions
  gold/                Gloria's gold labels and agreement labels
  src/                 page selection, extraction, baselines, checks, routing, metrics
  results/             one folder per run: config, prompts, raw outputs, scores
  memo/                one-page Research-to-Product memo
```

## 8. Rules for Claude Code

1. **Never create, edit, or "pre-fill" gold labels.** The gold set must be Gloria's independent work. Model-generated labels may only go into clearly separate files used for verification-mode review *after* the gold set is done.
2. **Reproducibility on every run**: save model name and version, full prompt, input text source and SHA-256 hash, decoding settings, raw output, and timestamp in `results/<run_id>/`.
3. **Never let a model rewrite source text** (see design rule above).
4. **Public data only.** No Cal Academy internal data or credentials. Check licenses before committing data; don't commit large raw data, commit scripts that fetch it.
5. Before any paid API batch, run on 5 pages, report the cost per page, and wait for Gloria's go-ahead.
6. Keep the labeling workflow spreadsheet-friendly: export review sheets as CSV with columns `page_id · snippet · gold_label · model_label · match · review_seconds`.
7. Flag anything unverified (for example the FineBooks coordinates claim) rather than stating it as fact in the README or memo.

## 9. Work plan

1. One-page plan and a 5–10 page pilot: fetch the three text versions and run one extraction end to end
2. Get feedback on the eval design (Deep Matters and other conversations)
3. Compute CER for candidate pages and pick 20–30 pages from Butler and Reeve with the stratified rule
4. Labeling guide v1; Gloria labels the gold set independently on expert transcriptions; a friend labels 5 pages for agreement
5. Run the matrix: three text versions × rule baseline or LLM × with/without evidence requirement
6. Shadow evaluation: flag proposed auto-accepts, score them against the gold set, log review time
7. Analysis: metrics with per-book uncertainty, three error groups, grounding Levels 1–2 (Level 3 on a few pages)
8. Run the PCAS botany pages as the external case, reported separately
9. Ship: GitHub repo, ai4s.fyi write-up, one-page Research-to-Product memo

## 10. Suggested first tasks for Claude Code

1. Set up the repo skeleton above with a Python environment (`duckdb`, `pandas`, `datasets`, `requests`).
2. Load the Butler and Reeve pages from `finebooks/bhl-impact-gt` and confirm the schema, license, and PageID/BarCode join to `bhl-metadata`.
3. Fetch legacy BHL OCR for those pages, compute per-page CER against the expert transcription, and summarize the CER distribution per book.
4. Join `page_name` counts per page and propose a stratified sample (entity-rich, low-density, no target entities, poor OCR) for Gloria to approve.
5. Draft (do not fill) `ANNOTATION_GUIDE.md` and an empty mention-level gold CSV template (`page_id · start · end · field · text · notes`).

## 11. References

- Lei, Docherty, Cooper (2024), Digital Discovery: https://pubs.rsc.org/en/content/articlelanding/2024/dd/d4dd00074a (arXiv: https://arxiv.org/abs/2403.06949)
- FineBooks: https://finebooks-readme.static.hf.space/README.md
- bhl-impact-gt: https://huggingface.co/datasets/finebooks/bhl-impact-gt
- bhl-metadata: https://huggingface.co/datasets/finebooks/bhl-metadata
- BHL OCR leaderboard: https://huggingface.co/spaces/finebooks/bhl-ocr-leaderboard
- Common Pile BHL subset: https://huggingface.co/datasets/common-pile/biodiversity_heritage_library
- Plazi TreatmentBank: https://plazi.org/treatmentbank/
- NHM AI & Innovation: https://nhmuk.github.io/ddi/teams/ai-innovation
- GBIF species match API: https://techdocs.gbif.org/en/openapi/v1/species
