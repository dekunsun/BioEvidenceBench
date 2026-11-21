# Release decision: module 7b checkpoints (7d)

*Draft by Claude, 2026-11-21, for Gloria's decision. Evidence: `rl/TRAINING_REPORT.md`,
`rl/training/runs/STAGE4_TEST_REPORT.md`, `rl/training/results_7c/ATTRIBUTION_7C.md`,
`rl/REWARD_AUDIT.md` part 2. Nothing here changes a test result or a checkpoint.*

## 0. How the criteria were set (read first)

The plan (7d) asks for release criteria written by Gloria **before** seeing results. No separate
release document was written before the test. What was fixed before the test, with her approval, is
the set of decision rules in `METRICS.md` section 5 and `TEST_PROTOCOL.md` sections 4–5. Section 1 uses
only those. Section 2 adds practical criteria written **after** the results; they are marked as such
and are arguments, not pre-registered tests. This is a deviation from the plan, recorded in `rl/LOG.md`.

## 1. Pre-registered criteria, per candidate

Criteria (all from the frozen rules): (a) repair above Base, raw and post-processed, interval above
0 in both seeds; (b) preservation non-inferior to Base (margin 1 point); (c) confirmed reward-hacking
rate ≤ 2%; (d) no severe loophole exploited; (e) for a GRPO checkpoint, adds to SFT (D − B).
Held-out book reported alongside.

| Candidate | (a) repair vs Base | (b) preservation | (c) hacking | (d) loophole | (e) adds to SFT | Cuvier vs Base |
|---|---|---|---|---|---|---|
| C. GRPO from base (s1, s2) | **fail** (−0.031 [−0.060, −0.016]; −0.003 [−0.011, 0.008]) | pass | pass (0%) | pass | – | **worse** in both seeds |
| C-CER (P1, s1) | **fail** (−0.010 [−0.030, 0.001]) | pass | pass (0%) | pass | – | not better |
| B. SFT (s1, s2) | pass (+0.36 [0.29, 0.56]; +0.37 [0.30, 0.56]) | pass (+0.06) | pass (0–0.45%) | pass (H4 not used) | – | better (+0.17) |
| D. SFT → GRPO (s1, s2) | pass (+0.36; +0.37) | pass (+0.07) | pass (≤ 0.1%) | pass (H4 not used) | **fail** on repair (−0.004, intervals span 0); preservation +0.003 / +0.004 above 0 | better (+0.15 / +0.16) |

**Statistically and practically meaningful**: SFT over Base (repair ×10, names 0.01 → 0.36–0.44,
preservation +6 points, both seeds, both test books). **Statistically but not practically
meaningful**: D over B on preservation (+0.3 points: about 3 fewer broken words per 1,000 correct
words). **Not meaningful**: every GRPO-from-base result.

**Regressions to weigh**: trained models break lines Base already had right (pass@1 0.94–0.96 on
those lines for B and D); they sometimes apply a language prior the book does not follow (`valdè`,
`magnæ`, `intérieur`); 9 of 2,000 GRPO seed-2 answers loop to the length limit; on the French book
SFT keeps only half its gain and repairs no ligature.

## 2. Practical criteria (written after the results)

1. **Use as automatic text replacement in a library pipeline: no.** B and D still break 1.3–1.8% of
   correct words and repair 40% of damaged ones on the in-book test (21% on Cuvier). A library would
   be introducing new errors into text that was right. Any use needs review and evidence (the main
   study's G1 design: the model points at the source, code keeps the original).
2. **Downstream value is untested.** The module measured line repair, not whether repaired lines raise
   extraction F1 in the BioEvidenceBench pipeline; the main study's exploratory G2 (LLM repair) did,
   with a much larger model.
3. **Cost**: B costs about $0.01 of GPU per run; D adds a GRPO run (about $0.45) for +0.3 points of
   preservation.

## 3. Proposed decision (Gloria to confirm or change)

| Question | Proposal | Why |
|---|---|---|
| Which checkpoint, if any | **No production release.** As a research artifact: **B, SFT seed 2** (`sft_s2`, release `rl-ckpt-20261121-2008_sft600s2`), with D seed 1 (`sft_grpo_s1`, release `rl-ckpt-20261121-2007_sft600s1`) kept beside it for comparison | B meets every pre-registered criterion that D meets; D's extra step buys only a practically small preservation gain. Seeds chosen by the stage-3 rule's metric on dev, not by a test result: B seed 2 (dev repair 0.361 vs 0.358), D seed 1 (0.353 vs 0.347); both differences are within noise |
| Make the weights public | **Gloria's decision** (the draft releases are private). If yes: a model card with the task, data licences (BHL / IMPACT, CC-BY 3.0; Qwen3 Apache 2.0), the test numbers, the regressions above and "not for automatic replacement" | Publishing is outward-facing |
| Keep investing in GRPO on this setup | **No** | Two seeds, two rewards, and an SFT start all show no repair gain; the cause (the policy rarely samples correct repairs; copying is a safe floor) is understood |
| Any further training | Optional, one small experiment (about $2–3 of the remaining about $14): Reward v1.4 (dash glyphs unified, H4 fixed), GRPO from B with pass@8 measured first; or rejection-sampling fine-tuning as the cheaper alternative. Only with a new dev-only plan and a new locked test | Tests the one open question (does GRPO help when the group already contains repairs?) without reopening this round |
