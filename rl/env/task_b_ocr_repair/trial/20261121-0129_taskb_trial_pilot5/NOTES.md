# Notes on the 5-page pilot (Claude, 2026-11-21)

Dev pages only. $0.787 in total (Opus 5.5 $0.769 = $0.154 per page, $0.0024 per call; Haiku 5.5
$0.018). 640 of 640 calls answered, all `end_turn`.

**The reward behaved as designed** on every case read by hand:
- Haiku's 17 multi-line answers (5%) are thinking written into the reply ("Wait, I must reproduce
  the line…"): the format gate scores them 0.
- Opus "corrected" the print's own misprints (`hahens` → `habens`, `Ausführunsgänge` →
  `Ausführungsgänge`) and lost 0.5 for each: the instruction to keep the book's spelling is tested.

**Zero-variance failures that come from conventions, not from the models** (all eight samples fail
the same way, so they add no GRPO signal and lower pass rates for the wrong reason):
1. Typographic apostrophe: the transcription writes `Canary’s`, `half-hour’s` (U+2019), the OCR `'`.
   A correct reading counts as damaged. 65 dev units have such a damaged word.
2. Letter-spaced emphasis (Sperrsatz): print and OCR `H e i d e r`, transcription `Heider`. Opus keeps
   the spacing because the prompt says "as the book prints it". About 23 dev units (Chitinskelett).
3. Reference typo: `dér` for the print's `der` (Trudy). Not detectable automatically.

**Signal:** items whose 8 rewards are not all equal: Haiku 28% (2–5 damaged words: 48%), Opus 10%
(14%). Outputs differ as text in 45% (Haiku) and 20% (Opus) of groups. Opus at default temperature is
close to deterministic on this task; a 0.5–1.5B model will differ, so these figures test the reward
and item design, not the training signal itself (plan 9: calibrate on the target model).

**Item mix:** the Butler and Trudy pilot pages had few dev lines with 2–5 damaged words, so the fill
gave 15 clean items of 40 (38%, target about 20%).
