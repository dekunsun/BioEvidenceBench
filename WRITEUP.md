# Where does trustworthy data get lost between a 19th-century page and a database row?

*A write-up of BioEvidenceBench V1 (November 2026). The decision memo is in
[`memo/MEMO.md`](memo/MEMO.md) ([中文](memo/MEMO_zh.md)); the full method and every number are in the
[README](README.md).*

Millions of pages of historical natural history are now scanned and online, most of them in the
[Biodiversity Heritage Library](https://www.biodiversitylibrary.org/) (BHL). Turning them into data
(which species, seen where, when, by whom) is the obvious next step, and LLMs make it look easy. The
harder question is where to spend effort so that the data is *trustworthy*: better OCR, a better
model, automated verification, entity resolution or human review?

BioEvidenceBench is a small, system-level evaluation of **evidence-grounded scientific data
extraction**. It is not an OCR benchmark ([FineBooks](https://huggingface.co/spaces/finebooks/bhl-ocr-leaderboard)
already scores OCR models). It follows one mention through the whole pipeline and asks how much
reliability each step loses.

## The setup

- **Two books, three versions of every page.** Butler, *Birds of Great Britain and Ireland* vol. 2
  (1907) and Reeve, *Conchologia iconica* vol. 5 (1849). FineBooks' expert transcriptions of these
  pages mean each page exists as BHL's legacy OCR, a modern open OCR (dots.mocr) and an expert
  transcription. The page stays the same; only the text quality changes.
- **A gold set made before any model output.** 22 pages (6 for development, 16 locked for testing),
  labelled by hand with a written, versioned guide: taxa, people, places, institutions, dates and
  vernacular names, each as an exact character span. A second labeller double-labelled 5 test pages
  (agreement 0.90 exact, 0.95 overlap).
- **Values are never rewritten by the model.** The model returns a line number and a verbatim quote;
  code checks the quote against the source and slices the value out. Every output can be traced back
  to the page.
- **Pre-registered, then frozen.** Hypotheses, metrics and the configuration were written down and
  frozen (`FREEZE.json`) before the test pages were run; test outputs stayed sealed until the gold set
  was final. Everything decided afterwards is labelled exploratory and logged in `DEVIATIONS.md`.

## What we found, step by step

**1. OCR is the first and largest loss, on these books.** On legacy BHL OCR, extraction value F1 is
0.60 (Butler) and 0.64 (Reeve); on modern OCR 0.95 and 0.98; on the expert transcription 0.98 for
both. 151 of 163 wrongly handled gold mentions were OCR-sensitive. Moving from modern OCR to an
expert transcription added almost nothing. *(pre-registered)*

**2. Page error rate is the wrong OCR metric.** Across 22 OCR versions of the same pages, page-level
character error rate barely predicts extraction quality, while the share of gold names that survive
OCR intact predicts it almost exactly (Spearman 0.95 and 1.00). Several OCR models under 0.5% page
CER still broke a fifth to two fifths of Butler's names. *(exploratory)*

**3. Once names survive OCR, the extraction model matters little.** Claude Haiku 5.5, Sonnet 5.5,
Opus 5.5 and Fable 5.2 all land between 0.93 and 0.98 on modern OCR, and all at 0.58 to 0.65 on
legacy OCR. Haiku costs about a fifteenth of Opus. A rule baseline (gnfinder plus regular
expressions) is far behind on names. *(LLM vs rules pre-registered; model comparison exploratory)*

**4. Entity resolution is the largest loss on clean text.** Linking extracted bird names to GBIF with
a plain name lookup lost 14 of 34 correctly extracted names (old genera, synonyms, names now treated as
subspecies, abbreviations). *(pre-registered)* An LLM linker that first proposes today's accepted name
from the name and its context recovers most of them (link recall 0.59 to 0.91); what is left are
taxonomic judgment calls. Here the model does matter: Opus 0.91, Haiku 0.76. *(exploratory)*

**5. Much apparent model error is undefined scope.** On an 8-page botany case (Eastwood 1898),
aligning five boundary conventions (titles in person names, place-name chains) moved F1 from 0.83 to
0.94 with no model change. On a whole-book run, 16% of extracted mentions sat on index pages the guide
had never defined; ruling them out of scope shrank the review queue by 60%. *(exploratory)*

**6. Same accuracy is not the same evidence.** Three routes past bad OCR reach similar F1: modern OCR
plus quote-checked extraction, an LLM that repairs legacy OCR, and reading the page image directly.
But only the first gives every value a mechanical trail back to the page. Repaired values (about 30%
on legacy OCR) need a person to check them, and about 1 in 12 is a confident wrong reading. Image-only
values have no text evidence, and the boxes a vision model draws land on the right word only 67%
(Butler) / 40% (Reeve) of the time. *(exploratory)*

**7. Model agreement is not correctness.** On legacy OCR, mentions that two models from different
providers agreed on were still wrong 50 (Butler) and 75 (Reeve) times: both copied the same OCR
damage. *(pre-registered)* On modern OCR, a 60-item spot-check outside the sample found 25 of 25
checked Opus outputs correct, and a second model surfaced real misses. *(exploratory)*

## What it suggests about where to spend

1. Keep investing in OCR, but accept it on whether names survive, per kind of material.
2. Treat entity resolution as its own workstream, with a curator-owned taxonomy policy.
3. Write down the scope (index pages, authorities, broad vernacular words) before scaling.
4. Review by sampling, with evidence attached; never skip review because models agree.
5. Do not buy a bigger extraction model; spend the difference on steps 2 to 4.

## Things I got wrong or learned along the way

- **A null result is a statement about the metric.** Requiring a verbatim quote did not change
  accuracy, and no unsupported value appeared in either arm. That is because both arms took values
  from the source by code, so the test compared two forms of verification rather than verification
  against none. It does not show that evidence has no value; its value is traceability and audit
  cost, which accuracy does not measure.
- **Rules found on test pages go into the guide and the gold, never into the prompt.** Scores are
  reported both with and without those later rules.
- **Adjudicating after seeing model output pulls the gold towards the model.** On the botany case
  every boundary decision moved the gold closer to the model, so both versions are reported.
- **Write the scope before the sample.** A page sampled as "no entities" had two; the strata were
  defined before the guide was.

## What this does not show

- Two books (plus 8 botany pages), all English print from 1849 to 1907: a direction for a pilot, not a
  rule for BHL. Other languages, layouts, print eras, tables, plates and handwritten records may fail
  OCR in entirely different ways, so "OCR is no longer the main bottleneck" does not extend to them.
- Exploratory results were designed after seeing the test results and need a fresh test set.
- The books are public and may be in the models' pre-training data. A probe found no sign that repair
  relies on memory of these pages (a plausible but changed epithet was restored 0 of 29 times), which
  does not prove there is none.
- One gold labeller; mollusc name linking and a proper review-time study are left for the next round.

## Reproduce

Everything uses public data (BHL, FineBooks, GBIF). The README lists the scripts in order, from
loading the pages to scoring; raw outputs, prompts, input hashes and costs for every run are in
`results/`. The whole project cost about $49 in API calls; the real cost was labelling time.

*Data: expert transcriptions from [finebooks/bhl-impact-gt](https://huggingface.co/datasets/finebooks/bhl-impact-gt)
(IMPACT / BHL, CC-BY 3.0), metadata from [finebooks/bhl-metadata](https://huggingface.co/datasets/finebooks/bhl-metadata)
(CC0), legacy OCR and page images from BHL and the Internet Archive.*
