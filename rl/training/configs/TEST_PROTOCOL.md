# Module 7b: locked test protocol (stage 4)

*Written 2026-11-21 after the stage-3 dev runs and before any test line was scored (Gloria: "跑4").
Frozen by the commit that adds `stage4_models.json` (after the SFT-600 re-run); nothing below changes after a
test result is seen. Deviations, if any, go to `rl/LOG.md` marked as such. Design: `METRICS.md`.*

## 1. Test sets (`TEST_SETS.md`, drawn once by `make_test_p0.py`, seed 20261122)

| Set | Lines | Source | Use |
|---|---|---|---|
| `p0_test_inbook` | 500 (100 per training book; 93 pages, 12 split-v2 blocks) | split v2 `intest`, leaving out the 17 usable lines (of 22) that the alignment audits displayed | primary |
| `p0_test_cuvier` | 500 (319 pages) | Cuvier, *Histoire naturelle des poissons* t. 10, 1835, French; built by `src/rl_task_b_build_cuvier.py` with the automatic in-book rules (no manual exclusions or scan-checked typos: nobody has read the book) | held-out book and language |
| `p0_test_inbook_rest` | 3,226 | every other usable in-book test line | larger confirmation (P1): Base, B and the GRPO condition chosen on dev |

Cuvier has 75% clean lines and 7 lines with a damaged name in its 500, so its name recovery is
descriptive only.

## 2. Models (fixed before the run, `stage4_models.json`)

Copy (the OCR), A = Base `Qwen/Qwen3-0.6B`, A′ = Base post-processed, and the dev-chosen checkpoints
of stage 3: B = SFT 600 steps (re-run `sft600s1/2`), C = GRPO from base (`p0s1/2`), D = SFT→GRPO from
the 600-step B (`sft600s1/2`), seeds 1 and 2. **GRPO condition for the larger confirmation**: the one
of C and D with the higher mean dev repair rate (post-processed) over its two seeds.

**P1 (Gloria, 2026-11-21, decided before any test result): reward ablation only.** C-CER = GRPO from
base with R-A = 1 − CER as the reward (no gates; everything else as C), seed 1 (`p1cer`), chosen on
dev with the same rule, tested on `p0_test_inbook` and `p0_test_cuvier`, compared with C seed 1 and
with A. The data ablation (no name oversampling) and the name-weight ablation (P2) are **dropped**:
C learns no names even with oversampling and weight 3 (dev, both seeds), so removing either cannot
show a difference. Question C-CER answers: is GRPO's collapse to copying caused by the shape of
Reward v1.3 (copying a damaged line scores 0, a broken word −0.5), or by a start model that rarely
samples a correct repair?

## 3. Decoding and scoring

Prompt `repair_v3`, thinking off, one renderer (`common_7b.render_prompt`). Evaluation decoding
T 0.7, top-p 0.8, top-k 20, min-p 0, max 128 tokens, seed 20261121, **8 answers per line**:
pass@1 metrics use answers 0–3 (METRICS.md 2a: 4 samples), pass@8 uses all 8, for every model.
Reward v1.3 and the fixed clean-up (`format_cleanup`). Primary metrics (METRICS.md 3), raw and
post-processed, pooled over lines (`analyze_test_7b.py`):

1. damaged-word repair rate; 2. scientific-name exact recovery; 3. correct-word preservation;
4. format failure rate (format, integrity or alignment gate), and its complement the format-valid rate.

Reported separately for in-book and Cuvier; per book as description only.

## 4. Comparisons and decisions (METRICS.md 4–5)

Paired Δ on the same lines, 95% interval from 2,000 bootstrap resamples of split-v2 blocks
(in-book; Cuvier: pages), seed 20261122. Each seed's Δ is shown; a claim needs every seed's interval
on the same side of 0. With 12 in-book blocks the intervals are coarse; a page-level bootstrap is
reported next to it as a sensitivity check, never as the decision.

| Question | Comparison | Rule |
|---|---|---|
| GRPO improves the delivered repair | C − A, raw repair rate | lower bound > 0 in both seeds, and preservation not inferior |
| … content, not only format | C − A′, post-processed repair rate | lower bound > 0 in both seeds; otherwise a raw-only gain is a format gain |
| SFT → GRPO adds to SFT | D − B, raw and post-processed | as above |
| Preservation (non-inferiority, margin 1 point) | Δ preservation | pass if lower bound > −0.01; fail if upper bound < −0.01; else inconclusive |
| Names without harm to ordinary words | Δ name recovery > 0 and preservation passes | |
| Descriptive | B − A, D − A | |
| P1: does a dense reward escape copying? | C-CER − C (seed 1), C-CER − A | descriptive (one seed) |

Diagnostics, not success criteria: mean Reward v1.3, pass@1 / pass@8 (7c), CER, case accuracy.

## 5. Reward reliability (METRICS.md 3, 5)

Candidates: answers with reward ≥ 0.75 that fail a check independent of the reward: further from the
expert line than the OCR by edit distance, a damaged line copied unchanged, or run-on into the context.
Claude lists them (`hacking_candidates.csv`); Gloria confirms a sample of at least 20 (all if fewer).
Confirmed rate above 2% in any condition: the verifier is not reliable for that condition.

## 6. What this protocol does not allow

No checkpoint, model, setting, prompt or reward is changed or chosen after a test result. Cuvier is
scored once. P1 ablations, if Gloria runs them, are trained and chosen on dev like P0 and tested with
these same sets and rules.
