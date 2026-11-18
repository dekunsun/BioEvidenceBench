# Pre-registration: analysis plan for the locked test set

**Status: DRAFT, written 2026-11-18 by Claude Code for Gloria to review.** Nothing in the test set
has been opened. This plan is frozen, together with the code it names, by recording the commit
hash below **before** `src/unseal.py` is run on any test outputs. Anything decided after unsealing
goes in the deviations log at the bottom, with the reason.

Frozen at commit: `__________` (fill in when Gloria approves)

## 1. What is scored

| Item | Value |
|---|---|
| Pages | 16 locked test pages (`data/sample_split.csv`, split = test): Butler 7, Reeve 9 |
| Text versions | `expert` (IMPACT-BHL transcription), `legacy` (BHL OCR), `modern_dots-mocr` (FineBooks output) |
| Extractors | rule baseline (gnfinder v1.4.0 + regex, condition `RULE`); Claude Opus 5.5 with prompt `p2-guide-v0.2` (conditions `G0`, `G1`); Gemini 4 Carbon with the same prompt once run (for RQ4) |
| Runs | `20261118-0903_rules-gnfinder-v1.4.0_all`; the p2 Opus run (`*_claude-opus-5-5_all_batch_p2`); the Gemini run (to be added before freezing) |
| Gold | `gold/gold_mentions_gloria.csv`, ANNOTATION_GUIDE version recorded in each row (expected v1) |
| Agreement | 5 test pages labelled independently by a second person; span agreement per field reported before scoring |

Pages are never pooled across books for a headline number; every result is reported per book.

## 2. How a prediction is matched (fixed in `src/score.py`)

- Predicted spans are mapped to expert-text offsets by character alignment; spans that cannot be
  placed are **unaligned** and count as false positives.
- Three levels, one-to-one per field: **lenient** (overlap), **exact** (identical span), **value**
  (overlap and identical text after normalisation). The **value** level is the primary metric,
  because a correctly placed but misread name is wrong data.
- Located statuses come from `src/locate.py` (fuzzy threshold 85). These rules were tuned on dev
  pages only.

## 3. Questions, primary measures and what would count against each hypothesis

The thresholds below are decision rules written in advance, not significance tests. With 7 and 9
pages per book, intervals will be wide; a result whose interval spans the threshold is reported as
inconclusive.

| | Primary measure (per book, per field and all fields) | Hypothesis | Counts against it |
|---|---|---|---|
| RQ1 OCR | Value-level F1 of Opus G1 on legacy, modern, expert; paired page-bootstrap interval of each difference. Secondary: recall vs entity-span CER of each gold mention. | In Reeve, legacy → modern raises value F1 by at least 0.10, and modern → expert by less than 0.05. | modern → expert gain of 0.05 or more (OCR still the bottleneck), or legacy → modern gain under 0.10 |
| RQ2 baseline | Lenient and value F1, LLM (G1) vs rule baseline, on each text version | LLM recall is higher for every field; the gap is largest for person and institution | Rule baseline F1 equal to or above the LLM for taxon on the expert text |
| RQ3 evidence | Unsupported-output rate (G0: `not_found` + `fuzzy`; G1: `invalid_evidence` + `silent_correction`) and recall, G1 vs G0 | G1 lowers the unsupported rate and loses less than 0.05 recall | G1 recall lower by 0.05 or more with no drop in unsupported outputs |
| RQ4 review | Precision of mentions flagged "proposed auto-accept" (both LLMs extract it at lenient level in the same version, and it is located `exact` or `cross_line`) vs the rest; risk-coverage curve; mentions both models missed | Flagged precision exceeds unflagged precision by at least 0.10 | No difference, or most flagged errors are shared by both models |
| Entity resolution (Butler taxa) | Link-type accuracy against `gold/gold_links_gloria.csv` | To be specified once the linking step exists | — |

Every outcome above is reportable, including all of them failing. The main question ("when does
OCR stop being the bottleneck") is answered from RQ1 plus the error analysis, and "no single
threshold" is a valid answer.

## 4. Uncertainty

- 1,000 page-level bootstrap resamples, seed 20261118, percentile 95% intervals, per book.
- Differences between conditions use paired resampling (the same pages in both arms).
- No correction for multiple comparisons: this is an exploratory pilot, and every comparison
  in this plan is reported, not only the significant ones.

## 5. Error analysis (after scoring)

Every false positive and false negative of Opus G1 on the test pages is tagged by Gloria with one
or more of: OCR-sensitive, extraction or reasoning, ambiguous or mixed (CLAUDE.md section 4).
Counts are reported per book and field.

## 6. Exclusions and edge cases

- A failed or empty API response counts as zero predictions for that page (all gold mentions are
  false negatives) and is listed.
- Pages whose gold is a single `none` row contribute only false positives.
- No page is dropped after unsealing.

## 7. Contamination and other limits to state with the results

BHL text, the IMPACT transcriptions and FineBooks outputs are public and may be in the models'
training data. Two books cannot estimate generalisation to BHL as a whole.

## Deviations log

| Date | Change | Reason |
|---|---|---|
| | | |
