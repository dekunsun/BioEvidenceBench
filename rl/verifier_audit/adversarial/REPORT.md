# 2A: Attacking the frozen scorer

*rl/ module 2A (`rl/PLAN_zh.md`, section 4). Run 2026-11-20 with `python src/rl_attack_scorer.py`
and `--patched`. No model was called; cost $0.*

## What was done

68 adversarial answers, each a model answer for one of the 16 old test pages (now development data
for `rl/`; this is an audit, not training). A "clean" answer quotes every single-line gold mention
correctly; each attack changes one target mention or adds outputs in one way. Every answer goes
through the frozen pipeline unchanged: `locate.locate_all` → `score.char_map` / `map_span` →
`score.match_page`. Three conditions as in the study: G1 (line + verbatim quote, value sliced from
the source by code), G0 (value only, located in the source by code), G2 (quote for location, the
model's `reading` used as the value).

Verdicts compare the scorer's behaviour with what the guide implies. The `expected` column is
Claude's reading of ANNOTATION_GUIDE v0.10 and of score.py's documented rules, **for Gloria to
review**; it is not a gold label. Every case, its answer and its result are in `cases.csv`
(frozen rules) and `cases_patched.csv` (patched rules).

## Results

| Category | Cond. | Frozen scorer | Patched |
|---|---|---|---|
| 1 Whole line quoted as the mention | G1 | ok 4 | ok 4 |
| 2 Scattershot: every capitalised word as a taxon | G1 | ok 4 (page value F1 1.000 → 0.65–0.78) | ok 4 |
| 3 Edge punctuation, case, Markdown | G2 | by design 9, **false negative 3** | by design 12 |
| 4 Ligatures written out (`Linnaeus` for `Linnæus`) | G2 / G0 / G1 | ok 3 / **finding 1**, ok 2 / **finding 1**, ok 2 | ok 9 |
| 5 One letter changed | G2 / G0 / G1 | ok 3 / **finding 3** / **finding 3** | ok 9 |
| 6 Right quote, wrong field | G1 | ok 3 | ok 3 |
| 7 Right text at a non-gold occurrence | G1 | ok 3 | ok 3 |
| 8 Empty answer | G1 | **finding 3** | **finding 3** |
| 10 Only optional (later-rule) rows, sensitivity mode | G1 | ok 3 (no gain, no penalty) | ok 3 |
| 11 Name broken across lines: first line only / whole | G1 | ok 6 | ok 6 |
| 12 The scan's reading where the transcription has a typo | G2 | ok 2 | ok 2 |
| 13 Same mention twice | G1 | ok 3 (one TP, one FP) | ok 3 |
| 14 Reading with the author appended | G2 | ok 3 | ok 3 |
| 15 Legacy OCR: faithful copy of a misread / corrected quote | G1 | ok 4 | ok 4 |
| **All** | | **ok 45, by design 9, finding 11, false negative 3** | **ok 53, by design 12, finding 3** |

## Findings

**1. The value is blind to quote fidelity in G0 and G1 (8 cases).** When the model's quote or
value is wrong but close (one letter changed, a ligature written out), the locator still finds the
place by fuzzy match (`fuzzy` in G0, `silent_correction` in G1) and the code slices the *correct*
source text. The model gets full credit for text it did not reproduce. For the study this is
intended: the database value comes from the source, and RQ3 counts silent corrections separately.
**As an RL reward it is a hole:** a policy would never be penalised for an unfaithful quote, so the
evidence requirement would not shape behaviour.
- *Effect on reported results: none.* In the frozen test runs (Opus and Gemini, G0 and G1, all
  text versions) the locator never fell back to `fuzzy`, `silent_correction` or `case_variant`;
  every located mention was `exact`, `cross_line` or `layout_variant`.
- *Patch (rl/ only):* for those three statuses, use the model's own text as the value
  (`score_patched.gate_value`). All 8 cases become ok.

**2. Quotation marks at the edges of a value are not stripped (3 cases, G2).** `norm_value` maps
curly quotes to straight ones but strips only ` .,;:()[]` at the edges, so a reading written as
`"BULIMUS CHILENSIS"` is not credited.
- *Effect on reported results: none.* 0 of 9,239 readings in the exploratory G2 runs are wrapped in
  quotation marks.
- *Patch:* also strip `"` at the edges (`score_patched.norm_value_patched`).

**3. An empty answer scores like "found nothing" (3 cases).** `{"mentions": []}` gets 0 true
positives and every gold mention as a false negative, exactly like a model that read the page and
found nothing. The scorer cannot tell a refusal or a silent failure from a real negative; on a
page with no gold mentions, an empty answer and a correct answer are identical. In the study this
is handled outside the scorer (request outcome tables count API and parse errors; the Gemini empty
answer was found by checking `parsed` and token counts).
- *For the environment:* the reward function must return a flag (`info["empty"]`) and the run must
  count empty answers separately; on pages that do have gold mentions an empty answer is a failure,
  not a negative.

**By design, kept (9 → 12 cases).** Values are compared case-insensitively and after stripping edge
punctuation, Markdown emphasis and line-end hyphenation. That suits value extraction (modern OCR
writes Markdown; the case of a printed small-capitals heading is not information). It does **not**
suit a transcription-fidelity reward, which is why task B uses exact NFC comparison instead.

## What held

Quoting a whole line, field mismatches, wrong occurrences, duplicates and appended authors all lose
credit; scattershot output costs 22–35 points of page F1; names broken across lines get credit only
when quoted whole; the scan's reading is accepted where the transcription has a typo; on legacy OCR
a faithful copy of a misread name is not credited and a "corrected" quote that is not in the OCR
line is rejected as invalid evidence; outputting only optional rows gains nothing.

## Limits

- `expected` is a reading of the guide, not an independent label; Gloria reviews it and may add
  attacks.
- Cases are built from the 16 old test pages and their gold; they test the scorer's rules, not a
  model.
- The attacks are hand-designed (68 cases); they are a checklist, not an estimate of how often a
  trained policy would find each hole. Module 7 (training) tests that directly.
