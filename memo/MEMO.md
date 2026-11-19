# Decision memo: where should the next investment in BHL data extraction go?

*Draft for Gloria's review, 2026-11-20. From the frozen, pre-registered test run (`FREEZE.json`);
numbers are per book with 95% page-bootstrap intervals. A pilot on 16 pages of two books.*

**To:** a team deciding how to spend the next unit of effort on extracting structured data
(names, people, places, institutions, dates) from historical biodiversity literature.
**From:** Gloria Sun. **Evidence:** BioEvidenceBench V1: 16 locked test pages from Butler 1907
(birds) and Reeve 1849 (shells), each read as legacy BHL OCR, modern OCR (dots.mocr) and an
expert transcription; Claude Opus 5.5 and Gemini 4 Carbon; gold labelled before any model output.

## Recommendation

1. **Re-OCR first, then stop.** Modern OCR recovers almost everything legacy OCR loses;
   expert transcription adds little on top. Do not fund transcription to get better extraction.
2. **Put the next unit of effort into entity resolution.** Once the text is good, the largest
   loss is linking extracted names to a taxonomic database: a plain GBIF lookup loses about
   four in ten names that extraction got right.
3. **Keep evidence (line + verbatim quote) on by default** as an audit trail: it cost no recall.
   Do not expect it to fix anything by itself; there was nothing for it to fix here.
4. **Do not use two-model agreement to skip review.** The models agree on nearly everything,
   including their mistakes on bad OCR. Route review by text quality instead.

## What the evidence says

| Option | Finding | Verdict (pre-registered) |
|---|---|---|
| Better OCR | Value F1 (Opus, with evidence), legacy → modern → expert: **Reeve 0.64 → 0.98 → 0.98**; Butler 0.60 → 0.95 → 0.98. Reeve: +0.34 [0.25, 0.46] from re-OCR, +0.005 [−0.015, 0.03] from expert transcription. On legacy OCR the models find the right place (lenient F1 0.93–0.97) but copy the misread text | supports |
| Better extraction | On the expert text both LLMs are at 0.98 value F1. The rule baseline (gnfinder + regex) is far behind on names (taxon value F1 0.64 Butler, 0.54 Reeve) and people. The few extraction errors left are mostly scope: broad vernacular words (insects, moss, pine) added to the guide after the prompt was fixed | LLM beats rules: mostly supports |
| Automated verification | Requiring a verbatim quote changed recall by −0.015 to +0.007. Neither condition produced any unsupported value, because values are always sliced from the source | no cost; no measurable benefit |
| Prioritised review | 99–100% of predictions flagged as "both models agree": too few left to compare. Errors inside the flagged set: legacy OCR **50 (Butler) / 75 (Reeve)**, modern OCR 6 / 5, expert 3 / 4 | too few to compare; agreement is not correctness |
| Entity resolution | Butler, 34 gold-resolved names: **14 lost at linking vs 0 before it** on the expert text (difference 0.41 [0.25, 0.60]); 13 vs 1 on modern OCR. Of the 14: 8 matched only at genus, 3 to the wrong taxon, 3 not found. What they are: old genera and synonyms (`Aedon`, `Lusciniola`, `Munia`), names now treated as races of another species (`Motacilla beema`, `M. melanocephala`, `M. cinereocapilla`), abbreviated genera whose full name is not on the page (`M. minuta`), a homonym (`Passer`) and one typo in the expert transcription (`nontifringilla`). Subfamily names were not scored (no such rank in the GBIF backbone) | supports |
| Error analysis | Of 163 mentions wrong in some version, 151 are OCR-sensitive (130 only that), 17 extraction/reasoning, 32 ambiguous/mixed (tagged by Gloria) | — |

**Answer to the main question, for these two books:** OCR stops being the main bottleneck at
modern-OCR quality (page CER around 1%); from there, entity resolution is the limiting step.
There is no single CER threshold in this data; the jump is between legacy and modern OCR.

## What this does not show

- Two books and 16 pages: a direction for a pilot, not a rule for all of BHL. Book and OCR
  quality are confounded, so results are per book.
- The linker is deliberately naive (name only, no hints). A better linker could close much of
  the linking gap; that is the experiment to fund next, not a reason to skip it.
- One gold labeller; a second labeller on 5 pages agreed at 0.90 (exact) / 0.95 (overlap).
- No review-time study: review workload is counted in mentions, not minutes.
- The texts are public and may be in the models' training data; values are sliced from the
  input, so memorisation cannot silently correct a misread name.

## Cost

API cost per page for all eight conditions (4 text versions × with/without evidence): Opus
$0.09 (batch), Gemini $0.26 (sync, prices valid to 2026-11-30). Whole project about $15 of a
$15–30 budget. The main cost was human: labelling 22 pages, Butler's name links and the error
analysis.
