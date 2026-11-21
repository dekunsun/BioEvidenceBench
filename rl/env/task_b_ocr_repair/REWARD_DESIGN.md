# Task B reward design (Reward v1.2)

*Task B: repair one line of legacy OCR so it matches the expert transcription, changing only
recognition errors. Implementation: `src/rl_task_b.py`. Fixed unit tests:
`tests/test_rl_task_b.py` (61 tests). Decisions: Gloria, 2026-11-20. The coefficients are a
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
- **N** (v1.2): reference words the OCR has with the right letters in another case only (small
  caps printed, `BULIMUS` in the transcription, `Bulimus` in the OCR). Neutral: see section 4a.

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
- **Typographic apostrophes folded** (U+2019 ’ and U+2018 ‘ → `'`; Gloria, 2026-11-21, after the
  step 5 pilot): the transcription types `Canary’s` where the OCR reads `Canary's`.
- **Typographic hyphen inside a word** (U+2010, U+2011 between letters, `HOUSE‐SPARROW`) equals `-`
  (Gloria, 2026-11-21). A hyphen at the end of a line is left as it is.
- **Fractions are not converted in any text.** When scoring, an answer's fraction character or
  superscript/subscript form (`3½`, `⅔`, `²/₃`) is accepted as the reference's `31/2` or `2/3` only if
  the reference has exactly that form, whole number included (`accept_fractions`). A different value
  is never made equal (Gloria, 2026-11-21: accept clearly equivalent forms; no global conversion).
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

## 4a. Case (v1.2, Gloria 2026-11-20)

The transcriptions of Butler and Reeve write small-capital headings in capitals; the OCR reads them
as Title case. Case-only differences were 14% of Reeve's damaged words and 8% of Butler's. They are
a transcription convention, not recognition errors, and the OCR gives no evidence for them: a model
rewarded for them would learn to guess capitals.

| OCR | Reference | Treatment |
|---|---|---|
| `Bulimus nimbosus` | `BULIMUS NIMBOSUS` | both words neutral (N) |
| `Bulimus nimbosus` | `BULIMUS nimbosus` | `BULIMUS` neutral, `nimbosus` correct |
| `Bulimus nimbosus` | `BULIMUS nimbosns` | `BULIMUS` neutral, `nimbosns` damaged (real spelling) |
| `Species` | `ſpecies` | damaged: not a case difference (long-s rule, section 4) |

- **Neutral is not free.** A neutral word earns no repair credit, and any case of its letters is
  accepted; changing its letters (`Bulimus` → `Bulinus`), deleting it or replacing it is a broken
  word (−0.5); writing it twice is an inserted word (−0.25).
- A **damaged** word whose OCR case pattern differs from the reference (UPPER vs Title or lower)
  is repaired by the right letters in any case. Every other word is compared exactly, so changing
  the case of a word the OCR had right is a broken word.
- Comparison uses `lower_keep`: lower case one character for one, ſ never folded. `str.casefold()`
  is not used anywhere because it turns ſ into s. The original characters are always kept.
- Alignment ignores case (it only finds positions); pairing an expert line with OCR uses
  case-insensitive similarity.
- Reported separately, not in the reward: `case_only_words`, `case_accuracy` (share of neutral and
  case-differing damaged words the output writes in the reference's exact case) and
  `exact_repair_rate` (repaired / damaged, unweighted, neutral words not counted). The
  case-only mismatch rate per book is in `build/STATS.md`.

## 4b. References that cannot be targets (v1.2)

- *Piscium querelae*'s transcription types ligatures as MUFI private-use code points. Those whose
  reading is clear from the words they occur in are folded like U+FB00–FB06: U+EADA ſt, U+EBA2 ſi,
  U+EBA6 ſſ, U+EBA7 ſſi, U+EEC5 ct (e.g. `e`+U+EADA = `eſt`, `fo`+U+EBA7+`libus` = `foſſilibus`).
- A reference line that still holds U+FFFD (Greek in *Piscium*, ♂ and fractions in Butler's plate
  captions) or an unidentified private-use character (U+EFA1, U+F4F9, U+F1AC, U+F519, U+F50E) is
  invalid: no output can match it.
- Engraved imprints and plate captions whose OCR and transcription are both unreliable are set
  aside (`exclusions.csv`, with reasons). Readable plate captions stay, and heavy OCR damage alone
  is never a reason to set a line aside: badly damaged lines with a reliable reference are the most
  useful training items. Every line set aside is kept with its page, line and reason
  (`set_aside.jsonl`, `build/set_aside_summary.csv`) as a later hard-case set.
- **OCR deletions** (a damaged word with no OCR text at all; Gloria, 2026-11-21). Judged only from
  what the model is shown, never from whether a model failed:
  - A deletion means no letter or digit at all in the OCR between the neighbouring aligned words; a
    word read wrong (`1` as `l`) is a substitution and is scored as damage, not set aside.
  - Context is the nearest line above and below on the same page that has OCR text.
  - *recoverable deletion*: the word (3 characters or more, not a number) stands in those context
    lines, or it is the line's number in an explicit sequence (n−1 before, n+1 after). Kept and marked
    (`recoverable_deletion`); reported separately. Repairing deletions is part of OCR repair.
  - *unrecoverable*: anything else (a Reeve index page number lost with its column). Set aside: the
    reward must not encourage the model to supply historical text from general knowledge.
- **Suspected reference typos** (`reference_errata.csv`): set aside until Gloria has checked each
  against the scan; `confirmed` stays set aside, `not_typo` comes back.
- Also set aside: lines with a word mixing Latin and Cyrillic letters (Trudy's transcription), and
  index and contents lines with leader dots (Gloria, 2026-11-21; `LEADERS` in `src/rl_task_b.py`),
  whose OCR drops the page references or reads the next column.

## 5. Diagnostic fields (returned with every reward)

`reward, reward_reading, format_valid, format_reason, integrity_valid, alignment_valid, clean_line,
damaged_words, repaired_words, scientific_name_damaged, scientific_name_repairs, correct_words,
preserved_correct_words, damaged_correct_words (B), extra_words (I), penalty,
weighted_repair_rate, cer_diagnostic, case_only_words, case_words, case_accuracy,
exact_repair_rate`. If training raises the reward while behaviour worsens, these
show whether names improved, ordinary words were sacrificed, or the scorer was exploited.

## 6. Rules fixed by unit tests

Each line of `tests/test_rl_task_b.py`: perfect = 1; OCR unchanged = 0 on damaged lines and 1 on
clean lines; the worked example; fixed penalties for a broken and an inserted word; a duplicated
word is not rewarded twice; a wrong repair is a substitution, not an insertion; OCR fragments kept
are not penalised again; the right word written next to the damaged one is not a repair; eight
format errors; the integrity check; ligature folding; æ kept; the long-s table; clipping at −1;
v1.2: MUFI folding; unreadable references marked; case-only words neutral in any case; a neutral
word changed, deleted or repeated is penalised; real spelling next to a case difference is damaged;
ſ vs S is not a case difference; changing the case of a correct word is broken; a damaged small-caps
word is repaired by its letters in any case.

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
| v1.2 | 2026-11-20/21 | Typographic apostrophes folded; U+2010 inside words; fractions accepted where the reference has the same form; unrecoverable deletions set aside, recoverable ones marked; suspected reference typos set aside pending check (21st, after the step 5 trials); case-only words neutral (letters must survive); case-free repair of small-caps words; case diagnostics; MUFI ligatures folded; references with U+FFFD or unidentified private-use characters invalid; unreliable imprints and captions set aside | Gloria (from the step 4 audit) |
