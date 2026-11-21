# 7c: where and why (on the frozen stage-4 test answers)

*`rl/training/attribution_7c.py`, CPU, $0, 2026-11-21. Answers 0–3 of the locked test run
`20261121-2112_test4`, after the fixed clean-up. Nothing was chosen: this describes the models the
pre-registered test already judged (`runs/STAGE4_TEST_REPORT.md`). Tables: `repair_by_error_type.csv`,
`edit_behaviour.csv`, `difficulty_pass1.csv`, `difficulty_repair.csv`.*

## 1. What SFT learned, by error type (in-book repair rate, Base → SFT s1 / s2)

| Damaged word type | Words | Base | SFT | GRPO | SFT→GRPO |
|---|---|---|---|---|---|
| Ordinary misread letters | 399 | 0.05 | 0.45 / 0.47 | 0.01 / 0.05 | 0.45 / 0.46 |
| Long s (ſ) | 169 | 0.00 | 0.32 / 0.35 | 0 | 0.32 / 0.35 |
| Split by the OCR | 34 | 0.07 | 0.25 / 0.29 | 0.02 / 0.05 | 0.24 / 0.29 |
| Ligature (æ œ) | 29 | 0.00 | 0.39 / 0.31 | 0 | 0.36 / 0.28 |
| Scientific name | 22 | 0.01 | 0.43 / 0.34 | 0 | 0.40 / 0.32 |
| Digit | 9 | 0.03 | 0.22 / 0.25 | 0 | 0.22 / 0.25 |
| Missing in the OCR | 3 | 0 | 0 | 0 | 0 |

Base repairs almost nothing of any type, and never writes ſ or a ligature the OCR lost: these are
transcription conventions of the expert edition, which SFT shows the model and GRPO cannot (it
would first have to sample them). On Cuvier, SFT repairs French letters at half the in-book rate
(0.20–0.23) and no ligature: the conventions it learned do not all carry over.

## 2. Edit behaviour: "more careful", not "more edits"

| In-book | Edit rate | Edit precision | Words broken per answer | Words inserted per answer |
|---|---|---|---|---|
| Base | 0.50 | 0.04 | 0.36 | 0.51 |
| SFT s1 / s2 | 0.61 / 0.62 | 0.41 / 0.43 | 0.13 / 0.13 | −0.01 / 0.08 |
| GRPO s1 / s2 | 0.07 / 0.17 | 0.05 / 0.18 | 0.04 / 0.03 | 0.00 / 0.25* |
| SFT→GRPO s1 / s2 | 0.60 / 0.60 | 0.43 / 0.44 | 0.10 / 0.10 | −0.01 / 0.03 |
| C-CER s1 | 0.26 | 0.09 | 0.03 | 0.15 |

\* GRPO seed 2's mean comes from 9 of 2,000 answers that loop until the 128-token limit (reward 0).
Edit precision = reference words the model changed that are now right ÷ words it changed.

- Base edits half the lines and only 4% of its changes are right: editing is harmful for Base, so
  under a reward that penalises broken words, not editing is the better policy. This is the copy
  trap seen in training, and why GRPO from Base edits only 7–17% of lines.
- **What GRPO after SFT did change**: same edit rate and repairs as SFT, but about 25% fewer broken
  words (0.13 → 0.10 per answer, both seeds). That is the +0.3 point preservation gain of the test,
  and it is what Reward v1.3's −0.5 per broken word asks for. It did not add repairs.

## 3. Difficulty before training (lines grouped by Base's pass rate over 8 answers)

| In-book group | Lines | Base pass@1 | SFT | GRPO | SFT→GRPO |
|---|---|---|---|---|---|
| 0% (Base never right) | 289 | 0.00 | 0.30 / 0.29 | 0.13 / 0.12 | 0.30 / 0.29 |
| 1–99% | 49 | 0.53 | 0.83 / 0.81 | 0.92 / 0.96 | 0.87 / 0.84 |
| 100% (Base always right) | 162 | 1.00 | 0.95 / 0.94 | 0.97 / 0.99 | 0.95 / 0.96 |

- SFT's gain is mostly on lines Base **never** gets right in 8 tries (0.00 → 0.30): new answers,
  not a sharper choice among answers Base already gives. GRPO's 0.13 there comes from copying
  clean lines Base used to damage, with repair rate 0.004–0.020.
- On the lines Base already gets right, every trained model sometimes breaks them (0.94–0.99).
- Together with pass@8 (stage-4 report section 3): GRPO after SFT raises pass@1 by under one point
  and pass@8 not at all. Consistent with Yue et al. (2025): RL here makes answers the policy
  already samples slightly more likely; it did not reach answers outside that set.

## 4. Gloria's reading

**Gloria's reading of 43 test lines (2026-11-21; `results_7c/received/2026-11-21_reading_sheet_gloria.xlsx`).**
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
