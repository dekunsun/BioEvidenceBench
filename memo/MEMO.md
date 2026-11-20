# Where does a literature-to-data pipeline lose reliability, and where should the next unit of effort go?

*Decision memo, draft for Gloria's review, 2026-11-20. Evidence: BioEvidenceBench V1, a pilot on two
historical books from the Biodiversity Heritage Library (Butler 1907, birds; Reeve 1849, shells) plus
an 8-page botany case (PCAS 1898). Results marked **[pre-registered]** come from the frozen test run
(`FREEZE.json`, 16 locked pages, gold labelled before any model output); results marked
**[exploratory]** were designed after unsealing (`DEVIATIONS.md`) and need a fresh test before they
count as findings. Per book, 95% page-bootstrap intervals where given.*

**To:** a team deciding how to spend the next unit of money or people time on turning historical
biodiversity literature into structured, trustworthy data (names, people, places, institutions, dates).

BioEvidenceBench is a system-level evaluation of **evidence-grounded scientific data extraction**,
not an OCR benchmark: OCR is one step of the pipeline it follows (FineBooks already scores OCR).

## The question is not "which OCR or which LLM scores highest"

A record is only as trustworthy as the weakest step between the printed page and the database row.
This pilot follows one mention through every step and asks where reliability is actually lost, how
much of it, and what it would cost to win it back.

## Bottom line

On these books (English, printed 1849 and 1907), **OCR was the first bottleneck and modern OCR
removed most of it cheaply; after that, the limits were entity resolution and the definition of
what counts as a datum, not extraction.** This does **not** mean OCR investment is finished: other
languages, layouts, print eras, tables, plates and handwritten records may have entirely different
error distributions, and this pilot did not test them. The next unit of effort should go to
(1) measuring, per material type, whether names survive OCR, and re-OCR where they do not,
(2) entity resolution with an LLM linker and a curator-owned taxonomy policy, (3) a written scope for
what the pipeline extracts, and (4) sample-based review. A bigger or more expensive extraction model
is the place *not* to spend.

## Where reliability is lost, step by step

| Step | What we measured | How much is lost here | Can it be won back, and at what cost |
|---|---|---|---|
| **1. Page → text (OCR)** | Extraction on legacy BHL OCR vs modern open OCR vs expert transcription | **Largest loss.** Value F1 Reeve 0.64 → 0.98 → 0.98, Butler 0.60 → 0.95 → 0.98 **[pre-registered]**; 151 of 163 wrong gold mentions are OCR-sensitive (Gloria's error tags) | On these books, yes, cheaply. Modern OCR, an LLM that repairs the OCR while keeping a verbatim quote (0.60 → 0.96 Butler), or reading the page image (0.96 / 0.98) all close most of the gap **[exploratory]**, but they leave different evidence (next section). What remains: *fluent* OCR errors (`Linnaeus` for `Linnæus`) that no later step can see (0.81 / 0.87 even after repair) |
| **2. Text → mentions (extraction)** | LLM vs rule baseline; four Claude models | Small once the text is clean: 0.98 on expert text; rules far behind on names (taxon 0.64 / 0.54) **[pre-registered]**. Model choice moves F1 by ≤0.05; Haiku costs about 1/15 of Opus **[exploratory]** | Already won. Use the cheapest model that is good enough |
| **3. Mentions → evidence (verification)** | Values sliced from the source, model quotes checked character by character | **Costs no accuracy; its value is not visible in these metrics.** Requiring a quote changed recall by −0.015 to +0.007 **[pre-registered]**. Neither arm produced an unsupported value, because in both the value is taken from the source by code (sliced or aligned): the test compared two forms of verification, not verification against none, so it could not show a reduction. This does **not** mean evidence verification has no value. Its value is traceability and audit cost, which accuracy does not measure (next section). Image coordinates drawn by a vision model hit the right word only 67% / 40% **[exploratory]** | Keep it as a design requirement: line + quote on every value, image coordinates from OCR word boxes. Measure its value next round with audit metrics: share of values traceable to the page, reviewer time per value, errors caught with vs without evidence |
| **4. Mentions → entities (resolution)** | Butler names linked to GBIF | **Largest loss on clean text.** A plain GBIF lookup loses 14 of 34 correctly extracted names vs 0 lost before linking (difference 0.41 [0.25, 0.60]) **[pre-registered]** | Mostly. An LLM linker (name + context → accepted name → GBIF) raises link recall 0.59 → 0.91; the rest are taxonomic judgments (which species concept, which checklist) **[exploratory]**. Model choice matters here (Opus 0.91, Haiku 0.76) |
| **5. What counts as a datum (specification)** | Labeller agreement; PCAS adjudication; whole-book spot-check | Two labellers agree 0.90 exact / 0.95 overlap. On PCAS, aligning five boundary conventions (titles, place chains) moves F1 0.83 → 0.94 without any model change. In the whole-book run, 16% of extracted mentions sat on index pages that the guide never defined; once index pages were ruled out of scope, the queue of mentions needing review (no agreement or a failed check) shrank from 1,404 to 555 **[exploratory]** | Yes, cheaply: a written scope (index pages, authorities, broad vernacular words) and one adjudicator. Much of the apparent "model error" is undefined scope |
| **6. Review (human or automated)** | Model agreement as an auto-accept signal; cheap checks; whole-book spot-check | Agreement is not correctness: on legacy OCR 50 (Butler) / 75 (Reeve) flagged mentions are wrong **[pre-registered]**. On modern OCR, 25 of 25 checked Opus outputs outside the sample were correct, and a second model surfaced real misses (10 of 14) **[exploratory]** | Route by text quality: on legacy OCR two mechanical checks catch 55% of errors in 25% of the output; on clean text use random-sample QA (about 30 s per item) and a second model for recall, never agreement-based skipping |

## Same accuracy is not the same evidence

The three routes past bad OCR reach similar value F1, but they do not produce equivalent, auditable
evidence. What an auditor can check, and how much work it takes, differs:

| Route | Value F1 (Butler / Reeve) | Where the value comes from | Text evidence (Level 2) | Image evidence (Level 3) | What an auditor has to do |
|---|---|---|---|---|---|
| Modern OCR + extraction with evidence (G1) | 0.95 / 0.98 **[pre-registered]** | Sliced by code from the OCR text; never rewritten | Line + verbatim quote, checked by code | Not available from dots.mocr (Markdown, no coordinates); needs an OCR output with word boxes | Trust the slice; open the scan only to catch OCR misreads (none in the 25 spot-checked values) |
| Legacy OCR + LLM repair (G2) | 0.96 / 0.91 **[exploratory]** | The model's reading; it differs from the quoted OCR text for about 30% of values on legacy OCR (each flagged `repaired`) | The quote of the legacy text is checked; the repaired reading is not | Possible through the legacy OCR's hOCR word boxes (not demonstrated) | Check every flagged repair against the scan: 92% are right, so about 1 in 12 is a confident wrong reading |
| Page image only (V1) | 0.96 / 0.98 **[exploratory]**, value-bag scoring | The model's transcription | None | Boxes drawn by the model: on the right word only 67% / 40% (V3) | Find every value on the scan by hand; the box cannot be trusted as a pointer |

Two further cautions: the image-only score uses value-bag scoring (a value counts if the same text is
on the page), so it cannot tell a right value at the wrong place from a right value at the right
place; and a vision model's transcription has no checkable link to any text. **Choose a route on
accuracy and on audit cost per value, not on F1 alone.** Where evidence matters (data going to GBIF
or into a citable record), modern OCR with word coordinates plus quote-checked extraction is the only
route here whose every value can be traced mechanically to the page.

## Recommendation: where the next unit of effort goes

1. **Keep investing in OCR, but steer it by an acceptance test on names, per material type.** Choose
   OCR on how many entity names survive intact on a small labelled sample, not on page CER: across 22
   OCR versions page CER barely predicts extraction, entity preservation predicts it almost exactly
   (Spearman 0.95 / 1.00). For English print like these books, modern OCR is already enough; for
   other languages, layouts, eras, tables, plates and handwriting, run the same test before deciding,
   because their error distributions may differ completely. Prefer OCR whose errors are visible;
   fluent misreadings cannot be repaired downstream.
2. **Fund entity resolution as its own workstream.** An LLM linker recovers most of the linking
   loss at low volume (one call per distinct name). The remainder needs a curator decision on which
   checklist and species concept the data follow; that is a governance question, not engineering.
3. **Write the scope down before scaling.** Index pages, joint authorities (`H. & A.`), broad
   vernacular words and place-name boundaries change scores by up to ten points. Decide them once,
   with an adjudicator, and filter what is out of scope: after the spot-check, BHL `Index` pages were ruled out, a page-type filter that costs nothing.
4. **Review by sampling, with evidence attached.** Prefer routes that keep a machine-checkable trail
   (sliced values, verbatim quotes, OCR word boxes); a model's repaired reading or image transcription
   needs a person for every changed or unanchored value. Keep line + verbatim quote on every value. On
   legacy OCR route review with cheap checks; on clean text estimate quality with a random sample and
   use a second model to find misses. Do not skip review because two models agree.
5. **Do not buy a bigger extraction model.** Haiku 5.5 extracted 682 pages for $0.40 in 7.5 minutes;
   Opus 5.5 cost $7.64 for a few points more. Spend the difference on steps 2-4.

## Answer to the research question

*When does improved OCR stop being the main bottleneck?* On these books, as soon as names survive
the OCR: modern OCR, LLM repair or image reading all bring extraction to about 0.95. Whether that
point is reached as easily on other material is an open question, not a result of this pilot. There is no
single page-CER threshold; entity preservation is the measure to watch. *What limits trustworthy
data after that?* Entity resolution (the largest measured loss on clean text), the definition of
what counts as a datum, and errors no step can see (fluent OCR misreadings). Requiring
evidence did not change the current accuracy metrics, which shows that those metrics do not capture
what evidence is for, not that evidence verification lacks value: it separates routes that look
equal on F1 (only quote-checked extraction from OCR text gives every value a mechanical trail back
to the page), and image coordinates have to come from OCR word boxes, not from a vision model.

## What this does not show

- Two books (plus 8 botany pages): a direction for a pilot, not a rule for all of BHL. Book and OCR
  quality are confounded, so results are per book. The PCAS case points the same way on botany.
- All material is English printed text from 1849-1907. Other languages (Latin-heavy descriptions,
  German, French), dense tables and indexes, plate captions, older or damaged print and handwritten
  field notes or labels may fail OCR in different ways; the conclusion "OCR is no longer the main
  bottleneck" does not extend to them. Even here, the Reeve index tables came out of modern OCR as
  HTML table markup, a layout effect this pilot did not score.
- Exploratory results were designed after seeing the test results and need a fresh test set.
- The books are public. Repair and image reading may be helped by pre-training exposure; a probe
  found no sign of page memory in repair (fluent substitutions restored 0 of 29 times), which does
  not prove there is none.
- One gold labeller; a second labeller on 5 pages. PCAS boundary decisions were made after seeing
  model outputs; both versions are reported.
- Entity resolution was measured on birds only (34 gold-resolved names). Shell names (Reeve, 56
  distinct names) were left for the next round: building their gold links would take 2-3 hours, and
  the pre-registered question is answered on Butler. Whether the LLM linker's gain holds for molluscs,
  where synonymy is heavier, is untested.
- Review time is from 9 timed spot-check items only (median 30 s), not a review-time study.

## Cost

API spend for the whole project about $49 (Claude about $42, Gemini about $7), including four
Claude models, a whole-book run of 682 pages and the botany case. Per page per pass: extraction
about $0.0006 (Haiku, batch) to $0.011 (Opus, batch); LLM repair about $0.05 and image reading about
$0.04 (Opus, sync). The real cost was people: labelling 22 + 8 pages, Butler's name links, error
tags and a 60-item spot-check.

---

*Details: README "Results", "Exploratory findings" and "PCAS botany case"; `results/analysis_test_main/`,
`results/linking_test/`, `results/ocr_ladder/`, `results/linking_variants*/`,
`results/exploratory_conditions/`, `results/model_comparison/`, `results/book_spotcheck/`,
`results/pcas/`.*
