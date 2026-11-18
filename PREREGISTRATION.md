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

## 8. Reporting and audit rules borrowed from the ADEPT reproduction

Added 2026-11-18 (still part of the draft). Source: the eight lessons in `adept_repro/NOTES.md`
section 6. ADEPT's published numbers all reproduced exactly, but some described a different
operating point than the one ADEPT actually runs. These rules are meant to stop the same thing
happening here. The "Status" column says whether the rule is already met by the code, or what
still has to be built **before the freeze commit**.

| # | Rule | How it is checked | Status |
|---|---|---|---|
| 1 | **Every reported number carries its operating point**: split (`dev` / `test`), text version, condition, prompt version, run id, and any threshold (for example the `locate.py` fuzzy threshold 85). A number without these tags is not reported. | `scores_*.csv` rows carry book, version and condition; the results table in the README and memo adds split, prompt version and run id. | Partly met. To do: write split, prompt version and thresholds into each scores file, not only in the folder name. |
| 2 | **No tuning on the test set.** Prompts, `locate.py` thresholds, normalisation and the RQ4 flag rule are chosen on dev pages only. ADEPT picked its classifier checkpoint on its own test split, so its test score is optimistic. | Test outputs stay sealed (`src/unseal.py`) until this plan is frozen; any change made after unsealing goes in the deviations log. | Met. |
| 3 | **Leakage and contamination are checked and stated, not only mentioned.** ADEPT's classifier test set shares 64 of 1,192 texts with its training set. Our version of this risk is pre-training contamination (section 7). | (a) Dev and test pages do not overlap (`data/sample_split.csv`). (b) Optional probe: give a model the first lines of a test page and measure whether it continues the expert transcription verbatim. | (a) Met. (b) Not built. It needs paid API calls, so it runs only after a 5-page cost report and Gloria's go-ahead (CLAUDE.md rule 5); if not run, the limitation is stated as untested. |
| 4 | **Errors are never counted as "nothing found".** When eFloras returned HTTP 403, ADEPT logged "No results" and the run still reported success. Each page × version × condition gets one outcome status: `ok`, `empty` (valid response, no mentions), `api_error`, `parse_error`, `truncated` (stop reason `max_tokens`); each mention keeps its `locate.py` status (G1: `exact`, `cross_line`, `wrong_line`, `silent_correction`, `invalid_evidence`; G0: `exact`, `case_variant`, `layout_variant`, `fuzzy`, `not_found`) plus unaligned. | The scores report includes a table of outcome counts per run, next to the F1 numbers. Section 6 still applies (failed responses score as zero predictions) and every such page is listed by id. | Partly met: `run_extraction.py` records `error` and `stop_reason`, and `score.py` counts unaligned and not-located mentions. To do: one outcome-status column and the counts table. |
| 5 | **Recall is measured at each stage, not only at the end.** ADEPT's funnel (866 pages → 80 → 13 for *Leersia*) has a published score for only one stage. Our stages: (i) gold mention survives OCR (entity preservation, entity-span CER); (ii) mention extracted (lenient recall); (iii) evidence located and value correct (value-level recall). | Report the three recalls side by side, per book and text version. The RQ1 answer says at which stage most gold mentions are lost on each version. | Partly met: `score.py` already writes entity-span CER and a `preserved` flag per gold mention (`results/entity_span_cer_<split>.csv`) and lenient/value scores. To do: one combined per-stage table. |
| 6 | **The scorer is strict, explicit and auditable**, like ADEPT's evaluation notebook: join on a unique key (page_id, field, span), never on row order; normalisation rules written down; lenient matching kept as a separate column, never merged into the headline; stop on duplicate or missing keys. | Each scoring run writes `evaluation_settings.json` (SHA-256 of the gold file and of every prediction file, code commit, matching rules, normalisation, thresholds) and `discrepancies.csv` (every FP and FN with gold text, predicted text and status). `discrepancies.csv` is also the input for the error analysis in section 5. | To do: `score.py` writes neither file yet. |
| 7 | **A quote is not proof.** ADEPT keeps a `verbatim` word for each trait, but the word "Stem" is enough to output `habitat = terrestrial`. In G1, a quote that matches the source shows only *where* the model looked. The value must also be stated by the quoted text and have the right type. | For G1 outputs: the sliced value must lie inside the quoted text, and the deterministic type check must pass (date parses; the span is a name, place, person or institution). Outputs failing this count toward the **unsupported claim rate** (RQ3), separately from invalid evidence and silent corrections. | Partly met: `locate.py` checks that the quote matches the source line. To do: the value-inside-quote and type checks, as a separate counter. |
| 8 | **The sample's make-up is stated next to every headline number.** ADEPT's 0.867 trait F1 is on 50 development descriptions, only 3 of them from BHL. | Every results table states the number of pages and gold mentions per book and field, and whether the numbers are dev or test. Butler, Reeve and PCAS are never pooled. Fields with fewer than 10 gold mentions are marked "too few to compare". | Mostly met by sections 1 and 3 (per-book reporting). To do: add the gold-mention counts and the "too few" marker to the report template. |

Engineering rules from the same reproduction, already followed: pin code and model versions (git
commit, model id, prompt version in every `results/<run_id>/`); record input SHA-256; check
whether a data source has changed format before reusing it (BHL's OCR export renamed its files
between 2025 and 2026, and ADEPT's asset script stopped matching them).

## 9. Additions after the guide decisions and a design review (2026-11-18, still draft)

**Frozen before unsealing** (ANNOTATION_GUIDE section 4). Fill in at the freeze commit:

| Item | Value |
|---|---|
| `guide_version` | v0.4 (or later, if labelling adds rules) |
| `prompt_version` | `p3-guide-v0.4` |
| Output schema | `SCHEMA_G0`, `SCHEMA_G1` in `src/prompts.py` at the freeze commit |
| Scorer | `src/score.py` and `src/locate.py` at the freeze commit |
| Model configuration | per run `config.json`: model id, effort, max tokens, provider |

**Fields.** The primary number is `ALL_PRIMARY` (taxon, person, locality, institution, date).
`vernacular` is scored and reported in its own rows and never enters `ALL_PRIMARY` or the taxon F1.
Section 1's Opus run is the `p3` run (the `p2` run is superseded).

**Ambiguous gold rows** (`adjudication = ambiguous`) are optional: no credit, no penalty, not a
false negative. Their count is reported per book and field. All `UNCLEAR` rows must be adjudicated
before scoring; `score.py` stops if any is left.

**Section 2 correction.** Matching is not "first unused gold mention": each prediction takes the
unused gold mention it overlaps most, so the result does not depend on row order.

**Known differences between text versions other than character accuracy.** They limit what RQ1
can claim, and are stated with the results:
- The modern OCR text is Markdown: scientific names often arrive wrapped in `*…*` or `**…**`, a
  cue the expert and legacy texts do not carry. It also has one paragraph per line, while expert
  and legacy keep the printed line breaks (so names broken across lines exist only there).
  A model could therefore score *higher* on modern OCR than on the expert text for reasons that
  are not OCR accuracy.
- Planned control (needs Gloria's go-ahead, about one third more API cost): a fourth text
  version, modern OCR with Markdown marks stripped (`common.strip_markdown`).
- The expert text itself is one reading order; about 20% of Butler's text pages lack an explicit
  `<ReadingOrder>`.

**Run-to-run noise.** Claude Opus 5.5 does not allow a fixed temperature, and each condition is one
sample. Planned (needs go-ahead, about $0.40 per repeat): three repeats of the dev pages under the
frozen configuration. A difference between conditions on the test set that is smaller than the
spread across repeats is reported as not distinguishable from noise.

**Where a gold mention is lost (the main answer).** For every gold mention and each OCR version:
(a) preserved in the OCR text or not (entity-span check); (b) extracted or not (lenient); (c) value
correct or not. The headline table is the count of mentions lost at (a), at (b) given (a), and at
(c) given (b), per book and version. "OCR is the bottleneck" means most losses are at (a).

**Sample strata.** The strata were defined before `person`, `institution` and `vernacular` were
added, using cues for names, places and dates only. A "no_entities" page may therefore contain
people, institutions or vernacular names. False positives on empty pages are computed on pages
whose gold is a single `none` row, whatever their stratum.

**Sample size, stated plainly.** 7 Butler and 9 Reeve test pages give wide page-level intervals;
several decision rules in section 3 will probably come out "inconclusive". That outcome is
reported as such, with the mention counts.

**Rule baseline.** Its regexes were written with knowledge of these two books (for example the
list of authority abbreviations) and checked on dev pages. It is an in-domain baseline, and is
described that way.

**Still to build before the freeze commit**: paired page-bootstrap for differences between
conditions; the per-stage loss table above; `evaluation_settings.json` and `discrepancies.csv`
(section 8, rule 6); the RQ3 counters and the RQ4 flag.

## Deviations log

| Date | Change | Reason |
|---|---|---|
| | | |
