# Module 7b: metrics, comparisons and gates fixed before training

*Drafted by Claude 2026-11-21 from `rl/PLAN_zh.md` 7b–7c and the step 4–5 results. Gloria's decisions
of 2026-11-21 are in (marked "Gloria"), and so is an external review she passed on the same day
(marked "review"). GPU budget: $20 hard cap in total, RunPod only.*

**What is frozen and when.** Development choices (training steps, learning rate, rollout
temperature, checkpoint) are made on dev and logged in `rl/LOG.md`. The **test protocol** below
(test lines, metrics, decoding, decision rules) is frozen before any test line is scored, and no
checkpoint, setting or reward is chosen after seeing a test result. Cuvier is scored once, last.

## 0. The questions

1. Does GRPO improve OCR repair as measured independently of its training reward?
2. Is the gain more than learning the output format?
3. Does it come from the reward design, from the training-data selection, or neither clearly?
4. Does what SFT already teaches leave room for GRPO (D vs B)?
5. Do gains on scientific names cost ordinary words?
6. Do gains made on five books hold on an unseen book and language (Cuvier)?

A null result on any of these is reported as a result.

## 1. Data

| Use | Data | Notes |
|---|---|---|
| Training | `train.jsonl` (31,909 lines, split v2) | **B, C and D use the same line distribution**: lines with a damaged name oversampled to half of each batch (toy GRPO: names are not learned otherwise) |
| Development | `dev.jsonl` (3,784) | choosing steps, settings, checkpoints; the 5 pilot pages and 200 trial items included; not blind |
| Locked test, in-book | 500 lines of `intest.jsonl`, drawn once with a seed, stratified by book, **excluding the 22 in-book test lines (11 pages) that the alignment audits displayed** | the audits read those lines while checking pairing; recorded here, left out of the test subset |
| Locked test, held-out book | 500 lines of Cuvier, built with the same rules when the test protocol is frozen | no Cuvier text has been read; **cross-book and cross-language** |
| Larger confirmation (P1) | all remaining in-book test lines (about 3,700) | only Base, SFT and the dev-chosen best GRPO condition |
| Never used | the 16 sealed pages, the 22 BioEvidenceBench sample pages | |

Suspected reference typos stay set aside until Gloria's check (`reference_errata.csv`). With about
100 lines per book and few damaged-name lines per book, per-book results are descriptive; claims
rest on the pooled paired comparisons below.

## 2. Conditions and priorities (review)

| Priority | Condition | Seeds | What it is |
|---|---|---|---|
| P0 | Copy | – | the OCR unchanged (no model) |
| P0 | A. Base | – | `Qwen/Qwen3-0.6B`, the post-trained instruct model (Gloria), task prompt, no training |
| P0 | A′. Base + format clean-up | – | A's outputs through the fixed clean-up of section 3 (the same clean-up is applied to every condition for the post-processed metrics); no GPU |
| P0 | B. SFT | 2 | supervised on (OCR → expert line) |
| P0 | C. GRPO | 2 | Reward v1.3 |
| P0 | D. SFT → GRPO | 2 | B, then C's training |
| P1 | Ablation: reward | 1 | C with R-A = 1 − CER as the reward |
| P1 | Ablation: data | 1 | C without name oversampling, **same reward and every other setting** (Gloria: secondary) |
| P2 | Ablation: name weight | 1 | C with name weight w = 1 |
| P2 | Third seed for B, C, D | +1 each | only if the budget allows after P0 and P1 |

The name weight (×3 in the reward) and the name oversampling (50% of batches) both raise the
weight of names. The main runs use both; the two ablations take one away at a time, so a name gain
can be traced to one or the other only as far as their single seeds allow.

**Compute is recorded, not assumed equal.** Every run logs input and output tokens processed,
rollouts generated, optimizer steps, GPU hours and cost. SFT and GRPO are compared at their logged
budgets; equal steps are not called equal compute.

## 2a. Prompts and decoding (thinking mode off everywhere)

- **Prompt version `repair_v3`** (dev decision, Gloria, 2026-11-21, before P0): context lines first, the line
  to repair last inside `<line>…</line>`, stop where the marked line ends. Chosen over `repair_v2` on the
  184 stage-1 dev items (run-on 41% → 2%, pass rate 4% → 15% at T 1.0, items with signal 56% → 54%;
  `rl/training/runs/20261121-1756_promptcmp/REPORT.md`). Used by every condition; never changed on the
  locked test set.
- **One prompt renderer for every stage**: `tokenizer.apply_chat_template(..., add_generation_prompt=True,
  enable_thinking=False)`, rendered once and passed on as plain strings to SFT, GRPO and evaluation
  (TRL's `GRPOConfig` has `chat_template_kwargs`, `SFTConfig` has no such option, so trainer-side
  rendering could differ). SFT targets are that prompt + the expert line + the end-of-turn token.
  Same checkpoint, tokenizer and prompt for every condition.
- **Checked, not assumed**: each run saves one rendered prompt verbatim and its SHA-256. Checked on
  CPU with the model's tokenizer (2026-11-21): with `enable_thinking=False` the template ends the
  prompt with `<|im_start|>assistant\n<think>\n\n</think>\n\n`, an empty thinking block inside the
  prompt, not in the answer; the default (thinking on) ends at `<|im_start|>assistant\n`. A rendered
  prompt is about 260 tokens. Stage 1 checks that Base answers contain no `<think>`.
- **Gated in the reward**: Reward v1.3 scores any `<think>` / `</think>` tag as a format error;
  the share is logged at every step and evaluation.
- `max_completion_length` 128 tokens; truncated answers counted.
- **Evaluation decoding**, fixed for every condition: the model card's non-thinking settings
  (temperature 0.7, top-p 0.8, top-k 20, min-p 0), pass@1 averaged over 4 samples per line.
  **Rollout decoding**: temperature 1.0, no top-p / top-k; stage 1 may change only the rollout
  temperature, on dev.

## 3. Metrics (in-book and Cuvier separately; pooled, and per book as description)

Primary:
1. **Damaged-word repair rate**: share of damaged reference words written exactly (unweighted).
2. **Scientific-name exact recovery**: share of damaged name words written exactly.
3. **Correct-word preservation**: share of words the OCR had right that the output keeps.
4. **Format failure rate**: answers scored 0 by the format, integrity or alignment gates.

Three kinds of failure are kept apart (review):

| Kind | What it is | Example |
|---|---|---|
| Format failure | the gates score the answer 0 | several lines, commentary, `<think>`, wrapping |
| Repair failure | a valid answer that does not repair damage or breaks correct words | `parua` left as is |
| Reward exploitation | an answer with **high reward** (≥ 0.75) that **violates a task requirement checked independently of the reward** | a hard word deleted yet scored as repaired by an alignment flaw |

**Reward-hacking rate** = answers confirmed as reward exploitation ÷ all evaluated answers.
Candidates are found by the `REWARD_AUDIT.md` checks and by reading; each candidate is confirmed by
hand (Claude lists, Gloria confirms a sample of at least 20 or all if fewer). Also reported: the
**high-reward violation rate** = confirmed violations ÷ answers with reward ≥ 0.75.

**Raw, format-valid and post-processed metrics (Gloria).** Every condition's answers are scored
three ways, on the same test lines and the same decoding:

| Metric | Answers scored | Question |
|---|---|---|
| Raw repair rate (and the other primary metrics) | as generated | how much repair the model's actual output delivers |
| Format-valid rate | as generated | whether the model follows the output format |
| **Post-processed** repair rate (and the others) | after the fixed clean-up | whether content improved once removable format differences are gone |

The clean-up (`format_cleanup` in `src/rl_task_b.py`, with tests) is applied identically to every
condition and never reads the reference: drop `<think>…</think>` blocks, keep the first non-empty
line, drop a commentary prefix, drop one pair of wrapping quotes, backticks or Markdown asterisks.
It only cuts: the code checks that the result is a contiguous piece of the answer, so it never
infers, adds or rewrites content. Content comparisons rest on the post-processed metrics.

Metrics on format-valid answers only are a **diagnostic, not evidence**: conditions differ in which
lines they answer validly (a weak model may be valid mostly on easy lines), so these subsets select
different populations. Likewise, splitting a gain into "format" and "content" parts is
**descriptive**: two models' answers are not the same answer before and after training, so the
split is not a causal attribution.

Diagnostics, not success criteria: mean training reward (Reward v1.3), CER, case accuracy,
`reward_reading` (ſ ≡ s), recoverable-deletion repair rate. **The training reward is never the
measure of success.**

## 4. Uncertainty (review)

Comparisons are **paired**: the same test lines for both conditions, Δ = metric(X) − metric(Y),
with a 95% interval from a bootstrap over page blocks (split v2 blocks), 2,000 resamples. Two
conditions' separate intervals are not compared for overlap. Seeds: each seed's Δ is shown; a
claim needs every seed's interval on the same side. The precision limit is the number of
independent test pages, not the number of resamples.

## 5. Decision rules

- **GRPO improves the delivered repair** if Δ(C − Base) on the raw repair rate has an interval above
  0 in every seed, and preservation passes the non-inferiority rule below.
- **GRPO improves content, not only format**, if Δ(C − Base) on the **post-processed** repair rate
  (Base post-processed = A′) has an interval above 0 in every seed. If only the raw difference is
  above 0, the result is reported as a format gain.
- **SFT → GRPO adds to SFT** on the same two terms, with D and B (both post-processed for content).
- **Preservation, non-inferiority** (Gloria: margin 1 point, provisional; review: as a
  non-inferiority margin): passes if the lower bound of Δ preservation is above −0.01; fails if the
  upper bound is below −0.01; otherwise **inconclusive** (never a pass by default).
- **Names without harm to ordinary words**: Δ metric 2 above 0 and preservation passes.
- **Reward reliability** (Gloria; review): a confirmed reward-hacking rate above **2%** in any
  condition means the verifier is not reliable for that condition. A **severe loophole** is handled
  on its own, whatever its share: an output type that earns more reward than the correct answer, or
  one exploit that reproduces. Training stops, the reward is fixed with a new REWARD_DESIGN version
  and a test, and affected runs are redone; a low rate never certifies a verifier as safe.

## 6. Stages and budget gates (review)

| Stage | What | Budget | Gate to continue |
|---|---|---|---|
| 1. Small-model calibration | Qwen3-0.6B, thinking off, K = 8 on 200 train/dev lines: template check, format failures, `<think>` share, `frac_reward_zero_std`, error kinds | within stage 2 | at least 20% of items with unequal rewards at the rollout temperature (provisional); otherwise change item difficulty or temperature on dev first, not more steps |
| 2. GPU smoke test | 50–100 GRPO steps and a short SFT: seconds per step, memory, tokens, cost per 100 steps | **$2** | decide how many P0 / P1 runs fit, before running them |
| 3. Primary comparison | P0 runs; checkpoints chosen on dev | **$13** | stop and re-plan if the measured cost would exceed this |
| 4. Ablations and final evaluation | P1 (P2 if room), locked tests once, larger confirmation | **$3** | |
| Reserve | debugging, storage | **$2** | |

Stage caps are budgets, not forecasts; going over one stops the work for a re-plan with Gloria,
no automatic extra runs. Prices: RunPod RTX 4090 Community $0.34/h, Secure $0.89/h (review, from
RunPod's page); community capacity is not guaranteed.

## 7. Attribution (7c), fixed now

pass@1 and pass@8 before and after training, with the same sampling settings (Gloria): if pass@1
rises after training but pass@8 before training already found the same right answers, training may
mainly have made existing answers more likely (Yue et al. 2025). This is an interpretation, not a
proof; error types (name letters, ordinary words, ligatures, long s,
numbers, punctuation, word splits); edit behaviour (edit rate, edit precision, edit recall);
difficulty before training (0%, 10–90%, 100% pass); Gloria reads about 50 lines (wrong before /
right after, and the reverse).

## 8. Logged during training

reward mean and std, `frac_reward_zero_std`, KL, completion length, `<think>` and truncation
shares, the reward's diagnostic fields, tokens, rollouts, optimizer steps, GPU hours and cost.

## 9. Stage 3 settings (development choices, fixed before the P0 runs, 2026-11-21)

Gloria: "用 v3，先重建训练数据，再跑阶段 3". Code `rl/training/stage3_p0.py`, data `rl/training/make_data_p0.py`
(`rl/training/data/P0_DATA.md`).

- **Training mix**: 4,800 lines = 300 steps × 16, every block of 16 = 8 damaged-name lines, 3 clean
  (19%), 5 other damaged; the 1,280 distinct name lines appear once or twice. B, C and D use this file.
- **Steps**: SFT 300 (one pass, 16 lines per step, lr 1e-5); GRPO 300 (16 prompts × 8 answers, lr 1e-6,
  the stage-2 settings, rollout T 1.0). Master weights float32 with bf16 autocast: pure bf16 weights
  would round away most updates at these learning rates (stages 1–2 used bf16 weights).
- **Seeds**: training seed and a seed-specific order of the 16-line blocks (GRPO reads blocks in order
  so the mix holds at every step; TRL gives vLLM the same sampling seed in every run, so without a
  different order two seeds would be nearly the same run).
- **Checkpoints**: every 50 steps; each answers 500 dev lines (100 per book) and 85 further dev
  name lines with the evaluation decoding, 4 answers per line. **Rule**: highest post-processed
  repair rate on the 500 dev lines among checkpoints whose post-processed preservation is at least
  Base's minus 0.01; ties to the earlier step; if none qualifies, the highest preservation (flagged).
  D starts from B's chosen checkpoint of the same seed.
- **Storage**: chosen checkpoints in bf16 as assets of a draft GitHub release (too large for git);
  the pod checks it can upload before training. Every GRPO completion is logged with step and reward.
- No test line is read in stage 3. The locked test protocol (500 in-book lines, 500 Cuvier lines)
  is frozen before stage 4.
- **Revision before the locked test (Gloria, 2026-11-21, "加到600步")**: SFT 600 steps (two passes), because
  dev repair was still rising at step 300 in both seeds; B and D re-run, C kept. Same checkpoint rule.
- **P1 decided before the locked test (Gloria, 2026-11-21, "按你的建议")**: only the reward ablation
  (C with R-A = 1 − CER, seed 1). The data and name-weight ablations are dropped: C learns no names with
  oversampling and weight 3, so taking either away cannot show a difference (TEST_PROTOCOL.md section 2).
