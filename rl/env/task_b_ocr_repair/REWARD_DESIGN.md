# Task B reward design (Reward v1.1)

*Task B: repair one line of legacy OCR so it matches the expert transcription, changing only
recognition errors. Implementation: `src/rl_task_b.py`. Fixed unit tests:
`tests/test_rl_task_b.py` (28 tests). Decisions: Gloria, 2026-11-20. The coefficients are a
first experimental setting, not validated optima; they are checked on development data before
any training run.*

## 1. What is rewarded

The unit is the **word**, not the character. The first BioEvidenceBench study found that page CER
does not predict whether scientific names survive OCR (Spearman −0.07 / −0.62) while name
preservation does (0.95 / 1.00); one wrong letter barely moves CER and makes a name useless. CER is
reported as a diagnostic only.

Sets per line, from **alignment A** (OCR input vs reference):
- **D**: reference words the OCR got wrong (damaged); weight wᵢ = 3 for scientific-name candidates
  (gnfinder v1.4.0 on the expert page), 1 otherwise.
- **C**: reference words the OCR got right.

From **alignment B** (model output vs reference):
- a damaged word is **repaired** if the output has it exactly, as a whole word, at the aligned place,
  **and the damaged OCR token is gone** (writing the right word next to the wrong one is not a repair);
- **B** = words of C the output changed or deleted;
- **I** = words the output inserted that align to no reference word, not counting insertions already
  present in the OCR input. Alignment is one-to-one, so a word written twice leaves one insertion.

## 2. Formula

Damaged line (D not empty):

```
R = clip( Σ_{i∈D} wᵢ·repaired(i) / Σ_{i∈D} wᵢ  −  0.5·B  −  0.25·I ,  −1, 1 )
```

Clean line (D empty):

```
R = clip( 1  −  0.5·B  −  0.25·I ,  −1, 1 )
```

**Fixed penalty per action** (replaces v1.0's λ·min(1, B/|D|)): the same damaging action costs the
same on every line, whatever its length or number of damaged words. Under v1.0, breaking one
correct word cost the whole reward on a line with one damaged word and almost nothing on a line
with many, and a two-word prefix on a clean 12-word line cost only 0.17.

Worked example (reference `Muscicapa parva recorded in specimens`, OCR `Muscicapa parua recorded
in specirnens`; `parva` weight 3, `specimens` weight 1):

| Output | R |
|---|---|
| neither repaired (the OCR unchanged) | 0.00 |
| only `specimens` repaired | 0.25 |
| only `parva` repaired | 0.75 |
| both repaired | 1.00 |
| both repaired, one correct word broken | 0.50 |

## 3. Hard gates (reward 0, flagged, not scored as insertions)

| Gate | Rule | Field |
|---|---|---|
| Format | empty; several lines; a commentary prefix (`Corrected line:`, `Here is …:`, `Output:` …); the whole line wrapped in Markdown or quotation marks (`*…*`, `` `…` ``, ```` ```…``` ````, `"…"`) unless the reference itself is | `format_valid`, `format_reason` |
| Integrity | output length outside 0.5–1.5 × the reference | `integrity_valid` |
| Alignment | under 50% of reference characters align to the output | `alignment_valid` |

Ordinary extra words are not format errors: they cost 0.25 each.

## 4. Characters

- **NFC only, never NFKC.**
- **Typographic ligatures folded** (U+FB00–FB06: ﬀ ﬁ ﬂ ﬃ ﬄ ﬅ ﬆ → letters) in every text. They are
  glyphs, not spelling: the transcription types `ﬁnest` where OCR writes `finest`.
- **Spelling letters kept**: æ and œ (`Linnaeus` for `Linnæus` is a broken word), and the long s ſ.
- **Long s, two measures.** The main reward keeps the transcription's glyph (`species` for `ſpecies`
  is wrong). `reward_reading` is the same reward with ſ and s treated as one letter, to show how much
  of a score difference is the glyph alone. Alignment always lets ſ align with s (to find the right
  position); only scoring distinguishes them.

| Reference | Output | Main reward | Reading metric |
|---|---|---|---|
| `ſpecies` | `ſpecies` | right | right |
| `ſpecies` | `species` | wrong | right |
| `ſpecies` | `fpecies` | wrong | wrong |
| `Linnæus` | `Linnaeus` | wrong | wrong (æ is spelling) |

Long s in the expert transcriptions (counted 2026-11-20): *Piscium querelae* (1708) 912 on 40 of 60
pages; Trudy 2; Das Chitinskelett 1; Butler, Reeve, Cuvier 0. Before task B uses *Piscium*, its 20
pages without ſ are checked: sparse pages, or an inconsistent transcription? If the transcription
uses s where the print has ſ, the reference is not "corrected" from the print's date.

## 5. Diagnostic fields (returned with every reward)

`reward, reward_reading, format_valid, format_reason, integrity_valid, alignment_valid, clean_line,
damaged_words, repaired_words, scientific_name_damaged, scientific_name_repairs, correct_words,
preserved_correct_words, damaged_correct_words (B), extra_words (I), penalty,
weighted_repair_rate, cer_diagnostic`. If training raises the reward while behaviour worsens, these
show whether names improved, ordinary words were sacrificed, or the scorer was exploited.

## 6. Rules fixed by unit tests

Each line of `tests/test_rl_task_b.py`: perfect = 1; OCR unchanged = 0 on damaged lines and 1 on
clean lines; the worked example; fixed penalties for a broken and an inserted word; a duplicated
word is not rewarded twice; a wrong repair is a substitution, not an insertion; OCR fragments kept
are not penalised again; the right word written next to the damaged one is not a repair; eight
format errors; the integrity check; ligature folding; æ kept; the long-s table; clipping at −1.

## 7. Known limits

- gnfinder's name candidates are noisy; weighted and unweighted (w = 1) rewards are both compared
  in training (plan 6.4), and gnfinder's precision and recall on damaged name words are measured on
  the 22 BioEvidenceBench sample pages (diagnostic only).
- Punctuation is not scored in v1.
- The commentary-prefix pattern is a list; new forms found in model trials are added and tested.
- `0.5` and `0.25` are first settings; they are checked on development data before training.

## 8. Version history

| Version | Date | Change | Decided by |
|---|---|---|---|
| v1.0 | 2026-11-20 | Weighted damaged-word repair minus λ·min(1, B/max(1,|D|)); clean lines 1 − B/|C| | Gloria (from an external review) |
| v1.1 | 2026-11-20 | Fixed penalties 0.5 per broken word, 0.25 per inserted word, clipped to [−1, 1]; hard format gate; repair requires the damaged token to be gone; long s kept in the main reward plus a reading metric; ligature folding | Gloria |
