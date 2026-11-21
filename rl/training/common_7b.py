"""Shared pieces for module 7b (runs on the GPU pod and here on CPU).

- `render_prompt`: the ONE prompt renderer for every stage (Base, SFT, GRPO, evaluation). It applies
  the model's chat template with `enable_thinking=False` (METRICS.md 2a) and returns a plain string,
  so no trainer renders prompts its own way.
- `score_answer`: Reward v1.3 on the raw answer and on the fixed clean-up (`format_cleanup`).
- `load_items` / `write_items`: the item files shipped with the repo (JSONL, one line per item).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

import rl_task_b as T  # noqa: E402

PROMPTS = ROOT / "rl" / "env" / "task_b_ocr_repair" / "prompts"
PROMPT_VERSION = "repair_v3"          # dev decision 2026-11-21 (runs/20261121-1756_promptcmp/REPORT.md); never changed on test
PROMPT_FILE = PROMPTS / f"{PROMPT_VERSION}.txt"
MODEL_ID = "Qwen/Qwen3-0.6B"          # the post-trained instruct model (Gloria, 2026-11-21)
BOOKS = {"Butler": ("Birds of Great Britain and Ireland, vol. 2", 1907, "English"),
         "Reeve": ("Conchologia iconica, vol. 5", 1849, "Latin and English"),
         "Trudy": ("Trudy Russkago entomologicheskago obshchestva / Horae Societatis Entomologicae Rossicae, vol. 16",
                   1881, "German, French, Latin and Russian"),
         "Chitinskelett": ("Das Chitinskelett von Eosentomon (Zoologica 64)", 1912, "German"),
         "Piscium": ("Piscium querelae et vindiciae", 1708, "Latin"),
         # held-out book, test only (BHL item 25923: title, volume, year and language FRE from the BHL metadata)
         "Cuvier": ("Histoire naturelle des poissons, vol. 10", 1835, "French")}


def prompt_messages(item: dict, version: str = PROMPT_VERSION) -> list[dict]:
    text = (PROMPTS / f"{version}.txt").read_text(encoding="utf-8")
    system = text.split("=== system ===\n", 1)[1].split("=== user ===\n", 1)[0].strip()
    user = text.split("=== user ===\n", 1)[1].strip()
    title, year, lang = BOOKS[item["book"]]
    return [{"role": "system", "content": system},
            {"role": "user", "content": user.format(book_title=title, year=year, language=lang, prev=item["prev"],
                                                    line=item["input"], next=item["next"])}]


def render_prompt(tokenizer, item: dict, version: str = PROMPT_VERSION) -> str:
    """The rendered prompt string, thinking off. Every stage calls this and nothing else."""
    return tokenizer.apply_chat_template(prompt_messages(item, version), tokenize=False, add_generation_prompt=True,
                                         enable_thinking=False)


def run_on(item: dict, answer: str) -> str:
    """How an answer relates to the line boundary (diagnostic): 'within' the line's length, or longer
    and containing the next line, the previous line, both, or other text."""
    import re
    norm = lambda s: re.sub(r"\s+", " ", s or "").strip().lower()
    o = norm(answer)
    if len(o) <= 1.5 * len(item["target"]):
        return "within"
    nx, pv = norm(item["next"])[:15], norm(item["prev"])[:15]
    has_n, has_p = bool(nx) and nx in o, bool(pv) and pv in o
    return "next" if has_n and not has_p else "previous" if has_p and not has_n else "both" if has_n else "other"


def score_answer(item: dict, answer: str) -> dict:
    """Raw and post-processed scores for one answer (METRICS.md section 3)."""
    raw = T.reward(item, answer)
    clean = T.format_cleanup(answer)
    post = T.reward(item, clean)
    out = {"reward": raw["reward"], "format_valid": raw["format_valid"], "format_reason": raw["format_reason"],
           "repaired": raw["repaired_words"], "broken": raw["damaged_correct_words"], "extra": raw["extra_words"],
           "reward_post": post["reward"], "repaired_post": post["repaired_words"],
           "broken_post": post["damaged_correct_words"], "has_think": "<think" in (answer or "").lower()}
    for tag, d in (("", raw), ("_post", post)):   # fields for the primary metrics (METRICS.md section 3)
        out["gated" + tag] = not (d["format_valid"] and d["integrity_valid"] and d["alignment_valid"])
        out["name_repaired" + tag] = d["scientific_name_repairs"]
        out["preserved" + tag] = d["preserved_correct_words"]
    return out


def primary_metrics(items: list[dict], rows: list[dict]) -> dict:
    """Pooled (micro) primary metrics over answers `rows` (each has `item_id` and score_answer fields):
    damaged-word repair rate, scientific-name exact recovery, correct-word preservation, format
    failure rate, mean reward, pass rate; raw and post-processed. Gated answers repair and keep
    nothing (their words count in the denominators)."""
    by_id = {it["item_id"]: it for it in items}
    dmg = sum(by_id[r["item_id"]]["n_damaged"] for r in rows)
    names = sum(by_id[r["item_id"]].get("n_name_damaged") or 0 for r in rows)
    # words the OCR had right, case-only differences included (copying the OCR keeps all of them)
    correct = sum(by_id[r["item_id"]]["n_words"] - by_id[r["item_id"]]["n_damaged"] for r in rows)
    n = len(rows)
    out = {"answers": n, "damaged_words": dmg, "name_words": names, "correct_words": correct}
    for tag in ("", "_post"):
        out["repair_rate" + tag] = round(sum(r["repaired" + tag] for r in rows) / dmg, 4) if dmg else None
        out["name_recovery" + tag] = round(sum(r["name_repaired" + tag] for r in rows) / names, 4) if names else None
        out["preservation" + tag] = round(sum(r["preserved" + tag] for r in rows) / correct, 4) if correct else None
        out["format_failure" + tag] = round(sum(r["gated" + tag] for r in rows) / n, 4) if n else None
        out["mean_reward" + tag] = round(sum(r["reward" + tag] for r in rows) / n, 4) if n else None
        out["pass_rate" + tag] = round(sum(r["reward" + tag] == 1.0 for r in rows) / n, 4) if n else None
    return out


def load_items(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.open(encoding="utf-8")]


def write_items(items: list[dict], path: Path) -> None:
    keep = ("item_id", "book", "page_id", "line_no", "split", "target", "input", "prev", "next", "n_words",
            "n_damaged", "n_damaged_reading", "n_case_only", "n_name_damaged", "damaged", "name_word_flags",
            "damage_class")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for it in items:
            f.write(json.dumps({k: it.get(k) for k in keep}, ensure_ascii=False) + "\n")
