# Prompt revision on dev: repair_v2 vs repair_v3 (Qwen3-0.6B, thinking off)

*2026-11-21 17:56 UTC, Secure RTX 4090, 4.82 min, about $0.071. A logged development-stage revision
approved by Gloria before P0 started ("可以，做 v3 对比，跑吧"). Same 184 dev items as stage 1, same
seed, K = 8 answers per item, Reward v1.3, both prompts in one run. No test line was read.*

Files in this folder: `prompt_repair_v2.txt`, `prompt_repair_v3.txt` (the full prompts), `config.json`
(model, decoding, seed, item-file and prompt-file SHA-256, one rendered prompt per version),
`answers.jsonl` (all 2,944 answers with their scores, `run_on` and `has_line_tag`), `summary.json`.

## Why a revision

Stage 1 found 40% of answers running on into the context lines; 70% of those appended the NEXT line.
Gloria asked whether the input boundary was ambiguous. No input contains a newline; the cause is the
layout of v2, which put the next line last, right before the answer, while sentences flow across
lines. v3 changes only the layout and the boundary instruction: context lines first, labelled "do not
repair or copy", then the line to repair last inside `<line>…</line>`, and "stop where the marked line
ends; never copy text from the context lines". Task, reward and data are unchanged.

## Results

| | v2, T 1.0 | v3, T 1.0 | v2, card | v3, card |
|---|---|---|---|---|
| Runs on into context (answer > 1.5 × line) | 41.6% | **1.7%** | 40.8% | **1.6%** |
| Format failures | 2.5% | 0.6% | 1.4% | 0.0% |
| `<line>` tag leaked into answer | 0% | 0% | 0% | 0% |
| Mean reward, raw | −0.064 | **+0.096** | −0.019 | **+0.162** |
| Pass rate (reward 1.0) | 3.9% | 15.4% | 5.0% | 18.2% |
| pass@8 (any of 8 answers reward 1.0) | 8.2% | 20.7% | 7.1% | 20.1% |
| Items whose 8 rewards are not all equal | 56.5% | 54.3% | 18.5% | 18.5% |

T 1.0 = rollout setting; card = model-card non-thinking setting (T 0.7, top-p 0.8, top-k 20),
the evaluation decoding.

**Behaviour** (share of answers):

| | v2, T 1.0 | v3, T 1.0 | v2, card | v3, card |
|---|---|---|---|---|
| Run-on | 39% | 2% | 40% | 2% |
| Copies the OCR unchanged | 19% | 34% | 29% | 43% |
| Edits the line | 39% | 64% | 31% | 55% |
| Format failure | 3% | 1% | 1% | 0% |
| Mean reward of edited answers | −0.23 | +0.01 | −0.20 | +0.10 |
| Words repaired / broken per edited answer | 0.14 / 1.76 | 0.30 / 0.60 | 0.15 / 1.85 | 0.36 / 0.44 |

By line class (T 1.0): on clean lines (36 items) the pass rate rises from 19% to 65% (v3 mostly
leaves them intact); on lines with 2–5 damaged words (147 items) pass rate 0.2% → 3.3% and repaired
words per answer 0.07 → 0.24.

## Choice: repair_v3

1. It removes the confound Gloria flagged: run-on drops from about 41% to under 2%, so later
   differences between Base, SFT and GRPO are about repair, not about where the line ends.
2. Edited answers stop breaking more words than they repair (1.76 → 0.60 broken per answer).
3. The GRPO learning signal is unchanged (56.5% → 54.3% of items with unequal rewards at T 1.0;
   the stage-1 gate of 20% still passes).
4. No new failure: no `<line>` tag in any answer, fewer format failures.

**What v3 does not fix, stated before training.** The untrained model under v3 is still below the
copy-the-OCR baseline on these items (mean reward 0.196 for copying every line: 36 clean lines score
1, damaged lines 0). v3 also copies more often (34% vs 19% at T 1.0), so the copy attractor seen in
the stage-2 GRPO smoke test may be at least as strong. Repair on damaged lines is still rare (3% pass).
Those are the questions P0 is meant to answer; they are not reasons to keep a prompt whose answers run
into the next line.

**Rule from here** (Gloria, 2026-11-21): `PROMPT_VERSION = "repair_v3"` in `rl/training/common_7b.py`
for Base, Base + clean-up, SFT, GRPO and SFT→GRPO alike, rendered by the one renderer with thinking off.
It is not changed again on the basis of the locked test set.
