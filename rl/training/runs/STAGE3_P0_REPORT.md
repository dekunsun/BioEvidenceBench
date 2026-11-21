# Stage 3 (P0): Base, SFT, GRPO, SFT→GRPO on dev, two seeds

*2026-11-21 18:32 UTC, two Secure RTX 4090 pods in parallel (`20261121-1832_p0s1`, 87 min, about
$1.29; `20261121-1832_p0s2`, 74 min, about $1.09; RunPod balance 23.97 → 21.55, $2.42). Settings and
checkpoint rule: `configs/METRICS.md` section 9, fixed before the runs. Prompt `repair_v3`, thinking
off, Reward v1.3. **Dev only** (not blind; the dev sets chose the checkpoints): these are development
observations, not results. No test line was read. Chosen checkpoints (bf16) are assets of two draft
GitHub releases (`rl-ckpt-20261121-1832_p0s1`, `..._p0s2`), uploads checked by size.*

## Chosen checkpoints on dev

Evaluation decoding (T 0.7, top-p 0.8, top-k 20), 4 answers per line. Repair rate and preservation:
500 dev lines (100 per book), post-processed; name recovery: 85 further dev lines with a damaged name.

| Condition | Seed | Step chosen | Repair rate | Name recovery | Preservation | Format failures (raw) |
|---|---|---|---|---|---|---|
| Copy the OCR | – | – | 0.000 | 0.000 | 1.000 | 0% |
| A. Base (A′ post-processed is the same here) | – | – | 0.061 | 0.008 | 0.929 | 2.6–2.9% |
| B. SFT | 1 | 300 | 0.324 | 0.361 | 0.977 | 0.7% |
| B. SFT | 2 | 300 | 0.315 | 0.340 | 0.979 | 0.3% |
| C. GRPO | 1 | 300 | 0.012 | 0.000 | 0.998 | 0.3% |
| C. GRPO | 2 | 300 | 0.057 | 0.050* | 0.997 | 0.2% |
| D. SFT → GRPO | 1 | 100 | 0.305 | 0.342 | 0.989 | 0.1% |
| D. SFT → GRPO | 2 | 200 | 0.309 | 0.348 | 0.988 | 0.1% |

\* C seed 2: 0.050 is on the 500 dev lines' 20 name words; on the 85 name lines it is 0.000, as for seed 1.
Every chosen checkpoint passed the preservation floor (Base − 0.01 = 0.917–0.919); none was flagged.

Dev repair rate by step (post-processed):

| Step | 50 | 100 | 150 | 200 | 250 | 300 |
|---|---|---|---|---|---|---|
| SFT s1 / s2 | 0.19 / 0.17 | 0.22 / 0.24 | 0.26 / 0.27 | 0.30 / 0.30 | 0.32 / 0.31 | 0.32 / 0.31 |
| GRPO s1 / s2 | 0.00 / 0.03 | 0.00 / 0.03 | 0.00 / 0.05 | 0.00 / 0.04 | 0.01 / 0.05 | 0.01 / 0.06 |
| SFT→GRPO s1 / s2 | 0.29 / 0.29 | 0.31 / 0.29 | 0.30 / 0.31 | 0.30 / 0.31 | 0.30 / 0.30 | 0.30 / 0.31 |

## What training did (training data, every completion logged)

| | Seed | Answers copying the OCR, steps 0–49 → 250–299 | Groups with no reward difference | Entropy | Training reward |
|---|---|---|---|---|---|
| C. GRPO | 1 | 79% → 93% | 46% → 95% | 0.16 → 0.01 | 0.12 → 0.19 |
| C. GRPO | 2 | 74% → 85% | 55% → 90% | 0.15 → 0.03 | 0.14 → 0.21 |
| D. SFT → GRPO | 1 | 18% → 18% | 19% → 45% | 0.43 → 0.16 | 0.54 → 0.65 |
| D. SFT → GRPO | 2 | 17% → 17% | 24% → 43% | 0.38 → 0.17 | 0.55 → 0.64 |

Answer length stayed at 18–20 tokens. No out-of-memory retry was needed (16 per device, vLLM at 0.3).
Training times: SFT 3–4 min, each GRPO run 29–32 min.

## Reading (development, both seeds agree)

1. **GRPO from the base model learns to copy.** Measured directly now, not inferred: copying rises to
   85–93% of answers, groups without signal to 90–95%, entropy collapses; dev repair stays at or below
   Base (0.01–0.06 vs 0.06) while preservation rises to 0.998. Under Reward v1.3 copying is never
   negative and the base model's edits break more words than they fix, so "change nothing" is the
   higher-reward policy it can reach. This happened with float32 master weights as well, so the
   stage-2 observation was not a bf16 rounding effect.
2. **GRPO cannot reinforce what the policy never samples.** Half of every batch held a damaged name,
   yet C recovers no dev name; SFT reaches 0.34–0.36. Oversampling (7a) is necessary but not sufficient.
3. **SFT does the work; GRPO after SFT adds no repair on dev.** D's training reward rises 0.54 → 0.65,
   but dev repair stays at SFT's level (0.31 vs 0.32 / 0.31) and preservation rises by about one point
   (0.978 → 0.989). A rising training reward is not a better repair.
4. **SFT was still improving at step 300** (0.31 → 0.32 between steps 250 and 300 in both seeds), so
   B and D start from an SFT that may be under-trained. More SFT steps would cost about $0.013 per 100.

What these do not show: anything about test lines or Cuvier (stage 4), whether differences are
outside noise (paired page-block bootstrap is for the locked test), or why D's preservation gain
comes with no repair gain (7c: edit behaviour, error types, pass@k).
