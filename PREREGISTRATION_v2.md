# Pre-registration v2: confirming the exploratory findings on sealed pages

**Status: DRAFT for Gloria's review (2026-11-20). Not frozen. No sealed page has been labelled,
opened or run.** The first pre-registration (`PREREGISTRATION.md`) is frozen and is not changed;
this is a second, separate study. Once Gloria approves it, this file, the code and prompts it names
and the new gold are hashed into `FREEZE_v2.json` **before** any model is run on the pages below.
Anything decided afterwards goes in the deviations log at the bottom.

## 0. Why a second round

The first round's headline findings were pre-registered (OCR quality, LLM vs rules, the evidence
requirement, review flags, loss at linking). Several findings that now carry recommendations were
**exploratory**: designed after the test pages were unsealed (`DEVIATIONS.md`). Exploratory results
need a fresh test before they count as findings. This round re-tests the ones that change what we
recommend, on pages sealed before any of this analysis: `rl/sealed/pages.csv` (16 pages drawn on
2026-11-20, seed 20261120, sha256 `c4abd664ac2a…`; frame: Butler and Reeve pages outside the 22
first-round sample pages, at least 300 characters, not BHL `Index` pages).

## 1. What is scored

| Item | Value |
|---|---|
| Pages | **All 16 sealed pages (8 Butler, 8 Reeve)** (Gloria, 2026-11-20). An 8-page fallback was considered and rejected: with 4 pages per book most per-book intervals would span every threshold |
| Gold (entities) | New file `gold/gold_mentions_gloria_v2.csv`, labelled by Gloria alone on the expert text, delivered and archived unchanged in `gold/received/` before any comparison. Rules: ANNOTATION_GUIDE v0.10 **plus** the post-freeze rules in `GUIDE_ADDENDUM.md` as of 2026-11-20 (joint authorities are one person; a sub-unit and its parent institution are one span). Index pages are already out of the frame |
| Gold (links) | New file `gold/gold_links_gloria_v2_names.csv`, Butler pages only, the short procedure used in round 1 (one row per distinct name; Avibase first; accepted name, not a key); keys found by `src/expand_links.py`. Reeve linking stays deferred, as in round 1 |
| Second labeller | Optional: 2 pages labelled independently by a second person, agreement reported before scoring. Not required for any verdict |
| Text versions | `expert`, `legacy` (BHL per-page OCR), `modern_dots-mocr`, and for H1 every FineBooks OCR row whose outputs may be sent to an API (the 21 rows used in round 1's OCR ladder; Datalab rows only for the no-LLM preservation measure) |
| Extractors and settings | Frozen exactly as in the round-1 runs they confirm (section 3). Prompt `p4-guide-v0.6` for G0/G1; the exploratory G2 and V1 prompts as saved in `results/20261120-0039_explore_G2/prompts/` and `results/20261120-0039_explore_V1/prompts/`; the LLM linker prompt and schema as saved in `results/linking_variants/config.json` |
| Runs | One run per setting after the freeze; one retry for failed requests (as in round 1). Outputs on the v2 pages are sealed on arrival and opened only after `FREEZE_v2.json` exists and `src/freeze.py --verify` (v2) is clean. The sealing for exploratory-style runs (`run_exploratory.py`, `link_variants.py`) must be added before the run; this is listed in section 8 |

Results are reported per book and never pooled with round 1 for a verdict. A pooled round-1 + round-2
table may be shown as description only.

## 2. Matching and scoring (unchanged from round 1)

`src/score.py` and `src/locate.py` as frozen in `FREEZE.json`: value level is primary; spans
mapped to the expert text by character alignment; one-to-one matching per field; `ALL_PRIMARY` =
taxon, person, locality, institution, date; vernacular scored separately. The 2A audit
(`rl/verifier_audit/adversarial/REPORT.md`) found that G0/G1 values are not checked for quote
fidelity when the locator falls back to fuzzy matching; that never happened in round 1. Here the
number of `fuzzy`, `silent_correction` and `case_variant` statuses is reported for every run, and
the main result is also given with the patched fidelity gate as a sensitivity check.

Rows decided by a guide rule added after the prompt was fixed (later than v0.6) are marked in
`later_rule`; as in round 1, results are reported with all rows and with those rows optional.

## 3. Hypotheses, measures and decision rules

Thresholds are decision rules written in advance, not significance tests. Uncertainty: 95%
intervals from 1,000 bootstrap resamples **of pages within a book**. Verdicts: **supports** (the
interval clears the threshold in the stated direction), **against** (the interval lies on the
other side of the "against" bound), **inconclusive** (otherwise).

| # | Exploratory finding being confirmed (round 1) | Hypothesis on the v2 pages | Primary measure | Supports if | Against if |
|---|---|---|---|---|---|
| H1 | OCR ladder: name preservation predicted extraction (Spearman 0.95 / 1.00), page CER did not (−0.07 / −0.62) | Across OCR versions, gold-name preservation predicts Opus G1 value F1 better than page CER does | Per book: ρ_pres = Spearman(value F1, preservation) and ρ_cer = Spearman(value F1, −median page CER) over the OCR versions; Δ = ρ_pres − ρ_cer | ρ_pres ≥ 0.7 and the Δ interval > 0 | ρ_pres < 0.4, or the Δ interval < 0 |
| H2 | LLM linker raised Butler link recall from 0.59 to 0.91 (expert text) | On new Butler names, the LLM linker links more gold-resolved names correctly than the plain GBIF lookup | Butler, expert-text arm: link recall(LLM linker) − link recall(plain `species/match`), on gold-resolved names that Opus G1 extracted correctly | difference interval > 0.15 | difference interval < 0.05 |
| H3a | LLM repair of legacy OCR came close to modern OCR (G2 legacy 0.96 / 0.91 vs G1 dots.mocr 0.95 / 0.98) | Repairing legacy OCR is within 0.05 of extracting from modern OCR | Per book: value F1(G2 on legacy) − value F1(G1 on dots.mocr) | interval within ±0.05 | interval entirely below −0.10 |
| H3b | 92% of the values G2 changed were right | G2's repairs are mostly right | Per book: share of changed values (reading ≠ quote) that equal the gold value | lower bound ≥ 0.80 | upper bound < 0.70 |
| H3c | Image only reached 0.96 / 0.98 (value-bag scoring) | Reading the page image is within 0.05 of modern OCR | Per book: bag F1(V1) − bag F1(G1 on dots.mocr), both scored by `run_exploratory.bag_scores` | interval within ±0.05 | interval entirely below −0.10 |
| H4 | Haiku 5.5 within a few points of Opus 5.5 on dots.mocr (0.94 / 0.95 vs 0.95 / 0.98) | A model at about 1/15 of the cost extracts nearly as well | Per book: value F1(Haiku G1) − value F1(Opus G1), dots.mocr | interval within ±0.05 | interval entirely below −0.10 |
| H5 | (Replication of pre-registered RQ1) legacy → modern +0.34 on Reeve; modern → expert +0.005 | OCR is the first and largest loss; modern OCR removes most of it | Per book: F1(dots.mocr) − F1(legacy); F1(expert) − F1(dots.mocr), Opus G1 | first > 0.10 and second < 0.05 | first < 0.05 |

Model settings for each hypothesis, copied from the round-1 runs:

| Hypothesis | Round-1 run(s) whose settings are reused |
|---|---|
| H1, H5 | `20261120-ocrladder_claude-opus-5-5_test_G1`, `20261120-ocrladder2_…` and `20261119-2052_claude-opus-5-5_test_batch` (Opus 5.5, G1, batch, effort medium, max tokens 16,000). `20261120-ocrladder3_…` (Mistral OCR via OpenRouter) is not part of H1: the Mistral version is not reported, so it cannot be frozen |
| H2 | `results/linking_variants/` (Opus 5.5 linker, effort medium; GBIF `species/match` as in `src/link_taxa.py`) |
| H3a–c | `20261120-0039_explore_G2`, `20261120-0039_explore_V1` (Opus 5.5, sync, effort medium) |
| H4 | `20261120-0145_claude-haiku-5-5_test_sync` (Haiku 5.5, G1, sync; see `results/model_comparison/`) and the Opus run above |

## 4. Not re-tested here, and why

- **PCAS boundary rules (F1 0.83 → 0.94 after adjudication).** That change came from re-adjudicating
  the gold after seeing model outputs. A fair test needs new botany pages labelled under the
  addendum rules **before** any output is seen. Out of scope for this round; noted as next.
- **Review signals (55% of errors in 25% of output on legacy OCR).** Too few errors are expected on
  16 pages to say anything; not re-tested.
- **Memorisation probe, image boxes, whole-book spot-check.** Not recommendations; not re-tested.
- **Gemini.** Not needed for any hypothesis above; may be added only if decided before the freeze.

## 5. Exclusions and edge cases

As in round 1 (`PREREGISTRATION.md` section 6): `excluded` gold rows are not gold; `ambiguous` rows
are optional; text in `gold/annotation_issues_gloria_v2.csv` regions is set aside; a page×version
with no answer from a model is reported as missing, never as "found nothing". Empty but valid
answers are counted separately (2A finding 3).

## 6. Contamination and limits to state with the results

- Same two books as round 1, both public; pre-training exposure cannot be ruled out. The
  round-1 memorisation probe found no sign of page memory in repair; it is not repeated here.
- 8 (or 4) pages per book: wide intervals; book and OCR quality remain confounded.
- Labelled by one person who has seen round-1 outputs on other pages of the same books and knows
  the hypotheses. The sealed pages themselves have not been seen. This is weaker than a labeller
  blind to the hypotheses; a second labeller on 2 pages is the only check.
- The prompt (`p4-guide-v0.6`) is older than the guide used for the gold; reported both ways (section 2).
- Task B in `rl/` splits by 10-page blocks, so neighbours of these pages may be in task B's
  training blocks. No model trained on task B is used here.

## 7. Order of work

1. Gloria reviews this draft. Decided: 16 pages. Still open: second labeller yes or no (default no); Gemini yes or no (default no).
2. Gloria labels the entity gold (and Butler links) alone; files archived unchanged and committed.
3. Code needed for sealed exploratory runs is added and tested on a dev page (section 8).
4. `FREEZE_v2.json`: this file, the gold, code commit, prompt hashes. Commit at once.
5. All runs (sealed on arrival). 6. Unseal after `--verify`; score; report as round 2.

## 8. Code to add before the freeze (no model calls)

- A v2 split file (`data/sample_split_v2.csv`) listing the sealed pages, so existing scripts can
  select them and the scorer can load the v2 gold.
- Sealing on arrival for `run_exploratory.py` and `link_variants.py` runs on v2 pages (today only
  `run_extraction.py` seals test outputs).
- `src/freeze.py` support for a second freeze file, or a small `freeze_v2` wrapper.
- An analysis script that computes H1–H5 with the decision rules above and writes
  `results/analysis_v2/REPORT.md`.

## 9. Budget

| Item | Estimate |
|---|---|
| Gloria: entity labels, 16 pages | about 8–16 hours (first-round pages ranged from 2 to 78 mentions); 8 pages about 4–8 hours |
| Gloria: Butler links | about 1–1.5 hours (≈3 minutes per name) |
| API (Opus G1 on ~23 text versions, G2, V1, Haiku, linker) | under $10, mostly batch |

## Deviations log

| Date | What changed | Why | Decided by |
|---|---|---|---|
| 2026-11-20 (draft) | Pages: all 16 sealed pages, not 8. Mistral OCR stays out of H1 (version not reported by OpenRouter; not needed for any hypothesis) | Gloria |
