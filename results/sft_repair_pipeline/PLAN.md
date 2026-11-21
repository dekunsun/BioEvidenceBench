# Plan: the released SFT repair model inside the extraction pipeline (exploratory)

*Written 2026-11-21 before the repair run and before any extraction on the repaired text. Gloria
approved the item ("按你的建议，删分支，然后做第 4 项"; estimate $1–3). Exploratory: the 16 test pages
were unsealed on 2026-11-20, so nothing here is a blind test; logged in `DEVIATIONS.md`.*

**Question.** If BHL's legacy OCR is first repaired line by line by the released research checkpoint
(`rl-sft-ocr-repair-v1`, Qwen3-0.6B SFT seed 2), how much extraction value does it recover, compared with
re-OCR (dots.mocr) and with Opus repairing while it extracts (G2)?

**Fixed rules** (also in `src/sft_repair_pipeline.py` and `rl/training/repair_pages.py`):
1. Every legacy OCR line with at least 15 characters and 2 words is repaired (924 of 991 lines on the 22
   pages); shorter lines stay as they are, as in training.
2. Context = nearest non-empty OCR line above and below on the same page; prompt `repair_v3`, thinking off.
3. Greedy decoding, at most 128 new tokens.
4. The answer goes through the fixed clean-up; if it is empty or its length is outside 0.5–1.5× the OCR line,
   the OCR line is kept (a pipeline's safe fallback). The fallback count is reported.
5. Page structure is kept; only line contents change.
6. Measures on all 22 pages: median page CER and the share of gold mentions preserved intact (the OCR
   ladder's measure, which predicted extraction F1 at Spearman 0.95 / 1.00).
7. Extraction on the 16 test pages: frozen G1 prompt `p4-guide-v0.6`, Claude Opus 5.5, batch, cap $1, scored
   by `score.py` against the frozen test gold. Compared with legacy G1 (0.60 / 0.64), dots.mocr G1 (0.95 / 0.98)
   and Opus G2 repair (0.96 / 0.91), Butler / Reeve.
8. Reported whatever the result, including if repair makes extraction worse.
