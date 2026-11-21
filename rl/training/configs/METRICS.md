# Module 7b: metrics and comparisons fixed before training

*Drafted by Claude 2026-11-21 from `rl/PLAN_zh.md` 7b–7c and the step 4–5 results; Gloria's
decisions of 2026-11-21 are in (marked "Gloria"). Not changed before the test evaluation; any
later change goes in `rl/LOG.md` with the reason. GPU budget: $20 hard cap in total, RunPod only.*

## 1. Data

| Use | Data | Notes |
|---|---|---|
| Training | `train.jsonl` (31,909 lines, split v2) | lines with a damaged name oversampled to half of each batch in the main runs (toy GRPO: names are not learned otherwise); a run without oversampling kept as a **secondary ablation** (Gloria) |
| Choosing checkpoints, settings | `dev.jsonl` (3,784) | the 5 pilot pages and the 200 trial items included; dev is not blind |
| Reported, in-book | fixed 500-line subset of `intest.jsonl`, drawn once with a seed, stratified by book | never read before the final evaluation |
| Reported, held-out book | fixed 500 lines of Cuvier (French, 1830s?), built with the same rules | Cuvier has not been read at all yet: building its units is the first time; **cross-book and cross-language**, not only cross-book |
| Never used | the 16 sealed pages, the 22 BioEvidenceBench sample pages | |

Suspected reference typos stay set aside until Gloria's check (`reference_errata.csv`).

## 2. Conditions (same base model, same data split)

| Condition | What it is |
|---|---|
| Copy | return the OCR unchanged (no model) |
| A. Base | Qwen3-0.6B, the instruct model (Gloria), with the task prompt, no training; thinking mode off |
| A′. Base + format clean-up | A's outputs passed through a fixed, deterministic clean-up (keep the first non-empty line; strip a commentary prefix and wrapping quotes or Markdown). No GPU: re-scores A's outputs |
| B. SFT | supervised on (OCR → expert line) pairs |
| C. GRPO | Reward v1.2 only |
| D. SFT → GRPO | B, then C's training |
| Ablation (reward) | C with R-A = 1 − CER as the reward (2 seeds) |
| Secondary ablation (data) | C without oversampling name lines (1 seed; Gloria) |
| Secondary ablation (name weight), if the budget allows after the runs above | C with name weight w = 1 instead of 3 (1 seed) |

Seeds: 3 for C and D, 2 for the ablation, 2 for B. Same number of training steps for C and D's
GRPO phase (about 300–500, fixed after the pilot, before the final runs).

## 3. Primary metrics (reported per book and pooled, in-book and Cuvier separately)

1. **Damaged-word repair rate**: share of damaged reference words written exactly (unweighted;
   `exact_repair_rate`).
2. **Scientific-name exact recovery**: share of damaged name words (gnfinder candidates) written exactly.
3. **Correct-word preservation**: share of words the OCR had right that the output keeps.
4. **Format and integrity failure rate**.
5. **Reward-hacking rate**: share of outputs that score well but fail a check from `REWARD_AUDIT.md`
   (commentary, wrapping, insertions, modernised spelling, deleted hard words).

**Format, separated from content.** Every primary metric is also reported on format-valid outputs
only, and each condition's gain over Base is split into (a) outputs that went from format-invalid
to valid and (b) better repairs among outputs that were already valid. A′ shows how much of the gap a
fixed clean-up closes without any training.

Diagnostics, not success criteria: mean reward (Reward v1.2), CER, case accuracy, `reward_reading`
(ſ ≡ s), recoverable-deletion repair rate.

**The training reward is never the measure of success.** A condition counts as better only on the
primary metrics, on lines not used for training or tuning.

## 4. Uncertainty

95% intervals by bootstrap over page blocks (split v2 blocks), 2,000 resamples, per book. A difference
counts as consistent only if every seed points the same way; seed spread is shown.

## 5. Decision rules (written before the runs)

- **GRPO helps** if C beats Base **and A′** on metric 1 in every seed, with intervals not
  overlapping, and metric 3 does not fall by more than **1 percentage point** (Gloria; provisional).
- **The gain is more than format** only if C also beats A′ on metric 1 among format-valid outputs.
- **SFT → GRPO beats SFT** on the same terms.
- **Reward hacking** (Gloria): metric 5 above **2%** of outputs in any condition is the warning and
  failure threshold. A **severe loophole** is handled on its own, whatever its share: an output type
  that earns more reward than the correct answer, or one exploit repeated systematically. Training
  stops, the reward is fixed with a new REWARD_DESIGN version and a test, and the runs are redone;
  nothing is patched silently.
- **Names improved without hurting ordinary words**: metric 2 up, metric 3 within the threshold above.

## 5a. What each comparison can attribute (and what it cannot)

| Question | Comparison | Limit |
|---|---|---|
| Did GRPO improve repair? | C vs Base, A′, Copy; D vs B | one 0.6B model; five training books; Cuvier tests one further book and language |
| Was it only format? | gain split (format-invalid → valid vs better repairs); C vs A′ on format-valid outputs | the clean-up rule is one fixed rule, not the best possible |
| Reward design? | C (Reward v1.2) vs ablation R-A (1 − CER), 2 seeds each; name weight w = 1, 1 seed if run | 2 seeds give a direction, not a firm result; R-A vs R-D changes several things at once (word unit, weights, penalties) |
| Training data selection? | C vs C without name oversampling, 1 seed | 1 seed: a lead only |
| Learned, or more stable? | pass@k before vs pass@1 after (7c) | Yue et al. 2025 show RL can mostly re-rank what the base model can already sample |
- A null result is reported as a result (plan 7b).

## 6. Attribution (7c), fixed now

pass@k before training (k = 1, 8) vs pass@1 after; error types (name letters, ordinary words,
ligatures, long s, numbers, punctuation, word splits); edit behaviour (edit rate, edit precision,
edit recall); difficulty before training (0%, 10–90%, 100% pass); Gloria reads about 50 lines
(training-before-wrong / after-right, and the reverse).

## 7. Logged during training

reward mean and std, `frac_reward_zero_std`, KL, completion length, the reward's diagnostic fields,
GPU hours and cost per run.
