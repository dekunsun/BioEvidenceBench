# Deviations from the pre-registration

`PREREGISTRATION.md` is frozen (`FREEZE.json`) and is never edited after the freeze. Every change
to the plan made after the test pages were unsealed is recorded here, newest first, with the
reason. Results affected by a deviation say so where they are reported.

| Date | Section | Plan said | What was done | Reason / decided by |
|---|---|---|---|---|
| 2026-11-20 | 5. Error analysis | "Every false positive and false negative of Opus G1 on the test pages is tagged by Gloria" | Tagging is done per case, not per scorer row: a misread mention (one FN + one FP in the scorer) is one row, and a gold mention is one row across the four text versions (`src/make_error_sheet.py`). For group A (wrong only on legacy OCR, 137 of 163 gold-mention rows) the tag "OCR-sensitive" is preset by its definition (the result changes when only the OCR input changes) and marked as a preset; Gloria spot-checks these rows and may add or change tags. Every other row is tagged by her without presets. A factual column per OCR version shows what the model's input held at the gold position | Gloria, 2026-11-20 ("加那一列吧，A组也按规则预设"). The preset follows from the definition, so it does not decide anything a person would decide differently; the spot-check guards against rows with a second cause |
