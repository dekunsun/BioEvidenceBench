# rl/ construction log

Decisions and deviations for the `rl/` extension (not the frozen study; that uses `DEVIATIONS.md`).
The plan is `rl/PLAN_zh.md`.

| Date | Step | What was done | Decided by |
|---|---|---|---|
| 2026-11-20 | Step 0 | Legacy per-page OCR checked for the four non-English / non-sample books (Cuvier, Trudy, Das Chitinskelett, Piscium querelae): one page each returned text from BHL's open-data S3; must be decoded as UTF-8 | Claude |
| 2026-11-20 | Step 0 | Sealed 16 pages (`rl/sealed/pages.csv`, sha256 `c4abd664ac2a…`), seed 20261120; frame 208 Butler, 259 Reeve | Plan v2 (Gloria authorised) |
| 2026-11-20 | Step 0 | Task B split (`rl/env/task_b_ocr_repair/splits.csv`, sha256 `a12f7893c25e…`): 10-page blocks by scan order, seed 20261120. Cuvier 516 pages held out. Train 1,277 / dev 167 / in-book test 167 pages; 38 excluded (22 sample + 16 sealed) | Plan v2 |
| 2026-11-20 | 2A | Attacked the frozen scorer: 68 adversarial answers on the 16 old test pages (`src/rl_attack_scorer.py`, `rl/verifier_audit/adversarial/`). Frozen rules: ok 45, by design 9, finding 11, false negative 3. Patched copy (`rl/verifier_audit/score_patched.py`: fidelity gate for fuzzy / silent-correction / case-variant locations; strip edge `"`): ok 53, by design 12, finding 3 (empty answers). Frozen test runs had 0 fuzzy / silent-correction statuses and 0 quote-wrapped G2 readings, so no reported number changes. `expected` values await Gloria's review | Claude (Gloria to review) |
| 2026-11-20 | 2A status | First-round audit completed; additional fidelity and parser checks pending (Gloria, 2026-11-20: next stage does not wait for them) | Gloria |
| 2026-11-20 | Task B steps 1–3 | Reeve pilot on 4 training pages (`src/rl_task_b.py`, `src/rl_task_b_pilot.py`, `rl/env/task_b_ocr_repair/pilot/`): 356 of 357 lines align; two word alignments and Reward v1.0 with diagnostic fields; 10 zero-cost adversarial checks. Rule changes: presentation-form ligatures (U+FB00–FB06) folded to letters (æ, œ, ſ kept); similarity floor 0.5 → 0.3 so badly damaged but correctly paired lines stay; `extra_words` (insertions found by alignment, not counting junk already in the OCR). Two reward bugs found and fixed. Open: penalty normalisation, long s | Claude (Gloria to decide the open questions) |
