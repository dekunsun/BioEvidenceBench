# BioEvidenceBench: working rules for AI-assisted research

This file is read by Claude Code at the start of every session. It states how an AI assistant may and
may not work on this repository, and where the project's state lives. The project itself is described
in [README.md](README.md); what was learned about working with an assistant is in
[docs/lessons_learned.md](docs/lessons_learned.md), section D.

## 1. What the project is

An evaluation of where reliability is lost when historical scientific pages become database records:
reading (OCR), extraction, evidence, linking names to databases, and review. Main question: *when does
improved OCR stop being the main bottleneck, and when do evidence verification and entity resolution
become the limiting factors?* "No single threshold" is a valid answer.

- **Not an OCR benchmark.** FineBooks already scores OCR models on these pages; this project measures
  what happens downstream of OCR.
- **Core study:** two English printed books with expert transcriptions (Butler 1907, Reeve 1849), each
  page read three ways (BHL legacy OCR, modern OCR `dots-mocr`, expert transcription). Results are
  **reported per book, never pooled**; book and OCR quality are confounded.
- **External cases, reported separately:** PCAS botany (Eastwood 1898) and the 本草綱目 manuscript
  (Siku quanshu edition), each with its own gold, freeze and report.
- **Scale:** a pilot with page-level uncertainty, not a formal benchmark. Never claim a best
  configuration for all of BHL.

## 2. Separation of powers

Claude is one of the model families under evaluation, so the assistant must not help set the exam.
The rule behind everything below: **the assistant does engineering and gathers facts; a person makes
every judgment, and every judgment leaves a record.**

1. **Gold labels.** The assistant never creates, decides or pre-fills a gold label. It may type into a
   gold file only a change the labeller decided explicitly, row by row, and logs each one in
   `gold/gold_changes_<labeller>.csv`. Model outputs go only into clearly separate review files.
2. **No review of test labels.** The assistant does not check test labels for omissions or wrong
   fields unless the labeller asks. It may supply facts ("is this word in the OCR input?").
3. **Deliveries first.** Every label delivery is archived unchanged in `gold/received/` and committed
   before any comparison with a model, another labeller or an assistant.
4. **Decisions are written down** with the date and the decider's own words (in the private working
   brief and, for public effect, in the guide, `DEVIATIONS.md` or the run folder).
5. **Questions that need a person** are grouped, each with a recommendation, and asked once.
6. **Paid runs.** A small pilot first (about 5 pages), cost per page reported, then an explicit
   go-ahead and a cap with headroom on every run. Spend is recorded per run in
   [docs/eval_settings.md](docs/eval_settings.md).
7. **Exploratory work is logged as a deviation before any conclusion is written**, and is never
   presented as a pre-registered result.

## 3. Hard rules

Older files (including frozen ones) cite "CLAUDE.md rule N" or "section 4 / 4a". They refer to the brief as
it stood until 2026-11-26 (commit `a6cd353`): rule 1 = gold labels, rule 2 = run records, rule 3 = the model
never rewrites source text, rule 4 = public data, rule 5 = 5-page paid pilot; sections 4 and 4a = the design
summarised in section 4 below.

- **The model never rewrites source text.** Inputs are numbered lines; the model returns a line and a
  verbatim quote; code finds the quote in that line and slices the value from the source. A quote
  that does not match exactly is logged as a silent correction or invalid evidence.
- **Frozen files are never edited:** `PREREGISTRATION.md`, `FREEZE.json`,
  `data/bencao/FREEZE_bencao.json` and every file they hash. Changes after a freeze go in
  `DEVIATIONS.md`; rules adopted after the freeze go in `GUIDE_ADDENDUM.md`.
- **Sealed test outputs** are never opened or printed before the gold set is complete and the freeze
  verifies (`src/unseal.py` refuses otherwise). Rules found on test pages go into the guide and the
  gold, never into the frozen prompt. Dev pages are not blind; only test pages are independent results.
- **Reproducibility:** every run folder `results/<run_id>/` keeps model name and version, full prompt,
  input source and SHA-256, decoding settings, raw output and timestamp.
- **Public data only.** No internal or non-public data from any institution. Check licences before
  committing data (expert transcriptions CC BY 3.0; BHL metadata CC0; Kanripo text CC BY-SA 4.0, and
  any file containing it carries that licence). Large raw data is fetched by scripts, not committed.
- **Flag anything unverified** instead of stating it as fact in the README, memo or preprint.
- **Secrets:** never print or store API keys or tokens; never ask anyone to paste one into chat.
- **Commits** contain no model identifiers in messages, code comments or documents.

## 4. Current design (as built)

Where this differs from older notes, this section and [ANNOTATION_GUIDE.md](ANNOTATION_GUIDE.md) win.

- **Unit:** a mention = character span in the expert transcription + field type. Primary fields
  `taxon`, `person`, `locality`, `institution`, `date`; `vernacular` is scored separately and never
  enters the primary score. Outputs on OCR texts are mapped to expert positions by character alignment.
- **Conditions:** G0 (values only, code aligns afterwards) and G1 (line + verbatim quote). Text
  versions: legacy, `modern_dots-mocr`, `modern_dots-mocr_plain` (Markdown removed by deletion only),
  expert. Rule baseline: gnfinder for names, regex for places and dates.
- **Metrics:** value F1 (exact and lenient) per field and `ALL_PRIMARY`; entity preservation and
  entity-span CER; invalid evidence, silent correction and unsupported-claim rates (not "hallucination
  rate", which is zero by construction); paired page-bootstrap intervals per book.
- **Review (RQ4):** shadow evaluation only; nothing skips review. A value is flagged "proposed
  auto-accept" when both models extract it and the deterministic checks pass. Agreement is not
  correctness.
- **Linking (Butler):** plain name-only GBIF lookup scored against labelled links; a GBIF match is a
  signal, not proof. Subfamily names are not scored (no such rank in the GBIF backbone).

## 5. Where things are

| Path | What |
| --- | --- |
| `ANNOTATION_GUIDE.md`, `GUIDE_ADDENDUM.md` | labelling rules (versioned) and rules adopted after the freeze |
| `PREREGISTRATION.md`, `FREEZE.json` | frozen analysis plan and hashes; `PREREGISTRATION_v2.md` is an unfrozen draft |
| `DEVIATIONS.md` | everything decided or run after the freeze |
| `gold/` | labels, `received/` deliveries, change logs, adjudication |
| `data/sample/` | the page texts used by the runs (hashes in `manifest.csv`) |
| `results/<run_id>/`, `results/analysis_*` | run records and analyses |
| `src/` | every script starts with a note on what it does and how to run it |
| `rl/` | the training study (SFT, GRPO, reward audit) |
| `data/bencao/`, `docs/notes/bencao_*` | the 本草綱目 case, its guide, freeze and draft pre-registration |
| `docs/` | product memo, results, lessons, preprint (`docs/preprint.md`), RL report |
| `poster/` | Deep Matters 2026 poster (see `poster/README.md`) |

## 6. Checks and builds

```bash
pip install -r requirements-lock.txt      # exact versions (requirements.txt has the lower bounds)
pytest -q                                  # unit tests
python src/freeze.py --verify              # main evaluation unchanged since the freeze
python src/bencao_freeze.py --verify       # 本草綱目 case unchanged since its freeze
```

The same checks run in CI on every push (`.github/workflows/ci.yml`). Builds:
`python src/build_preprint.py` (preprint) and `python src/build_preprint.py rl` (RL report);
`python src/plot_poster_v5.py && python src/build_poster_v5.py && node poster/render.js "$PWD/poster" poster A1`
(poster; `render.js` reports overflow); `python src/make_eval_settings.py` (spend table);
README figures from `src/plot_readme_figs.py` and `src/plot_scan_examples.py`.

## 7. Writing conventions for public pages

- Refer to the labeller as "the author" (byline Dekun Sun). Frozen files, working logs and gold file
  names keep their original wording.
- Keep pre-registered and exploratory results apart, and say which is which.
- The review numbers are "50 errors in Butler and 75 in Reeve inside the agreed set on legacy OCR";
  never "50 of 75".
- Every figure built from a scan credits its source and licence; text strings in figures are copied
  from project files, never retyped.
- Keep `README.md` / `README_zh.md` and `memo/MEMO.md` / `memo/MEMO_zh.md` in step.
