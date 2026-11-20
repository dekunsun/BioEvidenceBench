# rl/ construction log

Decisions and deviations for the `rl/` extension (not the frozen study; that uses `DEVIATIONS.md`).
The plan is `rl/PLAN_zh.md`.

| Date | Step | What was done | Decided by |
|---|---|---|---|
| 2026-11-20 | Step 0 | Legacy per-page OCR checked for the four non-English / non-sample books (Cuvier, Trudy, Das Chitinskelett, Piscium querelae): one page each returned text from BHL's open-data S3; must be decoded as UTF-8 | Claude |
| 2026-11-20 | Step 0 | Sealed 16 pages (`rl/sealed/pages.csv`, sha256 `c4abd664ac2a…`), seed 20261120; frame 208 Butler, 259 Reeve | Plan v2 (Gloria authorised) |
| 2026-11-20 | Step 0 | Task B split (`rl/env/task_b_ocr_repair/splits.csv`, sha256 `a12f7893c25e…`): 10-page blocks by scan order, seed 20261120. Cuvier 516 pages held out. Train 1,277 / dev 167 / in-book test 167 pages; 38 excluded (22 sample + 16 sealed) | Plan v2 |
