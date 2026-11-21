# BioEvidenceBench: results

Every number in the project, in one place. Pre-registered results come from the frozen run ([`FREEZE.json`](../FREEZE.json), [`PREREGISTRATION.md`](../PREREGISTRATION.md)); everything decided after unsealing is exploratory and logged in [`DEVIATIONS.md`](../DEVIATIONS.md). Paths in backticks are relative to the repository root. Run-level settings (model, mode, prompt, requests, cost): [evaluation settings](eval_settings.md). What it means for a product: [product summary](product.md).

## 1. Pre-registered results (16 locked test pages)

Frozen before any test page was run (`FREEZE.json`); 16 locked test pages (Butler 7, Reeve 9);
Opus is the primary model, Gemini the second model for RQ4. Value F1 on `ALL_PRIMARY` with 95%
page-bootstrap intervals; verdicts against the rules in `PREREGISTRATION.md` section 3. Full
tables: `results/analysis_test_main/REPORT.md`, `results/linking_test/REPORT.md`.

| | Result |
|---|---|
| Agreement (5 pages, as delivered) | ALL_PRIMARY exact 0.90, overlap 0.95 (Butler 0.89 / 0.93, Reeve 0.90 / 0.96); lowest field: locality exact 0.75, mostly span edges. All 23 disagreements adjudicated "keep gold". `results/agreement_independent/` |
| RQ1 OCR | Opus G1 value F1, legacy → modern → expert: **Reeve 0.64 → 0.98 → 0.98**, Butler 0.60 → 0.95 → 0.98. Pre-registered (Reeve): legacy → modern +0.34 [0.25, 0.46], *supports* (≥ 0.10); modern → expert +0.005 [−0.015, 0.03], *supports* (< 0.05). Butler is descriptive: +0.36 and +0.03 [0.01, 0.06]. Almost all legacy-OCR loss is misread text inside a correctly found span (lenient F1 0.93–0.97). Butler's legacy-OCR taxon F1 is 0.20 although its page CER is low. Removing Markdown changes little (−0.015 to 0) |
| RQ2 baseline | On the expert text the LLM's recall is higher for taxon and person in both books and for Butler's localities (*supports*); Reeve's localities and institutions and Butler's dates are *inconclusive*. Taxon value F1: Butler 1.00 vs 0.64, Reeve 0.99 vs 0.54. The falsifier (rule ≥ LLM on taxa) did not occur. The gap is largest for person (+0.74 / +0.78 recall), not for institution |
| RQ3 evidence | Requiring evidence cost no recall (G1 − G0 between −0.015 and +0.007, all *supports*). But neither condition produced any unsupported output (0 in G0 and G1, both models), so the expected reduction could not be observed. In both arms the value is taken from the source by code, so this compared two forms of verification, not verification against none; it does not show that evidence verification has no value (its value is traceability and audit cost, which these metrics do not measure) |
| RQ4 review prioritisation | Models agreed on 99–100% of predictions, leaving ≤ 2 unflagged per book and version: *too few to compare*. Errors inside the "proposed auto-accept" set: expert 3 (Butler) / 4 (Reeve), modern OCR 6 / 5, **legacy OCR 50 / 75**. Agreement is not correctness |
| E4-lite linking (Butler) | Pre-registered (Opus G1, expanded linker): of 34 gold-resolved names, 14 are lost at linking and 0 before it on the expert text (difference 0.41 [0.25, 0.60], *supports*); 13 vs 1 on modern OCR (0.35 [0.10, 0.55], *supports*). Link recall of a plain GBIF lookup is 0.59 even on the gold text: 8 matched only at genus, 3 wrong taxon, 3 no record. On legacy OCR, 0.12 |
| Sensitivity | Treating the 12 rows decided by guide rules added after the prompt as optional changes ALL_PRIMARY value F1 by at most 0.004 (`results/analysis_test_sensitivity_v0.6/`) |
| Error analysis | Opus G1, 163 gold mentions wrong in at least one version, tagged by Gloria (several tags allowed; group A preset as OCR-sensitive by definition, see `DEVIATIONS.md`): OCR-sensitive 151, extraction/reasoning 17, ambiguous/mixed 32; 130 are OCR-sensitive only. Extraction errors are mostly Butler vernaculars covered only by guide rules added after the prompt (hawthorn, moss, insects, pine); ambiguous cases are span edges, relative dates and ligature forms. The 20 extra outputs (model outputs with no gold mention behind them): OCR-sensitive 18, extraction/reasoning 4, ambiguous/mixed 20; 15 of them appear only on OCR text, mostly legacy OCR on Reeve page 8966937. `results/error_analysis_test/SUMMARY.md` |
| Cost | Test runs: Opus $1.50 (batch), Gemini $4.11 (sync). Total API spend about $15.4 for the pre-registered work; about $49 including every exploratory follow-up (Claude about $42, Gemini about $7; per run in [evaluation settings](eval_settings.md)) |

**Reading for the main question (for these two books, with this linker):** once modern OCR is
used, extraction is within 0.03 of the expert transcription, and the largest remaining loss is at
entity resolution: a plain GBIF name lookup loses about four in ten names that extraction got
right. This is a pilot on 16 pages; it says where to look next, not a rule for BHL. The linker
is deliberately naive, so a better linker could change the second half of that sentence.
The exploratory follow-ups below do change it: an LLM linker recovers most of the linking loss, and an
LLM repair of legacy OCR or reading the page image directly reaches about the same accuracy as modern
OCR. What is left is fluent OCR errors, taxonomic judgment and the definition of a mention.

## 2. Exploratory findings (after the frozen test run)

*Decided after the test pages were unsealed, so none of this is a pre-registered result
(`DEVIATIONS.md`). Same 16 test pages, frozen gold and scorer; Claude Opus 5.5 unless stated.*

| Question | Finding | Where |
|---|---|---|
| Which OCR measure predicts extraction? | Over 22 OCR versions (21 FineBooks rows + legacy), value F1 tracks **gold-entity preservation** almost perfectly (Spearman 0.95 Butler, 1.00 Reeve); **page CER does not** (−0.07 / −0.62). Several OCR models with page CER under 0.5% keep only 57–80% of Butler's names intact. Extraction recall ≈ preservation (median gap +0.01): if the name survives the OCR, the model gets it | `results/ocr_ladder/` (`downstream.png`) |
| Is linking really the bottleneck? | Mostly a property of the naive linker. An **LLM linker** (name + context → currently accepted name → GBIF) raises Butler link recall from 0.59 to **0.91** on the expert text and from 0.12 to **0.71** on legacy OCR; a GBIF lookup with an animal hint only reaches 0.62. Its remaining misses are taxonomic judgment calls (e.g. `Phylloscopus tristis` as a race of *P. collybita*) | `results/linking_variants/` |
| Can an LLM repair stand in for re-OCR? | **Largely yes, for visible errors.** With a verbatim quote kept as evidence plus a separate repaired reading (G2), legacy OCR goes from 0.60 to **0.96** (Butler) and 0.64 to **0.91** (Reeve, with positions); Tesseract output from 0.68 to 0.96 / 0.94. 92% of the legacy values it changed became right. On the expert text it changed 4 values: 3 fixed the transcription's own typos (`nontifringilla`, `I898`, a broken word), 1 swapped a ligature | `results/exploratory_conditions/` |
| …and where not? | **Fluent OCR errors are not repairable.** DeepSeek-OCR-2 writes plausible text (`Linnaeus` for `Linnæus`, `Turritella brevisis`, `Valparaíso`); repair only lifts it to 0.81 / 0.87. Garbled legacy OCR (`BiioDEiup`) is easier to fix than fluent misreadings | same |
| Is a separate OCR step needed? | **Not for this task.** Reading the page image directly (V1) gives 0.96 / 0.98 value F1 (bag scoring), the same as modern OCR + extraction. Image + legacy OCR (V2) is no better than repair alone | same |
| Which cheap signal helps review? | On legacy OCR, two mechanical checks (OCR-junk characters; no exact GBIF match for a taxon) flag 25% of outputs and catch 55% of the errors at 77% precision; model disagreement catches 7%. On modern OCR, errors are rare (3%) and no cheap signal finds them | `results/review_signals/` |
| Does a cheaper or stronger model change the picture? | **No.** On the frozen G1 condition (`results/model_comparison/`), value F1 on dots.mocr is 0.94 / 0.95 for Haiku 5.5, 0.93 / 0.97 Sonnet 5.5, 0.95 / 0.98 Opus 5.5, 0.96 / 0.98 Fable 5.2 (Butler / Reeve; intervals overlap); on legacy OCR every model sits at 0.58–0.65. Haiku costs about 1/15 of Opus in the same mode ($1.5 vs $23 per 1,000 page-passes, sync). The model gap (≤0.05) is small next to the OCR gap (~0.35). Sonnet under-extracts long, dense pages in the repair condition | `results/model_comparison/`, `results/exploratory_conditions/` |
| Is repair memory of these books? | **No sign of it.** In a probe on the expert text (`results/memorisation_probe/`), two swapped letters in a gold name (a visible error) were put back in 65–68 of 69 cases by Opus and Fable (54 by Haiku); a binomial's epithet swapped for one printed on another page of the same book (a fluent change) was put back in **0 of 29** cases by all three models, even when the original name was printed elsewhere on the page. Repair reacts to visible errors, not to a remembered page. (It does not rule out memorisation in general.) | `results/memorisation_probe/` |
| Does it hold for a model from another provider? | **Yes, with one silent empty answer.** Gemini 4 Carbon (sync, schema enforced) on the same exploratory conditions (value-bag F1, Butler / Reeve): repair on legacy OCR 0.95 / 0.77 vs Opus 0.96 / 0.97; on the expert text 0.97 / 0.98; image only 0.97 / 0.97 vs 0.96 / 0.98; fluent DeepSeek-OCR-2 errors still not repaired (0.84 / 0.92). The Reeve gap is one page: on legacy page 8967281 (78 gold mentions) Gemini thought for 22,353 tokens and returned `{"mentions": []}` with a normal STOP; without that page Reeve is 0.986 (Opus 0.978); resent once as a diagnostic, the same request returned 77 mentions (page F1 0.954), so the empty answer was intermittent. As an **LLM linker** Gemini is the strongest model tried: Butler link recall 0.94 expert, 0.91 modern OCR, **0.88 legacy** (Opus 0.91 / 0.82 / 0.71). Its Batch API drops the newer `response_json_schema` field (3 of 3 bare arrays; the older `response_schema` works), so every Gemini run here is sync | `results/*_explore_*_gemini-4-carbon`, `results/linking_variants_gemini-4-carbon/`, `results/gemini_batch_schema_check/` |
| How does NHM's OCR choice do on the name test? | **Well on Butler, weaker on Reeve.** Mistral OCR, run through OpenRouter's PDF parser (Mistral version not reported; `src/fetch_mistral_ocr_openrouter.py`, $0.05 for 22 pages), added to the OCR ladder: on the 16 test pages it keeps **99.3%** of Butler's gold names intact and Opus G1 reaches value F1 **0.95** [0.92, 0.98] (dots.mocr 0.95); on Reeve it keeps **93.0%** and F1 is **0.92** [0.87, 0.97] (dots.mocr 0.98; rank 8 of 24). Its Reeve losses are single letters in the 1849 type (`SOWERBY`→`SOWERRY`, `Lamarck`→`Lamarek`, `leucozonias`→`leuczoonias` four times) plus ligatures written out (`Linnæus`→`Linnaeus`). Name preservation still predicts F1 (Spearman 0.95 / 1.00 with Mistral included). Not NHM's exact setting and not comparable with NHM's reported figures | `results/mistral_ocr_openrouter/`, `results/ocr_ladder/`, run `20261120-ocrladder3_claude-opus-5-5_test_G1` |
| Can a vision model give Level 3 (image) grounding? | **Values yes, boxes no.** Image only plus a box per mention (V3): 96–98% of values right, but the box contains the right word for only **67% (Butler) / 40% (Reeve)** of them (reference: Internet Archive hOCR word boxes, lenient). Level 3 should come from OCR word coordinates, not from boxes a model draws | `results/vision_boxes/` (`BOX_ACCURACY.md`, example images) |

Cost per page per pass (Opus 5.5, sync; batch halves it): plain extraction about $0.02, repair
$0.05, image only $0.04. **Caveat that matters most here:** BHL and the IMPACT transcriptions are
public, so repair and image reading may be helped by the model having seen these books. The
memorisation probe above found no sign of page memory in repair, but it cannot prove there is none;
the PCAS case (section 3 below) is a check on other material, but it is public too.

### Whole-book run and spot-check (exploratory)

Frozen G1 prompt on all 682 text pages of both books (dots.mocr), Opus 5.5 $7.64 and Haiku 5.5 $0.40, 7.5 minutes per batch; on the 16 test pages inside the run, value F1 reproduces the evaluated setting (Opus 0.96 / 0.98). Gloria checked 60 shuffled Opus/Haiku outputs from outside the sample against the scans: setting aside `unsure`, 25 of 25 Opus outputs were correct, none misread; 19 of the 21 `unsure` rows are entries in Reeve's index, a scope the guide never defined (16% of Opus's output sits on `Index` pages; Gloria then put `Index` pages out of scope, `GUIDE_ADDENDUM.md`, which also shrinks the "not agreed or check failed" review queue from 1,404 to 555 mentions); 10 of 14 Haiku-only outputs were real mentions Opus missed. Median 30 s per checked item (9 timed). `results/book_spotcheck/`.

## 3. PCAS botany case (external, reported separately)

Eastwood 1898, *Proc. Cal. Acad. Sci.* 3rd ser. Botany vol. 1, 8 pages (BHL item 48989; no expert transcription). Gloria labelled 210 mentions against the scans before any model ran (`gold/received/2026-11-20_pcas_gloria.tsv`); after seeing the outputs she adjudicated five boundary questions by the guide (titles out of person spans, narrow-to-wide chains as one span, one institution, a part-of-place phrase, `Carolinæ` as printed; `gold/gold_changes_pcas_gloria.csv`). Both versions are reported. Value-level F1, Opus 5.5, 8 pages pooled (no interval):

| Condition | as labelled | adjudicated | taxon (either) |
|---|---|---|---|
| Frozen G1 prompt on BHL legacy OCR | 0.70 | 0.80 | 0.73 |
| LLM repair (G2) on legacy OCR | 0.83 | 0.94 | 0.96 |
| Page image only (V1) | 0.83 | 0.94 | 0.99 |

The main experiment's pattern holds on botany: legacy OCR costs most on names, and repair or reading the image recovers it. New here: joint botanical authorities (`H. & A.`, `Torr. & Gr.`) are one person span (Gloria's rule, `GUIDE_ADDENDUM.md`), and the model splits them into two, a domain-specific error the bird and shell books did not show. Public text again, so contamination is not excluded. `src/score_pcas.py`, `results/pcas/`.

## 4. RL post-training (separate study, module 7)

Task: repair one line of legacy OCR into the expert transcription, scored word by word (not
extraction F1). Qwen3-0.6B, pre-registered locked test of 500 in-book lines and 500 lines of an unseen
French book. SFT raises damaged-word repair from 0.04 to 0.40–0.41 (Cuvier 0.21); GRPO from the base
model learns to copy the OCR (0.006 / 0.034); GRPO after SFT adds no repair (Δ −0.004) and +0.3 points
of preservation. The SFT checkpoint is released for research. Full results: [RL results](rl_results.md).

## 5. First findings from the data (descriptive, two books only)

- All 989 English GT pages join to the BHL `page` table by `PageID` (0 unmatched).
- Legacy OCR CER is much higher in Reeve than in Butler. Case-insensitive, on pages with 200 or
  more characters, the median is **6.6% vs 2.0%**. Reeve has Latin diagnoses in italics and dense
  abbreviations, and its OCR errors hit exactly the fields we care about. On one page it reads
  `Species 2S3` for 282, `184.6, p. 113` for `1846, p. 112`, and `Hob.` for `Hab.`.
- **Book and OCR quality are confounded.** Reeve has only 2 low-CER pages (< 2%) and Butler only
  8 high-CER pages (≥ 10%). A pooled F1-vs-CER curve would largely compare the two books.
- **Modern OCR closes most of the gap on the same pages.** dots.mocr's median CER (pages with
  200+ characters, case-insensitive) is **1.3% for Reeve and 1.1% for Butler**, down from 6.6% and
  2.0%. It is lower than legacy OCR on 91% of pages. So each page now comes in a high-CER and a
  low-CER version, which separates OCR quality from the book.
- Modern OCR has its own failure mode: 35 pages have CER > 10% while missing < 5% of the words.
  They are re-ordered, not misread.
- Small capitals add about 3 CER points by themselves: the experts typed them as upper case and
  the OCR did not. CER bands therefore use the case-insensitive value.
- Index pages in Reeve list bare epithets under a genus heading (`ampullaceum, Philippi`).
  TaxonFinder finds few or no names on them.
- Missing `<ReadingOrder>` affects about 20% of Butler's text pages and none of Reeve's.
