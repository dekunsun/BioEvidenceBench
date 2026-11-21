# Release decision: module 7b checkpoints (7d)

*Drafted by Claude, decided by Gloria on 2026-11-21 (section 4). Evidence: `rl/TRAINING_REPORT.md`,
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

## 4. Decision (Gloria, 2026-11-21: "按你的建议，同意选择 B Seed 2；同意在完成发布前检查后公开研究权重；暂时不再开展新的 GPU 训练实验")

1. **Checkpoint: B, SFT seed 2** (`sft_s2.tar`, draft release `rl-ckpt-20261121-2008_sft600s2`). No
   production use.
2. **Publish the weights as a research checkpoint after the pre-release checks below.**
3. **No new GPU training for now.** Reward v1.4 stays planned, not built. GPU spend stays at $5.83 of $20.
   The other draft releases (C, D, C-CER and D seed 1) stay private drafts.

## 5. Pre-release checks

| Check | Result | How |
|---|---|---|
| The file is the checkpoint that was tested | **Pass** | `stage4_models.json` (frozen) names asset 776877455, 1,203,578,880 bytes; the stage-4 pod downloaded that asset and checked its size before evaluating |
| SHA-256 of the file | **Pass** | computed on the pod from the downloaded draft asset: `bfeb5657e7e078d25b1c47c64a8afd2c63c80d5e8bb0594f285d0fafdea16e8c`; GitHub's digest of the re-uploaded file is the same |
| Contents: model files only, no secret | **Pass** | members listed on the pod: `sft_s2/` with `chat_template.jinja`, `config.json`, `generation_config.json`, `model.safetensors`, `tokenizer.json`, `tokenizer_config.json`, nothing else; the GitHub token was only an environment variable on the pod and is never written to disk |
| Base model licence | **Pass** | `Qwen/Qwen3-0.6B`: Apache 2.0 (Hugging Face card, checked 2026-11-21) |
| Data licences and rights | **Pass** | `finebooks/bhl-impact-gt` CC-BY 3.0 (attribution in the card); BHL `CopyrightStatus` of all six items: not in copyright / public domain |
| Personal or sensitive data | **Pass** | 19th- and early-20th-century printed natural history; no Cal Academy or private data |
| Model card with intended use, results, regressions, out-of-scope use | **Pass** | `rl/release/MODEL_CARD_sft_s2.md` |
| Results reproducible from the repository | **Pass** | code commit `c994ade`, run folder, data hashes, prompt file, decoding in the card |
| Known evaluation weaknesses disclosed | **Pass** | reward holes H1–H5 and the dash-glyph share in the card |
| Contamination disclosed | **Pass** | in the card |

## 6. Publishing (Gloria, 2026-11-21: "你直接发就可以")

Claude publishes. This session has no tool that edits releases, so a short RunPod pod (no GPU work)
runs `rl/release/publish_release.py` with the repository token from RunPod Secrets. The script:
1. downloads `sft_s2.tar` and checks its size against the frozen model list;
2. computes the SHA-256 and lists the files inside, and stops if any file is not a model or
   tokenizer file;
3. creates a new release `rl-sft-ocr-repair-v1` at the training commit `c994ade`, with the model
   card and the SHA-256 as notes;
4. uploads the same file, checks GitHub's digest against the SHA-256, then publishes.

The private drafts are left unchanged, so the D, C and C-CER checkpoints stay unpublished.
Result: `rl/release/publish_result.json`.

**Published 2026-11-21 22:41 UTC**: [https://github.com/dekunsun/BioEvidenceBench/releases/tag/rl-sft-ocr-repair-v1](https://github.com/dekunsun/BioEvidenceBench/releases/tag/rl-sft-ocr-repair-v1), asset `sft_s2.tar` (1,203,578,880 bytes,
SHA-256 `bfeb5657e7e078d25b1c47c64a8afd2c63c80d5e8bb0594f285d0fafdea16e8c`), tag at commit `c994ade`. Pod `20261121-2239_publish`, 3 minutes on an RTX 3090
(about $0.03; RunPod balance unchanged at 18.84 at the time of writing). The private drafts were not
changed.
