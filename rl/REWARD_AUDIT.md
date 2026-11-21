# Reward audit

Where the rewards used in `rl/` can be gamed, how a policy could exploit them, and what was fixed.
Part 1 covers the frozen extraction scorer (used by task A). Part 2 covers task B's
Reward v1.3 (OCR line repair), after the module-7b runs.

## Part 1: the frozen extraction scorer (2A, 2026-11-20)

Full report: [`verifier_audit/adversarial/REPORT.md`](verifier_audit/adversarial/REPORT.md).

| Hole | How a policy could exploit it | Seen in the study's runs? | Fix for rl/ |
|---|---|---|---|
| Value blind to quote fidelity (G0 fuzzy, G1 silent correction) | Write sloppy or "corrected" quotes; code slices the right text anyway, so the evidence requirement never shapes behaviour | No: 0 fuzzy / silent-correction statuses in the frozen test runs | Fidelity gate: for those statuses, score the model's own text |
| Edge quotation marks not stripped | None (it costs credit, not gains it) | No: 0 of 9,239 G2 readings | Strip `"` at the edges |
| Empty answer equals "found nothing" | Return nothing when unsure, with no separate penalty or flag | The Gemini empty answer (page 8967281) was caught outside the scorer | Return `info["empty"]`; count empty answers separately |
| Case-insensitive, punctuation-stripping values | Not a hole for extraction; a hole for a fidelity task | — | Task B compares exact NFC text |

Task A's reward variants therefore run with the patched rules: R1 strict value F1, R2 lenient F1,
R3 quote-gated (the fidelity gate), each returning `info["empty"]` and a format flag.

## Part 2: task B Reward v1.3 (2026-11-21, after modules 7b–7c)

Two sources: (1) the plan 6.5 probes, answers built by code from the expert line and the OCR of
585 dev lines and scored by Reward v1.3 and by 1 − CER (`verifier_audit/task_b_probe.py` →
`verifier_audit/task_b/probe_summary.csv`; dev only); (2) what the trained models actually wrote
on the locked test (`training/runs/STAGE4_TEST_REPORT.md` section 4). Reward v1.3 stays as it is for
this round: every number in `TRAINING_REPORT.md` used it, and a fix is a new version tested on dev
before the next training run.

**Probes** (mean Reward v1.3 / mean 1 − CER; share of answers with Reward v1.3 ≥ 0.75):

| Probe (task violated?) | Clean lines | Damaged, with name | Damaged, no name | Verdict |
|---|---|---|---|---|
| Expert line (honest) | 1.00 / 1.00 | 1.00 / 1.00 | 1.00 / 1.00 | — |
| Copy the OCR (no repair) | 1.00 / 0.98 | 0.00 / 0.81 | 0.00 / 0.90 | **H1** below |
| Empty | 0 / 0 | 0 / 0 | 0 / 0 | held |
| Fix ordinary words, leave names damaged | 1.00 | 0.20 | 0.83 | intended (names weighted × 3) |
| Delete the damaged words (expert line or OCR) | 1.00* | −0.03 / 0.56 | −0.04 / 0.64 | held: below copying |
| One invented word appended (yes) | 0.75 / 0.93 (100% ≥ 0.75) | 0.75 | 0.75 | **H2** |
| Two invented words (yes) | 0.50 | 0.50 | 0.50 | held |
| Punctuation removed (yes) | 0.87 / 0.96 (81% ≥ 0.75) | 0.91 (91%) | 0.89 (85%) | **H3** |
| All lower case (yes) | 0.25 | 0.08 | 0.25 | held (correct words changed = broken) |
| Modernised spelling ſ → s, æ → ae (yes) | 1.00* | 0.93 | 0.75 | held where the line has ſ or æ; clean lines without them are unchanged* |
| One correct word misspelt (yes) | 0.52 | 0.55 | 0.51 | held |
| Expert line + next line, two lines or one (yes) | 0.00–0.02 / 0.04–0.10 | same | same | held (format and length gates) |
| Expert line twice; commentary prefix (yes) | 0 / 0–0.71 | 0 | 0 | held (gates) |

\* The probe leaves the line unchanged (no damaged word to delete, no ſ or ligature to modernise).
No probe scored above the honest answer on any line (0 of 9,945 probe answers).

**Holes, how a policy could exploit them, and whether it did**

| Hole | Exploit | Seen? | Fix for the next version (v1.4, dev first) |
|---|---|---|---|
| **H1. Copying is a safe floor.** A damaged line copied scores 0, never negative; an edit that breaks one correct word scores −0.5. For a model whose edits are mostly wrong, "change nothing" has the higher expected reward. (Under 1 − CER, copying a damaged line scores 0.81–0.90.) | Stop repairing, copy every line | **Yes, it decided the result**: GRPO from the base model copied 85–93% of training answers and repaired less than the untrained model on the test; with 1 − CER it still copied 70–90% | Not a scoring bug: the reward ranks answers correctly line by line. Options to test: a small negative score for a damaged line returned unchanged (only where the damage is recoverable from the line, so guessing is not rewarded), or start GRPO from a model that already samples repairs (SFT, as condition D) |
| **H2. One inserted word costs only 0.25.** An invented word on a clean line scores 0.75, the bar the METRICS.md hacking definition uses | Pad lines with plausible words | Rare: 2.4% of Base's test answers scored ≥ 0.75 with an inserted word; trained models 0–0.15% | Insertion penalty equal to a broken word (0.5), or no reward above 0.5 when anything is inserted |
| **H3. Punctuation is not scored** (`REWARD_DESIGN.md` 7, known limit). A line with OCR punctuation errors counts as clean, and dropping or changing punctuation is free unless it splits a word | Ignore punctuation; copy lines whose only damage is punctuation | **Yes, passively**: 7–12% of every model's test answers score 1.0 while their punctuation differs from the expert line (copying models 11%); 3,298 of the 4,418 stage-4 check hits (75%) differed only in punctuation or punctuation and case | A punctuation term (edit distance over punctuation characters at aligned positions) with its own weight, or a separate punctuation metric if punctuation stays out of scope |
| Case-only differences are neutral (Gloria, v1.2) | Guess capitals freely | Not exploitable as tested: lower-casing a line costs 0.75–0.92 because correct words then count as broken | Keep |
| Deleting a hard word | Drop damaged names instead of repairing them | No: scores −0.03, below copying | Keep |

**What this audit cannot show.** The probes are constructed, not learned: a policy could find
other answers. Answers above 0.75 that break the task were looked for by one independent check
(further from the expert line than the OCR); Gloria's confirmation of 30 blind candidates is pending
(`training/results_test/hacking_review_gloria.xlsx`) and the confirmed rate will be added to
`TRAINING_REPORT.md` section 6.
