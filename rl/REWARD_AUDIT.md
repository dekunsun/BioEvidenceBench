# Reward audit

Where the rewards used in `rl/` can be gamed, how a policy could exploit them, and what was fixed.
Part 1 covers the frozen extraction scorer (used by task A). Part 2 will cover task B's
Reward v1.0 (OCR line repair) once it is built.

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

## Part 2: task B Reward v1.0

To do (plan section 6.5).
