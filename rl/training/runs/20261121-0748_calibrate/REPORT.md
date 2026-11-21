# Stage 1: small-model calibration (Qwen3-0.6B, thinking off)

*2026-11-21 07:48 UTC, Secure RTX 4090, 5.7 min, about $0.085. 184 dev items (the step-5 API trial's
lines under current data rules), K = 8 answers, prompt `repair_v2`, Reward v1.3. Fourth launch; the
first three failed on environment set-up (`rl/LOG.md`).*

| | Rollout setting (T 1.0) | Model card setting (T 0.7, top-p 0.8, top-k 20) |
|---|---|---|
| Items whose 8 rewards are not all equal | **57.1%** (gate ≥ 20%: passed) | 17.9% |
| Mean reward, raw / post-processed | −0.065 / −0.074 | −0.018 / −0.020 |
| Pass rate (reward 1.0), raw | 3.8% | 5.0% |
| Format failures | 2.5% (35 several lines, 2 commentary) | 1.4% |
| `<think>` in answers | 0% | 0% |
| Truncated at 128 tokens | 0.5% | 0.3% |
| Generation time, 1,472 answers | 118 s (first call includes vLLM start-up) | 3 s |

**What the untrained model does** (share of answers, rollout / card setting):

| Behaviour | T 1.0 | card |
|---|---|---|
| Runs on into the context lines (answer > 1.5 × the line: integrity gate, reward 0) | 39% | 40% |
| Copies the OCR unchanged | 19% | 29% |
| Edits the line | 38% | 30% |
| Format failure | 3% | 1% |

Edited answers score −0.24 / −0.20 on average: the model breaks more correct words than it repairs
(2–5 damaged-word lines: 0.05 words repaired, 0.44 broken per answer; clean lines: about 1 word
broken per answer, 24% kept intact).

**Reading.**
- Thinking mode is off in practice (0 `<think>`), and format is rarely the problem (1–3%), so the
  post-processed metrics barely differ from the raw ones: A′ (Base + clean-up) will not close the gap.
- The main failure is not knowing which line to repair: 40% of answers include the context lines.
  That is what SFT should fix first, and it is a prompt-design lead (context marked more clearly).
- The 57% "signal" at T 1.0 is real variance in reward, but much of it comes from answers that differ
  in how badly they break the line, not in how well they repair it: a weak signal for learning repair.
  It argues for SFT → GRPO (condition D) over GRPO from Base (C). This is a reading of one run, not a
  result.
- Compared with the API trial on the same lines (Opus 5.5 pass rate 59%, Haiku 5.5 40%), the 0.6B
  model starts near zero: ample room, and a reason to report Copy as a baseline it may not beat.
