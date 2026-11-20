# Task B pilot: steps 1–3 (Reeve, 4 training pages)

*Run 2026-11-20, `python src/rl_task_b_pilot.py`. No model called; cost $0. Pages 8966751–8966754
(Reeve, training split, scan sequence 13–16). Code: `src/rl_task_b.py`.*

## Step 1: do legacy OCR and the expert transcription align?

Each unit is one expert-transcription line (the target) and the legacy OCR aligned to it (the
input), found by character alignment of the whole page and widened to whole words.

- **356 of 357 lines align** (99.7%). The one rejected line had only 64% of its characters aligned:
  the OCR dropped "Species 6." before "(Mus. Cuming.)".
- Rejection rules: under 90% of reference characters aligned; aligned OCR span under 0.6× or over
  1.6× the line's length; or similarity under 0.3. The similarity floor was first 0.5; that
  rejected correctly paired but badly damaged lines such as `BULIMUS.—PLATE I.` read as
  `BULBIL'S.— Plate L`, the most useful lines to train on, so it was lowered to 0.3.
- Damaged words per valid line: 0 → 185 lines, 1 → 102, 2 → 31, 3 → 18, 4 → 8, 5 → 8, 6+ → 4.
  So only 65 of 356 lines (18%) have the 2–5 damaged words the plan prefers for GRPO on these pages;
  Reeve's legacy OCR is good on body text. Other books are expected to be worse; step 4 will show.

**A rule change from the plan: typographic ligatures are folded.** The transcription types
presentation-form ligatures (`diﬀerences`, `ﬁnest`, U+FB00–FB06) where the OCR writes plain letters.
Under "NFC only, exact words" a correct OCR reading counted as damaged and the model would have been
asked to output font glyphs. These seven characters are now folded to letters in every text.
**Letters that are spelling are kept**: æ, œ and the long s ſ. Whether ſ ≡ s should count as correct
is open (none in Butler or Reeve; *Piscium querelae*, 1708, has it).

## Step 2: alignments and Reward v1.0

Both alignments use the scorer's character alignment (`score.char_map`). A reference word is present
in a text only if the aligned characters spell it exactly and it stands as a whole word there.
Alignment A (OCR vs reference) gives the damaged and correct words; alignment B (output vs
reference) gives repairs and breakages. Scientific-name candidates come from gnfinder v1.4.0 on
the expert page (weight 3).

Every call returns the diagnostic fields:
`reward, format_valid, integrity_valid, alignment_valid, clean_line, damaged_words, repaired_words,
scientific_name_damaged, scientific_name_repairs, correct_words, preserved_correct_words,
damaged_correct_words, extra_words, penalty, weighted_repair_rate, cer_diagnostic`.

`extra_words` (added in step 3): words the model inserted that align to no reference word. Junk
already in the OCR input is not counted again, and a wrong attempt at a word is a substitution,
not an insertion.

## Step 3: zero-cost adversarial checks (50 lines: 25 damaged, 10 clean, 5 with æ/œ, 10 with damaged names)

| Output | Cases | Mean | Min | Max | What it shows |
|---|---|---|---|---|---|
| Perfect (the reference) | 50 | 1.000 | 1.000 | 1.000 | ok |
| Return the OCR unchanged | 45 | 0.111 | 0.000 | 1.000 | ok: 0 on every damaged line, 1 on clean lines |
| Empty | 50 | 0 | 0 | 0 | ok: format invalid, flagged |
| Two lines | 50 | 0 | 0 | 0 | ok: integrity invalid, flagged |
| Names left unrepaired | 13 | 0.137 | 0.000 | 0.571 | ok: name weight makes this cost most of the reward |
| Only names repaired | 32 | 0.106 | 0.000 | 0.857 | ok |
| Ligature letters written out (`ae` for `æ`) | 6 | 0.347 | 0.000 | 0.750 | ok: spelling not kept costs credit |
| One correct word changed | 48 | 0.384 | 0.000 | 0.917 | ok, but cheap on long lines (see below) |
| Lower-cased | 28 | −0.178 | −1.000 | 0.909 | ok: heavy damage, penalty capped at λ = 1 |
| "Corrected line: " prefix | 50 | 0.254 | 0.000 | 0.833 | weak on clean lines (see below) |

**Two bugs found and fixed during step 3:**
1. Returning the OCR unchanged first scored as low as −0.67, because OCR fragments of one word
   (`pi/iko//nster` for `pythogaster`) were counted as added words. Fixed: insertions already in the
   input are not counted.
2. A wrong attempt at a word was penalised twice (no repair credit, and again as an added word).
   Fixed: added words are found by alignment, so a substitution is not an insertion.

## Open design questions (for Gloria; plan 6.3)

1. **Penalty normalisation.** The penalty is λ·min(1, B/|D|) on damaged lines and B/|C| on clean
   lines. Breaking one correct word therefore costs a lot on a line with one damaged word (up to
   the whole reward) and little on a line with many; on a clean 12-word line an added two-word prefix
   costs only 0.17 (reward 0.83). Options: keep it; normalise by all words in the line on both kinds
   of line; or add a fixed cost per inserted word.
2. **Long s.** Count `ſ` read as `s` as correct or as damaged?
3. **Reward range.** With λ = 1 the reward runs from −1 to 1. GRPO normalises within each group, so
   this is fine for training; it only matters if rewards are compared across lines.

## Next (step 4)

Build all training and development units for the five training books (Cuvier untouched), report
per-book alignment and damage statistics, and audit 100 pairs across books, languages and error
types (Claude), 30 of them also checked by Gloria.
