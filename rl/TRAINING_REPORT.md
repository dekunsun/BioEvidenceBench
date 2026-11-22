# Training report: SFT and GRPO for historical OCR line repair (modules 7b–7c)

*2026-11-21. Dekun Sun (design decisions, audits, reviews) with Claude (code, runs, analysis).
Design fixed before training in `rl/training/configs/METRICS.md`; locked test protocol in
`rl/training/configs/TEST_PROTOCOL.md`, frozen with the model list (commit `1140608`) before any
test line was scored. Development decisions are logged in `rl/LOG.md` (Chinese: `rl/PLAN_zh.md`
section 14). The author's reward-hacking review and her reading of 43 lines are in section 6.*

## TL;DR

- **Supervised fine-tuning works; GRPO does not, for this model and task.** On 500 locked in-book
  test lines, SFT raises the damaged-word repair rate of Qwen3-0.6B from 0.04 to 0.40–0.41
  (scientific names 0.01 → 0.36–0.44) while keeping more correct words (0.92 → 0.98).
- **GRPO from the base model learns to copy the OCR.** Repair stays at or below the untrained model
  (0.006 / 0.034; below it in seed 1 and on the held-out book), its pass rate rises only because
  copying a clean line scores 1. A dense 1 − CER reward changes this by 2–3 points, not more.
- **GRPO after SFT adds no repair** (Δ −0.004, intervals spanning 0, three test sets). It makes the
  model break about a quarter fewer correct words (+0.3 points preservation), which is exactly what
  Reward v1.3 penalises.
- **Why**: GRPO can only reinforce answers the policy already samples. The base model's edits are
  right 4% of the time, so "change nothing" is its best reachable policy; SFT's gains come mostly
  from lines the base model never solved in 8 tries. On a cross-language book (Cuvier, French),
  SFT keeps about half its gain.
- Cost: **$5.83 of GPU** (RunPod RTX 4090, $20 cap), all runs and failures included; publishing and the
  later pipeline test (`results/sft_repair_pipeline/REPORT.md`) bring the total to about $5.93.
- **Released** (the author, 7d): the SFT seed-2 checkpoint as a research checkpoint, [`rl-sft-ocr-repair-v1`](https://github.com/dekunsun/BioEvidenceBench/releases/tag/rl-sft-ocr-repair-v1),
  `sft_s2.tar`, SHA-256 `bfeb5657e7e078d25b1c47c64a8afd2c63c80d5e8bb0594f285d0fafdea16e8c`; not for automatic replacement of library text (`rl/RELEASE_DECISION.md`).

## 1. Setup

| | |
|---|---|
| Task | Task B: repair one line of legacy BHL OCR into the expert transcription (IMPACT ground truth), given the line before and after as context (`rl/env/task_b_ocr_repair/`) |
| Data | Split v2 by content pages, 5 training books (Butler, Reeve, Trudy, Chitinskelett, Piscium); 39,439 usable lines (train 31,909, dev 3,787, in-book test 3,743) after the data rules and two alignment audits (one by the author, kappa 0.90); Cuvier held out, built only when the test protocol was frozen |
| Reward | Reward v1.3: weighted damaged-word repair rate (names × 3) − 0.5 per broken correct word − 0.25 per inserted word, clipped to [−1, 1]; hard gates for format, length (0.5–1.5×) and alignment; punctuation not scored, case-only differences neutral (`REWARD_DESIGN.md`) |
| Model | `Qwen/Qwen3-0.6B` (instruct), thinking off everywhere (`enable_thinking=False`, one renderer for all stages), prompt `repair_v3` |
| Training mix | 4,800 lines, every block of 16 = 8 damaged-name / 3 clean / 5 other damaged (`make_data_p0.py`) |
| SFT (B) | 600 steps × 16 lines (two passes), lr 1e-5, completion-only loss; dev chose steps 600 / 400 |
| GRPO (C, D) | TRL 1.18.2, 300 steps × 16 prompts × 8 answers, T 1.0, `dapo` loss, std scaling per group, β = 0, lr 1e-6, vLLM colocated; float32 master weights |
| Checkpoints | every 50 steps, chosen on 500 dev lines by a rule fixed before the runs (highest post-processed repair rate with preservation ≥ Base − 0.01) |
| Seeds | 2 per trained condition (training seed and block order); P1 one seed |
| Test | 500 in-book test lines (100 per book, 93 pages, 12 blocks; the 17 lines the audits displayed left out), 500 Cuvier lines, 3,226 more in-book lines for confirmation; T 0.7 / top-p 0.8 / top-k 20, 8 answers per line, pass@1 over answers 0–3 |
| Statistics | paired Δ, 95% interval from 2,000 bootstrap resamples of split-v2 blocks (Cuvier: pages); a claim needs every seed's interval on the same side of 0; preservation by non-inferiority (margin 1 point) |

## 2. Is it really better? (pre-registered, locked test)

| Model | In-book repair | Names | Preservation | Cuvier repair | Larger set repair |
|---|---|---|---|---|---|
| Copy the OCR | 0 | 0 | 1.000 | 0 | 0 |
| A. Base | 0.037 | 0.011 | 0.921 | 0.047 | 0.038 |
| B. SFT (s1 / s2) | 0.399 / 0.410 | 0.44 / 0.36 | 0.983 / 0.982 | 0.213 / 0.212 | 0.527 / 0.510 |
| C. GRPO | 0.006 / 0.034 | 0 / 0 | 0.996 / 0.990 | 0.002 / 0.011 | – |
| D. SFT → GRPO | 0.394 / 0.406 | 0.42 / 0.33 | 0.986 / 0.987 | 0.200 / 0.209 | 0.525 / 0.508 |
| C-CER (P1, s1) | 0.027 | 0 | 0.993 | 0.032 | – |

| Pre-registered question | Verdict | Key interval (seed 1; seed 2) |
|---|---|---|
| GRPO improves the delivered repair (C − A) | **No** | −0.031 [−0.060, −0.016]; −0.003 [−0.011, 0.008] |
| … content, not only format (C − A′) | **No** | same within 0.002 |
| … on the held-out book | **No**, worse than Base | −0.046 [−0.082, −0.018]; −0.037 [−0.072, −0.011] |
| SFT → GRPO adds to SFT (D − B), in-book / larger / Cuvier | **No** | −0.004 [−0.020, 0.001]; −0.004 [−0.012, 0.003] (in-book) |
| Preservation, D − B | **Pass** (non-inferior; interval above 0) | +0.003; +0.004 |
| Names without harm (D − B) | **No** gain | −0.023 [−0.083, 0.038]; −0.034 [−0.096, 0.000] |
| P1: does 1 − CER escape copying? (C-CER − C, C-CER − A) | slightly better than C, not above Base | +0.021 [0.007, 0.039]; −0.010 [−0.030, 0.001] |

Format is not the story: Base fails the gates in 4.4% of answers and the fixed clean-up recovers
almost none (A′ = A within 0.002). A page-level bootstrap (sensitivity only) agrees with every
verdict. Full tables: `rl/training/runs/STAGE4_TEST_REPORT.md`, `rl/training/results_test/`.

## 3. Where did it improve? (7c, on the frozen test answers)

- **By error type** (in-book repair, Base → SFT): ordinary misread letters 0.05 → 0.45–0.47, long s
  0 → 0.32–0.35, ligatures 0 → 0.31–0.39, scientific names 0.01 → 0.34–0.43, OCR splits 0.07 →
  0.25–0.29, digits 0.03 → 0.22–0.25; words missing from the OCR 0 everywhere (by design they cannot
  be recovered). GRPO is near 0 on every type. On Cuvier, SFT repairs French letters at half the
  in-book rate and no ligature.
- **By edit behaviour**: Base edits half the lines and only 4% of its changes are right; SFT edits
  61–62% with 41–43% precision; GRPO edits 7–17%. SFT → GRPO keeps SFT's edit rate and repairs but
  breaks 0.10 instead of 0.13 correct words per answer.
- **By difficulty before training**: on the 289 in-book lines Base never got right in 8 answers,
  SFT reaches pass@1 0.30; GRPO 0.12–0.13, almost all from copying clean lines it used to damage.

Details: `rl/training/results_7c/ATTRIBUTION_7C.md`.

## 4. Why?

1. **GRPO needs the right answer in the group.** The group-relative advantage only moves the
   policy toward answers it samples. Base's repairs are rare and mostly wrong (4% edit precision), so
   within a group the answers that change least score best, copying spreads, and the signal
   disappears: groups with no reward difference rose from 46–55% to 90–95%, entropy fell to 0.01–0.03,
   copied answers reached 85–93% (every completion was logged). The toy GRPO of module 7a showed the
   same vanishing signal, but there it came from success; here it came from collapse.
2. **It is not mainly the reward shape.** With 1 − CER, which gives partial credit and never zeroes
   a damaged line, GRPO still drifted to copying (70–90% of answers) and stayed below Base on repair.
3. **Oversampling is necessary but not sufficient.** Half of every batch held a damaged name, and C
   recovered no name; SFT recovered a third to almost half.
4. **SFT supplies answers outside the base model's reach**: the expert edition's conventions (long
   s, ligatures) that Base never writes. After SFT, GRPO raises pass@1 by under
   one point and pass@8 not at all, consistent with Yue et al. (2025, arXiv 2504.13837): RL made
   answers the policy already gives slightly more likely; it did not find new ones.
5. **What GRPO after SFT did learn is the penalty**: a quarter fewer broken words, the term Reward
   v1.3 penalises at −0.5 per word. The training reward rose 0.54 → 0.65 while dev repair stayed flat:
   a rising training reward was not a better repair.

## 5. What did it cost?

| | |
|---|---|
| GPU | **$5.83** (RunPod balance 24.67 → 18.84): stop test, 4 calibration launches (3 failed on set-up), smoke test, prompt comparison, P0 two seeds, SFT-600 re-run, P1, locked test; per-run log in `rl/LOG.md` |
| Preservation | every trained model keeps more correct words than Base (0.98–1.00 vs 0.92); D passes non-inferiority against B |
| Lines Base got right | trained models break some of them (pass@1 0.94–0.99 on Base's always-right lines) |
| Degenerate outputs | 9 of 2,000 GRPO seed-2 answers loop to the 128-token limit (reward 0) |
| Reward weaknesses seen | finishing a line-end hyphenated word scores 1.0 (H4); one invented word on a clean line scores 0.75; punctuation is not scored at all (section 6) |
| Not measured | side effects on other tasks (task A) and on general ability |

## 6. Reviews and audits

- **Reward hacking** (METRICS.md 3, 5), reviewed by the author (30 blind candidates, all confirmed).
  Confirmed rate: **Base 2.2% in-book, 3.4% Cuvier** (above the 2% threshold: Reward v1.3 does not
  judge the untrained model's answers reliably); **trained models 0–0.45%** (below it). Lower bounds,
  since one independent check found the candidates. The author also found a hole the probes had missed
  (**H4**): a word broken by the line-end hyphen can be finished with letters the line does not have
  and still score 1.0. It earns the same as the correct answer, Base does it (43 answers at 1.0), no
  trained model does, and GRPO training never rewarded it, so no completed run is affected; it is
  fixed in v1.4 before any further training. Details: `rl/REWARD_AUDIT.md` part 2.
- **The author's reading of 43 test lines (2026-11-21; `results_7c/received/2026-11-21_reading_sheet_gloria.xlsx`).**
  Base wrong / D right (25 lines): every one is a repair that matches the expert line: misread letters
  (`coDected` → `collected`, `iu` → `in`, `e3'e` → `eye`), Latin endings (`acnminatd` → `acuminatâ`),
  long s (`obfcuritate` → `obſcuritate`), a ligature in a subfamily name (`EMBERIZINÆ`), French
  spacing (`delà` → `de la`); D also stops at the line-end hyphen and adds no word where Base
  continued or padded (R14, R26, R27, R29, R32, R36, R37). One caveat (R08): `V e r h o e f f` →
  `Verhoeff` only removes letter spacing, not a misreading. Measured on all test answers, letter-spaced
  words are about 3% of the words SFT and D repair, so they do not drive the gain.
  Base right / D wrong (18 lines): 13 change, add or drop letters of a correct word with no support
  on the line (`Visagapatam` → `Viseugapatam`, `Commerson` → `Comerson`, `Incertellus` → `Incertus`,
  `very least` for `veriest`); 4 apply a language prior the book does not follow (`valde` → `valdè`,
  `magnae` → `magnæ`, `l'interieur` → `l'intérieur`, `Stt.` → `Stett.`), which the reward rightly
  penalises; 1 (R40) is a scoring problem: D only changed the hyphen in `45-46` to an en dash and lost
  0.5 (hole H5 in `rl/REWARD_AUDIT.md`). So SFT → GRPO's errors are mostly unsupported rewriting of
  correct words, the behaviour the −0.5 penalty targets and which GRPO reduced by about a quarter.
- `rl/REWARD_AUDIT.md` part 2 (task B, 2026-11-21): probes on dev plus the test answers. No probe beats the honest answer; five holes: copying is a safe floor (H1, decided the GRPO result), one inserted word costs only 0.25 (H2, rare), punctuation unscored (H3, 7–12% of answers score 1.0 with different punctuation), line-end hyphen continuation free (H4, found by the author), dash glyphs scored inconsistently (H5, found by the author; 16% of in-book damaged words differ only in a dash; SFT's repair rate without them is 0.39, so the conclusions hold). Fixes are for a v1.4 tested on dev, not applied to this round.

## 7. Development decisions and deviations (all on dev or before the test; none after it)

| Decision | Why | Record |
|---|---|---|
| Prompt `repair_v2` → `repair_v3` (target line last, inside `<line>` tags) | 41% of Base answers ran on into the next line; v3: 2%, signal unchanged | `runs/20261121-1756_promptcmp/REPORT.md` |
| Training mix about 20% clean lines (stage 2 had 31%) | copying is more attractive with more clean lines | The author, `METRICS.md` 9 |
| float32 master weights (stages 1–2 used bf16) | bf16 weights round away most updates at lr 1e-6 | `METRICS.md` 9 |
| Seed-specific block order | TRL gives vLLM the same sampling seed in every run | `METRICS.md` 9 |
| SFT 300 → 600 steps, B and D re-run | dev repair still rising at step 300 | The author, `rl/LOG.md` |
| P1 reduced to the reward ablation; data and name-weight ablations dropped | C learns no names with both, so removing either cannot show a difference | The author, `TEST_PROTOCOL.md` 2 |
| Cuvier built with the automatic rules only | nobody has read the book, so no manual exclusions or scan-checked typos | `src/rl_task_b_build_cuvier.py` |
| Reward-hacking candidates split into punctuation-only and word-level | punctuation is unscored by design, case neutral by decision; the check as frozen flags both | `STAGE4_TEST_REPORT.md` 4 |

## 8. Limits

- One small model (0.6B), one reward family, 300 GRPO steps at one learning rate, two seeds: "GRPO
  does not help" holds for this setting, not for GRPO in general. A larger model, or GRPO from a
  model whose samples already contain repairs, may behave differently.
- The in-book test has 12 independent page blocks, so intervals are coarse; Cuvier has 7 lines with
  damaged names, so name results there are descriptive.
- All texts are public (BHL, IMPACT) and may be in Qwen3's pre-training data.
- Reward v1.3 ignores punctuation; the metrics inherit that blind spot.

## 9. Next experiments this suggests

1. GRPO from a stronger start: SFT checkpoints at different steps, or a larger model, measuring how
   often the sampled group already contains a correct repair (pass@8 before training) and whether
   GRPO's gain grows with it.
2. A reward that pays for repairs only when the line was damaged and gives copying a damaged line
   a small negative score, so "change nothing" is no longer the safe optimum; checked first on dev
   for new exploits (inserted words, punctuation).
3. Rejection-sampling fine-tuning (keep SFT model answers that score 1, train on them) as a
   cheaper alternative to GRPO for the same purpose.
