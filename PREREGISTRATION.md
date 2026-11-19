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
| Text versions | `expert` (IMPACT-BHL transcription), `legacy` (BHL OCR), `modern_dots-mocr` (FineBooks output, Markdown), `modern_dots-mocr_plain` (same text, Markdown marks deleted) |
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
| Entity resolution (Butler taxa only) | Link recall (correct / gold `resolved`) and link precision of a plain GBIF name lookup against `gold/gold_links_gloria.csv`, on the gold mention text and end to end per text version (`src/link_taxa.py`). `correct` needs the printed rank and the gold accepted taxon. | With Opus G1 on the expert and on the modern OCR text, more gold-resolved names are lost at linking (wrong taxon, genus only, no record) than before it (not extracted). Rule: share lost at linking minus share lost before it `greater_than 0`, paired page bootstrap. | The interval of that difference lies at or below 0: OCR and extraction still lose more names than linking does |

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
| `guide_version` | gold: v0.10 or later (labelling may add rules); prompt: written from v0.6 and not changed by rules found on test pages |
| Gold files | SHA-256 of `gold_mentions_*.csv`, `annotation_issues_*.csv`, `gold_links_*.csv` at the freeze |
| `prompt_version` | `p4-guide-v0.6` |
| Output schema | `SCHEMA_G0`, `SCHEMA_G1` in `src/prompts.py` at the freeze commit |
| Scorer | `src/score.py` and `src/locate.py` at the freeze commit |
| Linker | `src/link_taxa.py` at the freeze commit: GBIF `species/match` v1, name only (no rank or class hint), `clean_name` and `expand_abbreviation` as coded |
| Model configuration | per run `config.json`: model id, effort, max tokens, provider |

**Fields.** The primary number is `ALL_PRIMARY` (taxon, person, locality, institution, date).
`vernacular` is scored and reported in its own rows and never enters `ALL_PRIMARY` or the taxon F1.
Section 1's Opus run is the `p4` run (the `p2` run is superseded; `p3` was run on dev pages only).

**Ambiguous gold rows** (`adjudication = ambiguous`) are optional: no credit, no penalty, not a
false negative. Their count is reported per book and field. All `UNCLEAR` rows must be adjudicated
before scoring; `score.py` stops if any is left.

**Section 2 correction.** Matching is strictly one-to-one with an optimal assignment
(`scipy.optimize.linear_sum_assignment` in `score.match_page`): a gold mention is matched by at
most one prediction and a prediction matches at most one gold mention; two predictions on one
gold mention count as one true positive and one false positive. Unit tests cover these cases.
Both the number of ambiguous gold rows excluded and the number of predictions that fell on them
are reported (`gold_ambiguous_excluded`, `pred_on_ambiguous_excluded`).

**Guide v0.5 additions (Gloria, 2026-11-18).** (a) Non-contiguous text makes no gold row; it is
listed in `gold/annotation_issues_<labeller>.csv`, and `score.py --issues` sets aside every
prediction that touches a listed fragment (neither right nor wrong; counts reported as
`pred_in_issue_region_excluded`). (b) Linking is correct only when `resolved` at the printed rank;
`partial` (genus-only for a species name), `ambiguous` and `unresolved` are reported as separate
counts and never added to species-level success. (c) The gold set is complete before unsealing:
double labelling of 5 test pages, adjudication of every disagreement and `UNCLEAR` row, then the
gold files' SHA-256 are written here. Corrections after unsealing go through independent review
without model answers, are logged in `gold/gold_changes.csv`, and scores are reported for both
the frozen and the corrected gold. (d) The prompt was `p3-guide-v0.5`; it is `p4-guide-v0.6` after the dev labelling (below).

**Order of work (Gloria, 2026-11-18).** Dev results and this plan are reported first; the
configuration is frozen; only then are the test pages run with the frozen prompt and unsealed.
Earlier sealed test outputs (prompts p1 and p2) are never unsealed for results.

**Known differences between text versions other than character accuracy.** They limit what RQ1
can claim, and are stated with the results:
- The modern OCR text is Markdown: scientific names often arrive wrapped in `*…*` or `**…**`, a
  cue the expert and legacy texts do not carry. It also has one paragraph per line, while expert
  and legacy keep the printed line breaks (so names broken across lines exist only there).
  A model could therefore score *higher* on modern OCR than on the expert text for reasons that
  are not OCR accuracy.
- Control (approved by Gloria, 2026-11-18): a fourth text version, `modern_dots-mocr_plain`, the
  same OCR text with Markdown emphasis and heading marks deleted. It is built by deletion only
  (`common.markdown_to_plain`): no OCR character, reading order or line break changes, which
  `export_sample_texts.py` checks for every page; lone printed asterisks (footnote marks) are
  kept. Its input hashes are recorded separately in `data/sample/manifest.csv`. Comparing it with
  `modern_dots-mocr` isolates the effect of formatting; comparing it with `expert` is the cleaner
  test of OCR character accuracy.
- The expert text itself is one reading order; about 20% of Butler's text pages lack an explicit
  `<ReadingOrder>`.

**Run-to-run noise.** Claude Opus 5.5 does not allow a fixed temperature, and each condition is one
sample. Approved by Gloria (2026-11-18): three repeats of the dev pages with prompt p3, all text
versions and G0/G1, reported by `src/repeat_report.py` (output consistency; and, once dev gold
exists, each repeat's F1 with mean and standard deviation). The test set is never used to choose a
prompt or a best condition. A difference between conditions on the test set that is smaller than the
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

**Built (2026-11-18): `src/analysis.py`, run by `src/analyze.py`, unit-tested in
`tests/test_analysis.py`.** These definitions are now part of the plan:

- *Paired bootstrap* (`paired_bootstrap`): metric(A) - metric(B) on the pages both arms share, the
  same pages drawn for both arms in each of 1,000 resamples (seed 20261118), percentile 95%
  interval. `verdict` compares the interval with the rule from section 3: `supports` / `against` /
  `inconclusive` (interval contains the threshold) / `no data` (no gold mentions in an arm).
  Rules as coded: RQ1 modern - legacy value F1 `at_least 0.10` and expert - modern value F1
  `less_than 0.05` (Reeve, primary fields together); RQ2 LLM - rule recall `greater_than 0` per
  primary field and book, and LLM - rule value F1 `greater_than 0` for taxon on the expert text;
  RQ3 recall(G1) - recall(G0) `greater_than -0.05` per book and text version. All other
  comparisons in `comparisons.csv` are descriptive.
- *Stage of loss* (`stage_loss`), one stage per strict gold mention: `lost_at_ocr` (the OCR text of
  the span is not the gold text after value normalisation; `of_which_still_found` counts those
  the model located anyway), `lost_at_extraction` (survived OCR, no lenient match),
  `lost_at_value` (matched, text differs: boundary), `kept`. On the expert text nothing is lost
  at OCR.
- *RQ3 counters* (`evidence_counters`): unsupported outputs as defined in section 3, plus
  `wrong_line`, `type_check_failed` and copied line labels, per book, version and condition.
- *Type check* (`type_check`), deliberately loose: empty; longer than 100 characters; a `date`
  with neither a year (1500-1999) nor a month; no letters; no capital letter (taxon, person,
  locality, institution); a digit (taxon, vernacular).
- *RQ4 flag* (`flag_auto_accept`), on the main LLM's G1 predictions: flagged when the second
  model's G1 output has an overlapping span of the same field on the same page and text version
  (one-to-one), the evidence status is `exact` or `cross_line`, and the type check passes.
  Tiers for the risk-coverage curve: 0 flagged; 1 agreement only; 2 clean evidence only; 3 neither.
  Correctness is value level. `rq4_summary` reports precision of flagged vs unflagged with a
  paired bootstrap (rule `at_least 0.10`), errors inside the flagged set, and gold mentions
  missed by both models. Two runs of the *same* model agree on about 99% of mentions (dev
  repeats), so the flag is only informative with a second model from another provider.
- *Request outcomes* (`outcome_table`): `ok` / `empty` / `api_error` / `parse_error` / `truncated`.
- *Audit trail*: `evaluation_settings.json` (hashes of gold, issues and every mentions file,
  code commit, matching and bootstrap settings) and `discrepancies.csv` (every false positive
  and false negative, with empty `error_group` and `error_note` columns for section 5).

- *Taxon linking* (`src/link_taxa.py`, Butler only; built 2026-11-18, smoke-tested against a
  throwaway reference). The linker is a plain lookup of the name string in GBIF's
  `species/match` service. Two variants are always reported: `printed` (the string as it
  stands, after layout clean-up only) and `expanded` (an abbreviated genus such as `A. gulgula`
  is first expanded from the nearest earlier binomial on the page). `expanded` is the primary
  variant. One outcome per gold link row:
  gold `resolved`: `correct` (record at the printed rank and its accepted key equals the gold
  `accepted_usage_key`), `wrong_taxon`, `partial_only` (another rank, e.g. genus for a species
  name; never correct), `no_link`, `not_extracted` (end to end only);
  gold `partial` or `unresolved`: `overclaim` (a record at the printed rank was returned) or
  `correct_abstain`; gold `ambiguous`: set aside and counted.
  Link recall = correct / gold resolved. Link precision = correct / (correct + wrong_taxon +
  overclaim). Two arms: the gold mention text (linking alone) and each run's extracted values
  per text version (end to end; the name is the lenient-matched prediction's value). Results
  are also split by name form, printed rank and `evidence_source`. Intervals: page bootstrap.
  Raw GBIF responses are saved with their fetch time, because the backbone changes.
  *Known limits.* (1) Where a gold link was itself decided on gbif.org, gold and linker share
  a source and agreement is optimistic; the split by `evidence_source` shows how much rests on
  it. (2) Three dev and seven test pages of one book: most intervals will be wide. (3) The
  linker gets no class hint and no fuzzy threshold of ours; GBIF's own matching decides.
  (4) The GBIF backbone has no subfamily rank. Gold taxon mentions printed as a subfamily
  (`Emberizinæ`, `FRINGILLINÆ`, `SYLVIINÆ`: 8 of Butler's 43 test mentions) are kept in the
  gold file but left out of link scoring and counted in the report (Gloria, 2026-11-20).
  (5) Gold keys come from Gloria's accepted names via `src/expand_links.py` (exact, accepted,
  rank-checked match; for a homonym such as `Passer` only the single accepted bird record).
  Where her accepted name is a synonym in the backbone (`Cercotrichas galactotes` →
  `Erythropygia galactotes`, 5788860) the key of the backbone's accepted name was entered on
  her decision (2026-11-20), consistent with the rule that a synonym counts when its accepted
  taxon is the gold one. The linker itself is unchanged: name only, no hint.

**Entity-resolution hypothesis confirmed (Gloria, 2026-11-19: "假设可以，就按这条写进预注册").**
The hypothesis, rule and falsifier in the entity-resolution row of section 3 are approved as
written: with Opus G1 and the `expanded` linker, on the expert and on the modern OCR text, the
share of gold-resolved Butler names lost at linking minus the share lost before it is
`greater_than 0` (paired page bootstrap). It was written after looking at GBIF's answers for
names on the dev pages, which are not blind; it is tested on the test pages only. Every other
linking number is descriptive.

**After the dev labelling (2026-11-19).** Gloria labelled the six dev pages (alone first, then
compared with an AI assistant) and decided the open cases; guide v0.6 and prompt `p4-guide-v0.6`
state them (Latin plurals of genus names, lower-case vernacular names, one span for a place
hierarchy, named regions, dated movements as events). The dev gold got three rows on her decision
(`gold/gold_changes_gloria.csv`). Two things learnt on dev are fixed in advance for the test set:
- *Value comparison* (`score.norm_value`) also folds the two ways of typing a hyphen (U+2010,
  U+2011 and `-`) and a quotation mark (curly and straight): the transcribers typed one, OCR
  engines write the other, and a reader sees the same character. Letters are never folded
  (`Achatinœ` in the transcription against `Achatinæ` in the modern OCR stays a mismatch).
- *Same occurrence rule for G1*: a quote that occurs several times in its cited line (a whole
  paragraph is one line in the modern OCR text) is placed like a G0 value, on the first
  whole-word occurrence not taken by a longer mention.
- *G0 alignment* (`locate.locate_all`): a G0 value has no position, so longer values are placed
  first and each value takes its first whole-word occurrence not already taken by another
  mention. Before this, `Jackdaw` could land inside `Jackdaws` and a person and a place both
  called `Lilford` on the same occurrence, which cost G0 one false positive plus one false
  negative each time with no extraction error. What stays ambiguous by nature (the same text in
  a heading and in a running head) is left so; it is a cost of having no evidence and is reported
  as such under RQ3.
- *Span boundaries.* On dev the same model, with the same prompt, wrote
  `Merida, Andes of Bolivia` as one mention in two of six runs and as two in four. At value level
  that one difference is one false negative plus two false positives. Value level stays the
  primary metric, and lenient level is always printed beside it, so that boundary conventions can
  be told apart from misses.
Dev scores are in `results/analysis_dev_p3/` and `results/analysis_dev_p4/` (tuning only, not
blind). With p4, value F1 of the primary fields on the expert text is 1.000 in all three repeats
for both books: the prompt and the guide were written from these six pages, so the dev set has
nothing left to tune on and says nothing about performance elsewhere. Only the test pages do.

**Guide rules found on test pages (from 2026-11-19).** Labelling a test page can show a gap in the
guide. The rule is added to the guide (v0.7 onwards) and the gold rows it decides are marked with that
version in the column `later_rule`, but the prompt stays `p4-guide-v0.6`: it was tuned on dev pages only, and no rule
that exists because of a test page is passed to a model. Every score is therefore reported twice:
with all gold rows, and with the rows whose `later_rule` is later than v0.6 treated as optional
(no credit, no penalty; this includes `excluded` rows, which record a decision that something is *not* a mention), so that "the model was never told this rule" can be told apart from "the
model got it wrong". So far the later rules have decided `vernacular` rows (v0.7: broad group names, material words, compounds; v0.8: nothing inside the title of a cited work is a mention), which are outside the
primary F1, and one `taxon` row (v0.10: a bare epithet sharing the preceding genus, `Darwinii`), which is inside it. Test labels are archived as received in `gold/received/` before any comparison or
adjudication; test-page gold is kept in `gold/gold_mentions_gloria_test.csv`.

**Errors in the reference transcription (2026-11-19).** The expert transcription is the reference
text, not the truth: on test page 8992489 it prints `Fringilla nontifringilla` where the scan has
`Fringilla montifringilla` (found by Gloria; the modern OCR reads it correctly). Gold offsets and
`text` always follow the transcription file. Where the labeller sees such a typo she records the
scan's reading in the gold column `scan_text`; at value level a prediction is correct if it
equals **either** reading, entity preservation counts an OCR text that equals the scan's reading
as preserved, and the linking step looks up the scan's reading. Known cases are listed in
`data/transcription_errata.csv` and their number is reported. Only typos the labeller noticed
are covered, so remaining transcription errors still count against a text version that reads the
page correctly; this biases value-level scores of the OCR versions slightly downwards.

**Scope decision (Gloria, 2026-11-18): "学名关联评分纳入，其余三项放 V2".** Taxon-link scoring
is in the frozen plan (above). Moved to V2 and **not** part of this pre-registration: the
controlled-perturbation experiment, the review-sheet CSV export, and the Level 3 image-region
demo. E1 therefore rests on natural OCR only (legacy, modern, expert, plus the Markdown
ablation) with entity-span CER and entity preservation; no claim about synthetic noise is made.

**Failed requests and RQ4 guards (built 2026-11-20).** A request can fail without the model being
wrong about the page: an API error, an answer that does not parse, a truncated answer. On dev,
Google's batch mode ignored the JSON schema and 3 of 48 answers were lost. Rules for the test run:
- Gemini runs in **sync mode with the schema enforced** (48 of 48 valid answers on dev); Opus
  runs in batch mode, where the schema is enforced.
- A failed request (`run_extraction.needs_retry`: an error, a truncated answer, or an answer that
  does not parse; a valid answer with no mentions is *not* a failure) is sent **once more** with
  identical settings, in sync mode, and the second answer is final. Both attempts are paid for and
  the first is kept inside the record (`attempts`, `first_attempt`); for test pages both stay in
  the sealed file. Batch runs do this when collected (`--collect`, unless `--no-retry`).
- A request that fails twice counts as "no predictions" in the main scores (the conservative
  reading); `outcomes.csv` gives each request's final outcome and its number of attempts, the
  failure rate is reported per model next to every score, and F1 on answered requests only is
  given beside it.
- RQ4: a page and text version for which the second model has no valid G1 answer is left out of
  the flagged-vs-unflagged comparison and of the risk-coverage curve, and counted
  (`excluded_no_answer_from_b`), so a missing answer is not read as disagreement.
- RQ4 verdicts need something to compare: with fewer than 10 unflagged predictions in a book and
  text version the verdict is "too few to compare" (`analysis.MIN_UNFLAGGED`). On dev every cell
  now reads so (0 or 1 unflagged prediction each), where the earlier code had written "supports"
  twice on a single unflagged mention.

**Still to run before the freeze commit**: nothing on dev. Everything in this document is built.
What remains is the gold set (one test page, the second labeller's five pages, adjudication, and
Butler's taxon links), then the freeze commit, then the test runs with Gloria's go-ahead.

## Deviations log

| Date | Change | Reason |
|---|---|---|
| | | |
