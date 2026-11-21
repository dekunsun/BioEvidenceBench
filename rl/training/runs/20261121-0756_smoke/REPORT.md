# Stage 2: GPU smoke test (Qwen3-0.6B, Secure RTX 4090)

*2026-11-21 07:56 UTC, 13.0 min, about $0.19. 2,000 training lines (half with a damaged name),
SFT 60 steps and GRPO 60 steps from the same base checkpoint, thinking off, Reward v1.3. A
throughput test: no checkpoint kept, no evaluation; the training curves below are observations on
training data only.*

## Throughput and cost

| | Seconds per step | Cost per 100 steps (at $0.89/h) | Peak GPU memory |
|---|---|---|---|
| SFT (16 lines per step) | 0.53 | $0.013 | 10.3 GB |
| GRPO (16 prompts × 8 answers per step, vLLM colocated at 0.3) | 5.81 | $0.144 | 20.3 GB of 24 |

Pod start-up and installing dependencies take about 5 minutes per launch (about $0.07). A GRPO run of
300 steps is about 29 minutes, about $0.43; SFT is almost free. The whole P0 design (2 SFT, 2 GRPO,
2 SFT→GRPO runs) is roughly $3–4 including set-up and evaluation, far inside the $13 primary budget,
so the Secure price is affordable and the Community price is not needed.

## What 60 GRPO steps from the base model did (training data)

| Step | Mean reward | Groups with all 8 rewards equal | Entropy | Answer length (tokens) |
|---|---|---|---|---|
| 5 | −0.05 | 59% | 0.13 | 28 |
| 20 | 0.14 | 83% | 0.07 | 25 |
| 40 | 0.30 | 90% | 0.02 | 20 |
| 60 | 0.24 | 93% | 0.02 | 20 |

Returning the OCR unchanged scores **0.307** on this sample (31% of its lines are clean). GRPO from
the base model climbed to about the copy score and the policy collapsed (entropy 0.13 → 0.02, 93%
of groups with no reward difference, shorter answers): it learned to stop running into the context
lines and to change little, not to repair. Copying is a safe local optimum under Reward v1.3: 0 on a
damaged line, 1 on a clean line, never negative. This is what the toy GRPO predicted (signal
vanishes as groups become uniform), here caused by a degenerate policy rather than by success.

SFT loss fell from 1.69 to about 0.64 in 60 steps.

## For stage 3 (Gloria's decision)

1. SFT → GRPO (condition D) is the condition likely to say something; GRPO from the base (C) is still
   worth running as the pre-registered comparison, and "C converges to copying" is a result.
2. The clean-line share of the training mix (31% here, plan about 20%) and the rollout temperature
   shape how attractive copying is; changing either is a dev-set decision to make before the runs.
3. `frac_reward_zero_std`, entropy and answer length are logged at every step; the copy baseline is
   part of every comparison.
