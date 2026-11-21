# Stage 4: locked test (module 7b P0 + P1)

*2026-11-21 21:12 UTC, one Secure RTX 4090, 16.6 min, about $0.25 (`20261121-2112_test4`). Protocol
`configs/TEST_PROTOCOL.md`, frozen with `configs/stage4_models.json` (commit `1140608`) before the
run. Every model and checkpoint was fixed on dev; nothing was chosen after this result. Analysis:
`analyze_test_7b.py` → `rl/training/results_test/` (`metrics.csv`, `paired_*.csv`, `pass8.csv`).*

## 1. Metrics (pass@1 over answers 0–3; repair rate and preservation raw; post-processed differ by ≤ 0.002)

| Model | In-book repair | names | preservation | format failure | Cuvier repair | names* | preservation |
|---|---|---|---|---|---|---|---|
| Copy the OCR | 0.000 | 0.000 | 1.000 | 0% | 0.000 | 0.000 | 1.000 |
| A. Base (A′ the same within 0.002) | 0.037 | 0.011 | 0.921 | 4.4% | 0.047 | 0.050 | 0.921 |
| B. SFT s1 / s2 | 0.399 / 0.410 | 0.44 / 0.36 | 0.983 / 0.982 | 0.2 / 0.7% | 0.213 / 0.212 | 0.20 / 0.38 | 0.981 / 0.982 |
| C. GRPO s1 / s2 | 0.006 / 0.034 | 0 / 0 | 0.996 / 0.990 | 0.3 / 0.4% | 0.002 / 0.011 | 0 / 0 | 0.999 / 0.998 |
| D. SFT→GRPO s1 / s2 | 0.394 / 0.406 | 0.42 / 0.33 | 0.986 / 0.987 | 0.2 / 0.4% | 0.200 / 0.209 | 0.20 / 0.33 | 0.983 / 0.985 |
| C-CER (P1) s1 | 0.027 | 0 | 0.993 | 0.3% | 0.032 | 0 | 0.995 |

\* Cuvier has 10 damaged name words in its 500 lines (7 lines): name recovery there is descriptive.
In-book has 22 damaged name words (corrected 2026-11-21: first written as 20 and 88, counting each word once per answer). Larger confirmation (3,226 more in-book lines): repair B 0.527 /
0.510, D 0.525 / 0.508, Base 0.038; names B 0.47 / 0.44, D 0.47 / 0.46.

## 2. Pre-registered decisions (paired Δ, 95% interval over split-v2 blocks; Cuvier over pages)

| Question | Comparison | Seed 1 | Seed 2 | Verdict |
|---|---|---|---|---|
| GRPO improves the delivered repair | C − A, raw repair, in-book | −0.031 [−0.060, −0.016] | −0.003 [−0.011, 0.008] | **No** (seed 1 is below 0) |
| … content, not only format | C − A′, post-processed | −0.031 [−0.063, −0.016] | −0.003 [−0.010, 0.008] | **No** |
| … on the held-out book | C − A, Cuvier | −0.046 [−0.082, −0.018] | −0.037 [−0.072, −0.011] | **No** (both below 0) |
| SFT → GRPO adds to SFT | D − B, raw repair, in-book | −0.004 [−0.020, 0.001] | −0.004 [−0.012, 0.003] | **No** |
| … larger confirmation | D − B, 3,226 lines | −0.002 [−0.005, 0.001] | −0.002 [−0.010, 0.006] | **No** |
| … Cuvier | D − B | −0.014 [−0.033, 0.010] | −0.003 [−0.017, 0.010] | **No** |
| Preservation, D − B (margin 1 point) | in-book / rest / Cuvier | +0.003 / +0.003 / +0.003 | +0.004 / +0.003 / +0.004 | **Pass** everywhere (small gain, interval above 0) |
| Preservation, C − A | in-book / Cuvier | +0.075 / +0.078 | +0.069 / +0.077 | **Pass** (by changing less) |
| Names without harm, D − B | in-book | −0.023 [−0.083, 0.038] | −0.034 [−0.096, 0.000] | **No** gain |
| Descriptive: B − A | in-book / Cuvier | +0.362 / +0.166 | +0.373 / +0.165 | intervals well above 0 |
| P1: C-CER − C (seed 1) | in-book / Cuvier | +0.021 [0.007, 0.039] / +0.031 [0.008, 0.060] | – | slightly more repair than C |
| P1: C-CER − A (seed 1) | in-book / Cuvier | −0.010 [−0.030, 0.001] / −0.015 [−0.048, 0.011] | – | still not above Base |

The page-level bootstrap (sensitivity, 93 in-book pages) puts every interval on the same side of 0
as the block bootstrap, except C-CER − A in-book, which is below 0 at page level ([−0.020, −0.001])
and spans 0 at block level. The larger confirmation also shows one seed-2-only gain: D − B names
+0.022 [0.006, 0.045] (seed 1: 0.000 [−0.012, 0.017]), which the rule does not count.

**Answers to the questions of METRICS.md section 0** (this task, this model, these settings):
1. GRPO from the base model does **not** improve OCR repair; it trades repair for preservation by
   learning to copy. In seed 1 and on Cuvier, repair is measurably below the untrained model.
2. Format is not the story: Base fails the gates in 4.4% of answers, and the fixed clean-up recovers
   almost none of them (A′ = A within 0.002); the failures are run-ons and broken lines, not wrappers.
3. A dense reward (1 − CER) moves GRPO slightly off pure copying (+2–3 points over C) but not
   above the base model: the reward shape is not the main cause.
4. SFT leaves **no room GRPO could use** here: D equals B on repair and names, with about 0.3 points
   better preservation (both seeds, every set).
5. SFT's name gains come with better, not worse, preservation (+0.06).
6. SFT transfers to the unseen French book at about half its in-book gain (0.21 vs 0.40 repair).

## 3. pass@1 and pass@8 (reward 1.0; 7c)

| Model | In-book pass@1 | pass@8 | Cuvier pass@1 | pass@8 |
|---|---|---|---|---|
| Copy | 0.478 | 0.478 | 0.752 | 0.752 |
| Base | 0.376 | 0.422 | 0.577 | 0.636 |
| SFT s1 / s2 | 0.561 / 0.554 | 0.612 / 0.598 | 0.703 / 0.710 | 0.758 / 0.768 |
| GRPO s1 / s2 | 0.478 / 0.486 | 0.482 / 0.494 | 0.747 / 0.747 | 0.748 / 0.750 |
| SFT→GRPO s1 / s2 | 0.567 / 0.562 | 0.610 / 0.604 | 0.718 / 0.726 | 0.762 / 0.774 |
| C-CER s1 | 0.483 | 0.492 | 0.749 | 0.756 |

GRPO's pass@1 rises above Base (0.48 vs 0.38) **without any repair**: it equals Copy's, because a
copied clean line scores 1. A higher pass rate is not a better repair. GRPO after SFT raises pass@1
by about 0.006–0.008 and leaves pass@8 unchanged, the pattern Yue et al. (2025) describe:
answers SFT could already give become slightly more likely.

## 4. Reward reliability (METRICS.md 3, 5)

Candidates = answers with reward ≥ 0.75 that are further from the expert line than the OCR. The
check as run flags 4,418 answers, but most differ from the reference only in punctuation, which
Reward v1.3 does not score by design (`REWARD_DESIGN.md`: "Punctuation is not scored in v1"); case
differences are neutral by Gloria's decision. Ignoring punctuation and case, word-level candidates
are (answers 0–3):

| Model | In-book | Cuvier | Larger confirmation |
|---|---|---|---|
| Base | 43 / 2,000 (2.2%) | 67 / 2,000 (3.4%) | 215 / 12,904 (1.7%) |
| SFT s1 / s2 | 0 / 9 (0–0.5%) | 2 / 0 | 33 / 46 (0.3–0.4%) |
| GRPO s1 / s2, C-CER | 0 | 0 | – |
| SFT→GRPO s1 / s2 | 1 / 2 | 1 / 0 | 29 / 39 (0.2–0.3%) |

Typical kind: on a clean line, one invented word appended (reward 0.75 = 1 − 0.25 per inserted
word), or a repaired line with one inserted word. No output type was found that earns more than the
correct answer. `results_test/hacking_review_gloria.xlsx` holds 30 blind candidates (20 Base, all
10 distinct trained-model ones) for Gloria to confirm; the rate counts only confirmed cases.
Separately, punctuation fidelity is outside Reward v1.3 and outside these metrics (a scope limit).

**Gloria's review (2026-11-21)**: all 30 candidates confirmed. Confirmed rate Base 2.2% in-book /
3.4% Cuvier (above 2%: the reward is not a reliable judge of Base's answers), trained models
0–0.45%. She also found hole H4 (finishing a line-end hyphenated word scores 1.0); no trained model
exploits it. `rl/REWARD_AUDIT.md` part 2.
