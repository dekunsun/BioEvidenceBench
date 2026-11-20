# Decision memo: where should the next investment in BHL data extraction go?

*Draft for Gloria's review, 2026-11-20 (revised after the exploratory runs). The table "What the
pre-registered test says" comes from the frozen run (`FREEZE.json`); "What the follow-up
experiments add" was decided after unsealing and is exploratory (`DEVIATIONS.md`). Per book,
95% page-bootstrap intervals. A pilot on 16 pages of two books.*

**To:** a team deciding how to spend the next unit of effort on extracting structured data
(names, people, places, institutions, dates) from historical biodiversity literature.
**From:** Gloria Sun. **Evidence:** BioEvidenceBench V1: 16 locked test pages from Butler 1907
(birds) and Reeve 1849 (shells), each read as legacy BHL OCR, 21 modern OCR outputs, the page
image and an expert transcription; Claude Opus 5.5 and Gemini 4 Carbon; gold labelled before
any model output.

## Recommendation

1. **Don't buy more character accuracy; buy name accuracy.** Choose or tune OCR on how many
   *entity names* it keeps intact on a small labelled sample, not on page CER: across 22 OCR
   versions page CER barely predicts extraction, entity preservation predicts it almost exactly.
2. **Re-OCR is not the only route to clean names.** On these books an LLM that keeps a verbatim
   quote but also gives a repaired reading brings legacy OCR from 0.60 to 0.96 (Butler), and
   reading the page image directly matches modern OCR + extraction (0.96 / 0.98). Pick between
   re-OCR, repair and image reading on cost and on what else the text is for (search, display),
   not on extraction accuracy. Prefer OCR whose errors are *visible*: garbled text is repairable,
   fluent misreadings (`Linnaeus` for `Linnæus`) are not.
3. **Fund LLM-assisted entity resolution, then a taxonomy policy.** A plain GBIF lookup loses
   four in ten correct names; an LLM linker recovers most of them (0.59 → 0.91). What is left is
   taxonomic judgment (which species concept, which checklist), a decision for curators, not an
   engineering task.
4. **Route human review by text quality, with mechanical checks; never skip it on model
   agreement.** On legacy OCR two cheap checks catch half the errors in a quarter of the output;
   two models agreeing catches 7%. On clean text errors are rare and need sampling, not flags.
5. **Keep evidence on (line + verbatim quote; repaired values marked) as the audit trail.**
6. **Use the cheapest model that is good enough for extraction.** Haiku 5.5 is within a few
   points of Opus 5.5 and Fable 5.2 at about 1/15 of Opus's cost; the model gap (≤0.05) is small
   next to the OCR gap (~0.35). Spend the difference on entity resolution and review.

## What the pre-registered test says

| Option | Finding | Verdict |
|---|---|---|
| Better OCR | Value F1 (Opus, with evidence), legacy → modern → expert: **Reeve 0.64 → 0.98 → 0.98**; Butler 0.60 → 0.95 → 0.98. Reeve: +0.34 [0.25, 0.46] from re-OCR, +0.005 [−0.015, 0.03] from expert transcription. On legacy OCR the models find the right place (lenient F1 0.93–0.97) but copy the misread text | supports |
| Better extraction | On the expert text both LLMs are at 0.98 value F1. The rule baseline (gnfinder + regex) is far behind on names (taxon value F1 0.64 Butler, 0.54 Reeve) and people. The few extraction errors left are mostly scope: broad vernacular words (insects, moss, pine) added to the guide after the prompt was fixed | LLM beats rules: mostly supports |
| Automated verification | Requiring a verbatim quote changed recall by −0.015 to +0.007. Neither condition produced any unsupported value, because values are always sliced from the source | no cost; no measurable benefit |
| Prioritised review | 99–100% of predictions flagged as "both models agree": too few left to compare. Errors inside the flagged set: legacy OCR **50 (Butler) / 75 (Reeve)**, modern OCR 6 / 5, expert 3 / 4 | too few to compare; agreement is not correctness |
| Entity resolution (plain GBIF lookup) | Butler, 34 gold-resolved names: **14 lost at linking vs 0 before it** on the expert text (difference 0.41 [0.25, 0.60]); 13 vs 1 on modern OCR. The 14: old genera and synonyms (`Aedon`, `Lusciniola`, `Munia`), names now treated as races of another species (`Motacilla beema`), abbreviated genera whose full name is not on the page (`M. minuta`), a homonym (`Passer`), one typo in the expert transcription | supports |
| Error analysis | Of 163 gold mentions wrong in some version, 151 are OCR-sensitive (130 only that), 17 extraction/reasoning, 32 ambiguous/mixed; of 20 extra outputs, 18 OCR-sensitive (tagged by Gloria; several tags allowed) | — |

## What the follow-up experiments add (exploratory)

| Question | Finding |
|---|---|
| Which OCR measure predicts extraction? | 22 OCR versions: value F1 vs gold-entity preservation, Spearman **0.95 / 1.00**; vs page CER **−0.07 / −0.62**. Some OCR models with page CER under 0.5% keep only 57–80% of Butler's names |
| Better linker | LLM linker: link recall **0.59 → 0.91** (expert), **0.12 → 0.71** (legacy OCR); GBIF with an animal hint: 0.62 |
| LLM repair instead of re-OCR | Legacy OCR **0.60 → 0.96** (Butler), **0.64 → 0.91** (Reeve); 92% of changed values right; on the expert text 3 of its 4 changes fixed the transcription's own typos. Fluent OCR errors (DeepSeek-OCR-2) stay: 0.81 / 0.87 |
| No OCR at all | Page image only: **0.96 / 0.98** (value-bag scoring) |
| Review signals | Legacy OCR: OCR-junk + no exact GBIF match flag 25% of outputs, catch 55% of errors (precision 0.77); model disagreement 7% |
| Cheaper / stronger model | G1 on dots.mocr: Haiku 5.5 0.94 / 0.95, Sonnet 5.5 0.93 / 0.97, Opus 5.5 0.95 / 0.98, Fable 5.2 0.96 / 0.98; on legacy OCR all 0.58–0.65. Cost per 1,000 page-passes (sync): Haiku $1.5, Sonnet $10, Opus $23, Fable $43 |
| Is repair memory? | Visible typos in gold names put back 65–68 of 69 times (Opus, Fable); fluent epithet swaps put back **0 of 29** by every model: repair reacts to visible errors, no sign of page memory |
| Image grounding | Image-only with boxes: values 96–98% right, but boxes on the right word only 67% (Butler) / 40% (Reeve): take Level 3 from OCR word coordinates |

**Answer to the main question, for these two books:** with an LLM in the loop, OCR stops being
the bottleneck early: either modern OCR, an LLM repair of legacy OCR, or reading the image gets
extraction to about 0.95. What then limits trustworthy data is (a) fluent OCR errors no one can
see, (b) entity resolution, where the remaining errors are taxonomic judgment, and (c) the
definition of what counts as a mention. There is no single CER threshold; entity preservation is
the measure to watch.

## What this does not show

- Two books and 16 pages: a direction for a pilot, not a rule for all of BHL. Book and OCR
  quality are confounded, so results are per book.
- The follow-up experiments were designed after seeing the test results; they need a fresh test
  set before they count as findings.
- The books are public. Repair and image reading may be helped by the models having seen them;
  a probe found no sign of page memory in repair, which does not prove there is none. Material
  outside the training data is the real test (the PCAS case is public too).
- One gold labeller; a second labeller on 5 pages agreed at 0.90 (exact) / 0.95 (overlap).
- Entity resolution was measured on birds only (Butler, 34 gold-resolved names). Shell names
  (Reeve, 56 distinct names) were left for the next round: building their gold links by hand would
  take 2-3 hours, and the pre-registered linking question is already answered on Butler. Whether
  the LLM linker's gain holds for molluscs, where synonymy is heavier, is untested.
- No review-time study: review workload is counted in mentions, not minutes.

## Cost

Per page per pass, Opus 5.5: plain extraction about $0.01 (batch) / $0.02 (sync), LLM repair
$0.05, image only $0.04 (sync). Gemini 4 Carbon about $0.03 per request (sync). Whole project
about $45 of API spend, including follow-up runs with four Claude models and a whole-book run. The main cost was human: labelling 22 pages, Butler's name links and the
error analysis.
