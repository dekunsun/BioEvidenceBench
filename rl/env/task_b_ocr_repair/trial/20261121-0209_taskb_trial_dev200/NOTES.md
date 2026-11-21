# Notes on the 200-item dev trial (Claude, 2026-11-21)

200 dev items (40 per training book; 164 with 2–5 damaged words, 36 clean; the five pilot pages left
out), prompt `repair_v2`, Reward v1.2 with typographic apostrophes folded, K = 8, Haiku 5.5 and Opus
5.5 at effort low. 3,200 calls, all answered, all `end_turn`. **$4.236** (Opus $4.138, $0.0026 per
call; Haiku $0.098).

## Within-group signal

| | Items with unequal rewards | among format-valid answers only | 2–5 damaged | clean | pass rate in (0.1, 0.9] |
|---|---|---|---|---|---|
| Haiku 5.5 | 32% | 27% | 37% | 8% | 12% |
| Opus 5.5 | 24% | 23.5% | 28% | 6% | 15% |

5% of Haiku's items have signal only because some answers broke the format (reasoning written into
the reply: 139 answers, 9%, 88% of them starting "Wait", "Note" and the like); that signal would teach
format, not repair. Per book, Piscium gives the most signal (Haiku 53%, Opus 43%) and Butler the
least (8%, 13%): Butler's OCR is good, so most items are all-pass.

## Never passed by Opus (66 of 200)

Read by hand and counted by rule. **Data, not the model (16 items):**
- 10: a damaged word has **no OCR text at all** (Reeve index page numbers lost with the column,
  Chitinskelett abbreviations such as `Sca =` missing). Not repairable from the input. 103 dev
  units (Reeve 76, Chitinskelett 21, Trudy 5, Piscium 1).
- 4: **fractions**: the transcription writes `31/2‴` for 3½ and `2/3`; Opus writes `3½`, `⅔`, `²/₃`.
  9 dev units (Trudy).
- 2: **typographic hyphen U+2010 inside a word** (`HOUSE‐SPARROW`), the same kind of glyph as the
  apostrophe. 13 dev units.

**Reference errors found while reading** (at least 5; the rule cannot find these): `Deny` for Derry
(Butler), `evanesceus` (Reeve), `Iaudabili` with capital I (Piscium), `Stauding er` split (Trudy),
`schwârzlich` for schwärzlich (Trudy). Found by reading model outputs, so the list is biased towards
what models get right; only a check against the scans can confirm them.

**The rest (about 50)** are real limits: accents the OCR dropped and the model did not restore
(`minùs`, `admodùm`, `aliásque`, `pallidè`, `variegatâ`), hard abbreviations (`Pso`, `Prtg`), wrong
guesses on badly damaged Latin, and changes to words the OCR had right (`A der Nerv` → `4 der Nerv`).
These are the items a trained model could improve on.

## Correction found afterwards (2026-11-21)

The context lines in these prompts were the expert lines numbered one above and one below. The
transcription numbers blank lines and short captions too, so for some items a context line was
`(none)` although the page had text there. `with_context` now takes the nearest line with OCR text;
the runs above are kept as they were sent. The pilot had the same setting.
