# OCR line repair, Qwen3-0.6B + SFT (research checkpoint)

**Research checkpoint. Not for automatic replacement of library text.** It still changes about 1.8%
of the words the OCR had right, and repairs about 40% of damaged words in the books it was trained on
and 21% in an unseen French book.

| | |
|---|---|
| File | `sft_s2.tar` (1,203,578,880 bytes; one folder `sft_s2/` written by `save_pretrained`: model config, generation config, `model.safetensors` in bf16, and the base model's tokenizer with its chat template) |
| Base model | [`Qwen/Qwen3-0.6B`](https://huggingface.co/Qwen/Qwen3-0.6B), Apache 2.0 (the revision downloaded on 2026-11-21 was not pinned; the hub's current revision that day was `c1899de2`) |
| Training | supervised fine-tuning, 600 steps × 16 lines, lr 1e-5, completion-only loss, float32 master weights with bf16 autocast; **checkpoint at step 400**, chosen on dev by a rule fixed before training; seed 2 |
| Code | commit `c994ade` of [dekunsun/BioEvidenceBench](https://github.com/dekunsun/BioEvidenceBench), `rl/training/stage3_p0.py`; run `rl/training/runs/20261121-2008_sft600s2/` |
| Data | 4,800 training lines (`rl/training/data/p0_train.jsonl`, SHA-256 `0b201974…`) from five books of the IMPACT ground truth on BHL: Butler 1907, Reeve 1849, Horae Societatis Entomologicae Rossicae 1881, Das Chitinskelett von Eosentomon 1913, Piscium querelae et vindiciae 1708 |
| Licences | base model Apache 2.0; expert transcriptions `finebooks/bhl-impact-gt` CC-BY 3.0 (credit: IMPACT project and the Biodiversity Heritage Library); legacy OCR from BHL; all six books are marked not in copyright in BHL's metadata |

## Task and how to use it

Input: one line of legacy BHL OCR with the OCR lines before and after it. Output: the line as the
expert edition prints it. Use the exact prompt `rl/env/task_b_ocr_repair/prompts/repair_v3.txt`
(context lines first, the line to repair last inside `<line>…</line>`), rendered with the tokenizer's
chat template and **thinking off**:

```python
from transformers import AutoModelForCausalLM, AutoTokenizer
tok = AutoTokenizer.from_pretrained("sft_s2")
model = AutoModelForCausalLM.from_pretrained("sft_s2", dtype="bfloat16")
prompt = tok.apply_chat_template(messages, tokenize=False, add_generation_prompt=True, enable_thinking=False)
# messages = [system, user] built from repair_v3.txt, as in rl/training/common_7b.prompt_messages
```

Evaluation decoding: temperature 0.7, top-p 0.8, top-k 20, at most 128 new tokens.

## Results (locked test, scored once; `rl/training/runs/STAGE4_TEST_REPORT.md`)

| | Damaged-word repair | Scientific names | Correct words kept | Format failures |
|---|---|---|---|---|
| In-book test, 500 lines | **0.410** (untrained 0.037) | 0.36 (0.01) | 0.982 (0.921) | 0.7% |
| More in-book test lines, 3,226 | 0.510 (0.038) | 0.44 (0.03) | 0.988 (0.948) | 0.2% |
| Unseen book, French (Cuvier 1835), 500 lines | 0.212 (0.047) | 0.38 on 10 words, descriptive (0.05) | 0.982 (0.921) | 0.2% |

Repair and preservation gains over the untrained model have 95% intervals well above zero on both
test books (paired bootstrap over page blocks); the name gain on Cuvier rests on 10 words. The training data and the test lines come from different pages; Cuvier was never used for
training or development.

## Known problems

- **Changes correct text**: about 1.8% of correct words, sometimes with a language prior the book
  does not follow (`valde` → `valdè`, `l'interieur` → `l'intérieur`), sometimes plain misspellings of
  correct words. Confirmed high-scoring violations of the task: 0.45% of answers on the in-book test.
- **Weaker on other languages and editions**: half the in-book gain on the French book; no ligature
  repaired there.
- **Edition conventions**: part of what it learned is the expert edition's habits (long s, ligatures,
  the line-end hyphen glyph U+2010, letter spacing removed). About 16% of the damaged words in the
  in-book test differ from the OCR only in a dash glyph.
- The evaluation reward has known holes (`rl/REWARD_AUDIT.md` part 2); punctuation is not scored.
- The texts are public and may be in the base model's pre-training data.

## Out of scope

Automatic correction of BHL text without review; other scripts, handwriting, tables; use as evidence
that a scientific name is correct (a repaired name still needs checking against the scan).

Full study: `rl/TRAINING_REPORT.md`, `rl/RELEASE_DECISION.md`.
