# Task B step 4: alignment audit (rounds 1 and 2)

*2026-11-20/21. Auditor: Claude (a model family that may later be trained or compared on this task;
Gloria checks 30 pairs independently, `audit_gloria.xlsx`, without Claude's verdicts). No model
was called. Verdicts: `yes` (right pair, usable target), `partly`, `no` (wrong pair or unusable).*

**Automatic coverage is not alignment accuracy.** The build accepts 40,070 of 45,083 lines (89%),
and the pilot aligned 356 of 357 lines; neither number says whether the accepted pairs are right.
That is what these audits measure.

## Round 1: on the first build (100 pairs, `audit_round1/`)

Sampled before the fixes, over similarity buckets (35 at 0.3–0.5, 10 under 0.3, 30 at 0.5–0.8,
25 at 0.8–1.0), every book represented. It found:

| Finding | Effect | Fix |
|---|---|---|
| *Piscium* transcription types ligatures ſt, ſi, ſſ, ſſi, ct as MUFI private-use characters (about 1,160), invisible on screen: `noſtro` looked like `noro` | targets had missing letters | folded to letters (Reward v1.2, 4b) |
| U+FFFD in references (Greek; ♂ and fractions in plate captions) | no output can match | line invalid |
| Small capitals: `BULIMUS NIMBOSUS` in the transcription, `Bulimus nimbosus` in the OCR (14% of Reeve's damaged words) | model would learn to guess capitals | case-only words neutral (Gloria) |
| Similarity was case-sensitive: `FAMILY MUSCICAPIDÆ` / `Family Muscicapid^:` rejected at 0.16 | right pairs lost | pairing ignores case |
| Plate imprints with garbled transcriptions (`Vertagstuchhandliung`) | unreliable target | set aside (`../exclusions.csv`, Gloria's rule) |
| Trudy multi-column lists: 2 of 73 accepted pairs were wrong lines | wrong target | none yet (see below) |

Accepted pairs: 73, of which 2 `no` and 3 `partly`; rejected: 27, of which 4 were right pairs.

## Round 2: on the fixed build (100 new pairs, `audit_sample.csv`)

Same buckets, **no pair from round 1** (the first sampler drew from a fixed window and would have
repeated 34 pairs), drawn uniformly within book × bucket, seed 20261121.

| Similarity | Accepted | yes | partly | no |
|---|---|---|---|---|
| 0.3–0.5 | 11 | 8 | 2 | 1 |
| 0.5–0.8 | 16 | 14 | 2 | 0 |
| 0.8–1.0 | 25 | 25 | 0 | 0 |
| **All** | **52** | **47** | **4** | **1** |

Rejected: 48; 4 of them right pairs (U+FFFD lines, correctly invalid), 23 `partly` (mostly index and
contents lines whose leader dots and page numbers are not in the OCR), 21 wrong pairs, all rightly
rejected, including all 11 Trudy column-list lines in the sample.

**Weighted by where usable lines are** (0.8–1.0: 95.8%, 0.5–0.8: 3.6%, 0.3–0.5: 0.6%), about 0.6% of
usable lines are not clean and 0.06% are wrong pairs. This estimate rests on 0 errors in 50 audited
pairs in the 0.8–1.0 bucket over both rounds: the 95% upper bound for that bucket alone is about 6%,
so the true rate could be several times higher. Gloria's 30 pairs are the independent check.

## What remains

- **Index and contents lines with leader dots** (`.. .. ..`, `- - - -`): the OCR drops the leaders
  and page numbers or reads the next column (round 2: B004, B006, B051). 287 usable lines (Trudy 180,
  Butler 77, Reeve 29, Chitinskelett 1). Not set aside yet: decision for Gloria.
- **Accepted wrong pairs in 0.3–0.5** come from reading order (columns, neighbouring lines): 2 of 33
  audited across both rounds.
- **Unidentified private-use characters** (U+EFA1 in `c?rulescente` and `Sturnid?`, æ or œ;
  U+F4F9, U+F1AC, U+F519, U+F50E) and **Cyrillic look-alikes inside Latin words** in Trudy's
  transcription (60 lines): set aside, not rewritten.
- **Reference typos** (`EnderIein`, `Soweby`) survive where only one word is affected.
