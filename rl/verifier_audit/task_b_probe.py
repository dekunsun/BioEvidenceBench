"""Task B reward audit (plan 6.5): constructed answers scored by Reward v1.3 and by 1 - CER.

    python rl/verifier_audit/task_b_probe.py

Each probe is built by code from the expert line (target) and the OCR (input) of the 585 dev lines
used to choose checkpoints in module 7b (`rl/training/data/p0_dev_eval.jsonl` + `p0_dev_names.jsonl`;
dev only, never test). A probe is a hole if it violates the task (adds, drops or changes text the
page does not support) and still scores high, above the honest answer it competes with, or both.
Writes rl/verifier_audit/task_b/probe_scores.csv and prints the summary table.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pandas as pd
import rapidfuzz.distance.Levenshtein as Lev

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "rl" / "training"))
import common_7b as C  # noqa: E402

T = C.T
OUT = ROOT / "rl" / "verifier_audit" / "task_b"


def cer_reward(it: dict, ans: str) -> float:
    return 1.0 - min(1.0, Lev.distance(T.nfc(ans or "").strip(), it["target"]) / max(1, len(it["target"])))


def replace_words(it: dict, which) -> str:
    """The OCR with the damaged reference words selected by `which(i, row)` written correctly."""
    rows, _ = T.word_status(it["target"], it["input"])
    s = it["input"]
    flags = it.get("name_word_flags") or []
    for i, r in sorted(enumerate(rows), key=lambda x: -(x[1]["span"] or (0, 0))[0]):
        if T.word_kind(r) == "damaged" and r["span"] and which(i, r, i < len(flags) and flags[i]):
            a, b = r["span"]
            s = s[:a] + r["word"] + s[b:]
    return s


def drop_damaged(text_from: str, it: dict, use_target: bool) -> str:
    rows, _ = T.word_status(it["target"], it["input"])
    dmg = [r for r in rows if T.word_kind(r) == "damaged"]
    if use_target:
        s = it["target"]
        for r in sorted(dmg, key=lambda r: -r["start"]):
            s = s[:r["start"]] + s[r["end"]:]
    else:
        s = it["input"]
        for r in sorted((r for r in dmg if r["span"]), key=lambda r: -r["span"][0]):
            s = s[:r["span"][0]] + s[r["span"][1]:]
    return re.sub(r"\s{2,}", " ", s).strip()


def modernise(s: str) -> str:
    return s.replace("ſ", "s").replace("æ", "ae").replace("œ", "oe").replace("Æ", "Ae").replace("Œ", "Oe")


def swap_letters(s: str) -> str:
    """Change one correct word: swap two inner letters of the longest word."""
    ws = sorted(T.words(s), key=lambda w: -(w[1] - w[0]))
    if not ws or ws[0][1] - ws[0][0] < 4:
        return s + "x"
    a, b, w = ws[0]
    return s[:a] + w[0] + w[2] + w[1] + w[3:] + s[b:]


PROBES = {
    "honest: expert line": lambda it: it["target"],
    "copy the OCR": lambda it: it["input"],
    "empty": lambda it: "",
    "fix ordinary words only, leave names damaged": lambda it: replace_words(it, lambda i, r, name: not name),
    "fix names only": lambda it: replace_words(it, lambda i, r, name: name),
    "expert line, damaged words deleted": lambda it: drop_damaged("", it, True),
    "OCR, damaged words deleted": lambda it: drop_damaged("", it, False),
    "expert line + one invented word": lambda it: it["target"] + " the",
    "expert line + two invented words": lambda it: it["target"] + " of the",
    "expert line, punctuation removed": lambda it: re.sub(r"\s{2,}", " ", re.sub(r"[^\w\s]", "", it["target"])).strip(),
    "expert line, all lower case": lambda it: it["target"].lower(),
    "expert line, modernised (ſ→s, æ→ae, œ→oe)": lambda it: modernise(it["target"]),
    "expert line, one correct word misspelt": lambda it: swap_letters(it["target"]),
    "expert line + next line (two lines)": lambda it: it["target"] + "\n" + it["next"],
    "expert line + next line (run-on, one line)": lambda it: it["target"] + " " + it["next"],
    "expert line written twice": lambda it: it["target"] + " " + it["target"],
    "commentary prefix": lambda it: "Corrected line: " + it["target"],
}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    items = [it for f in ("p0_dev_eval", "p0_dev_names") for it in C.load_items(ROOT / "rl" / "training" / "data" / f"{f}.jsonl")]
    assert all(it["split"] == "dev" for it in items)
    rows = []
    for it in items:
        cls = "clean" if it["n_damaged"] == 0 else "damaged, name" if it["n_name_damaged"] else "damaged, no name"
        for name, f in PROBES.items():
            a = f(it)
            r = T.reward(it, a)
            rows.append({"item_id": it["item_id"], "line": cls, "probe": name, "reward": r["reward"],
                         "cer_reward": round(cer_reward(it, a), 4), "same_as_target": a.strip() == it["target"].strip(),
                         "format_reason": r["format_reason"]})
    d = pd.DataFrame(rows)
    d.to_csv(OUT / "probe_scores.csv", index=False)
    honest = d[d.probe == "honest: expert line"].set_index("item_id")
    d["beats_honest_v13"] = d.reward > d.item_id.map(honest.reward)
    d["high_v13"] = d.reward >= 0.75
    t = d.groupby(["probe", "line"]).agg(v13=("reward", "mean"), cer=("cer_reward", "mean"),
                                         high_v13=("high_v13", "mean"), identical=("same_as_target", "mean"))
    t = t.round(3).unstack("line")
    order = list(PROBES)
    t = t.reindex(order)
    t.to_csv(OUT / "probe_summary.csv")
    with pd.option_context("display.width", 250):
        print(t.to_string())
    print("lines:", d.drop_duplicates("item_id").line.value_counts().to_dict())
    print("any probe beating the honest answer under v1.3:", int(d.beats_honest_v13.sum()))


if __name__ == "__main__":
    main()
