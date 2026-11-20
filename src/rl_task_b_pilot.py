"""Task B, steps 1-3 of the build order (rl/PLAN_zh.md section 6; Gloria's order of 2026-11-20):

  1. a few Reeve training pages end to end: do legacy OCR and the expert transcription align?
  2. the two word alignments and Reward v1.0 with its diagnostic fields (src/rl_task_b.py)
  3. zero-cost adversarial checks of the reward on those pages

    python src/rl_task_b_pilot.py

No model is called. Writes rl/env/task_b_ocr_repair/pilot/{units.csv, reward_checks.csv, REPORT.md}.
"""
from __future__ import annotations

import random
import re

import pandas as pd

import rl_task_b as T
from common import ROOT

PAGES = [8966754, 8966753, 8966752, 8966751]     # Reeve, train split, text-rich (seq 13-16)
OUT = ROOT / "rl" / "env" / "task_b_ocr_repair" / "pilot"


def ocr_words_kept(unit: dict, keep) -> str:
    """The reference line, but with the OCR's (damaged) reading put back for every damaged
    reference word for which keep(is_name) is True. Used to build partial repairs."""
    rows, _ = T.word_status(unit["target"], unit["input"])
    out, last = [], 0
    for r, is_name in zip(rows, unit["name_word_flags"]):
        out.append(unit["target"][last:r["start"]])
        out.append(r["aligned"] if (not r["ok"] and keep(is_name) and r["aligned"]) else r["word"])
        last = r["end"]
    out.append(unit["target"][last:])
    return "".join(out)


def attacks(unit: dict) -> dict[str, tuple[str, str]]:
    """name -> (output, what the reward should do). Expectations follow rl/PLAN_zh.md 6.3-6.5."""
    t, i = unit["target"], unit["input"]
    damaged = unit["n_damaged"] > 0
    a = {
        "perfect": (t, "1.0"),
        "identity (return the OCR)": (i, "0 if damaged, 1 if clean"),
        "empty": ("", "0, format invalid"),
        "two lines": (t + "\n" + t, "0, integrity invalid"),
        "commentary prefix": ("Corrected line: " + t, "below 1 (extra words)"),
        "lower-cased": (t.lower(), "below 1 unless the line is already lower case"),
        "one correct word changed": (re.sub(r"\b([a-z]{4,})\b", lambda m: m.group(1) + "e", t, count=1),
                                     "below 1 (a correct word broken)"),
    }
    if damaged:
        a["names left unrepaired"] = (ocr_words_kept(unit, lambda is_name: is_name),
                                      "repair rate without the name words")
        a["only names repaired"] = (ocr_words_kept(unit, lambda is_name: not is_name),
                                    "repair rate of the name words only")
    if re.search("[æœÆŒ]", t):
        a["ligature letters written out"] = (t.replace("æ", "ae").replace("œ", "oe").replace("Æ", "Ae")
                                             .replace("Œ", "Oe"), "below 1 (spelling not kept)")
    return a


def main() -> None:
    units = [u for p in PAGES for u in T.line_pairs(p)]
    ud = pd.DataFrame(units)
    OUT.mkdir(parents=True, exist_ok=True)
    keep = ["page_id", "line_no", "valid", "why_invalid", "coverage", "span_ratio", "similarity",
            "n_words", "n_damaged", "n_name_damaged", "input", "target"]
    ud[keep].to_csv(OUT / "units.csv", index=False)
    v = [u for u in units if u["valid"]]

    rows = []
    rng = random.Random(20261120)
    sample = rng.sample([u for u in v if u["n_damaged"] > 0], 25) + rng.sample([u for u in v if u["n_damaged"] == 0], 10)
    sample += [u for u in v if re.search("[æœ]", u["target"])][:5]
    sample += [u for u in v if u["n_name_damaged"] > 0][:10]
    for u in sample:
        for name, (out, expect) in attacks(u).items():
            if out == u["target"] and name != "perfect":
                continue                      # the attack changed nothing on this line
            d = T.reward(u, out)
            rows.append({"page_id": u["page_id"], "line_no": u["line_no"], "attack": name, "expect": expect,
                         "n_damaged": u["n_damaged"], "n_name_damaged": u["n_name_damaged"]} | d)
    rd = pd.DataFrame(rows)
    rd.to_csv(OUT / "reward_checks.csv", index=False)

    summ = rd.groupby("attack").agg(cases=("reward", "size"), mean_reward=("reward", "mean"),
                                    min_reward=("reward", "min"), max_reward=("reward", "max"),
                                    format_invalid=("format_valid", lambda s: int((~s).sum())),
                                    integrity_invalid=("integrity_valid", lambda s: int((~s).sum()))).round(3)
    print(summ.to_string())
    dist = pd.Series([u["n_damaged"] for u in v]).clip(upper=6).value_counts().sort_index()
    print("damaged words per valid line (6 = 6+):", dist.to_dict())
    print("valid", len(v), "of", len(units), "| invalid:", ud[~ud.valid].why_invalid.tolist())
    (OUT / "summary.txt").write_text(summ.to_string() + "\n\ndamaged words per valid line (6 = 6+): "
                                     + str(dist.to_dict()) + f"\nvalid {len(v)} of {len(units)}\n", encoding="utf-8")


if __name__ == "__main__":
    main()
