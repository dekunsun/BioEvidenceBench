"""Exploratory (DEVIATIONS.md): does LLM repair work from general knowledge or from having
seen these books?

    python src/memorisation_probe.py make       # perturbed copies of the 16 test pages' expert text
    python src/run_exploratory.py --cond G2 --versions probe_typo,probe_swap [--model ...]
    python src/memorisation_probe.py analyse    # what the model's reading did with each change

Two kinds of change to gold `taxon` and `person` mentions in the expert transcription:
  typo  two neighbouring interior letters swapped ("Lamarck" -> "Lamrack"): a VISIBLE error.
        Putting it back needs only knowledge of the name, not of this book.
  swap  for a binomial, its epithet replaced by the epithet of a binomial printed on ANOTHER test
        page of the same book ("Bulimus calvus" -> "Bulimus turritus"): FLUENT, nothing looks
        wrong. Putting it back is only possible from memory of this page (or from the context
        around the name, e.g. the same name printed again on the page, which is recorded).
For each change the model's G2 `reading` at that place is classed as: restored (the original),
kept (the changed text), other, or not extracted. The text is not a real OCR: the G2 prompt
says it may contain recognition errors, which is what invites a repair.
Writes data/probe/<kind>/<page>.txt (committed: derived from CC-BY 3.0 text, attribution in
data/sample/ATTRIBUTION.md), data/probe/changes.csv, and results/memorisation_probe/.
"""
from __future__ import annotations

import random
import re
import shutil
import sys

import pandas as pd

from common import DATA, ROOT, TEXT
from score import load_gold, norm_value

PROBE = DATA / "probe"
SEED = 20261120


def swap_letters(word: str, rng: random.Random) -> str | None:
    idx = [i for i in range(1, len(word) - 2) if word[i].isalpha() and word[i + 1].isalpha()
           and word[i].lower() != word[i + 1].lower()]
    if not idx:
        return None
    i = rng.choice(idx)
    return word[:i] + word[i + 1] + word[i] + word[i + 2:]


def make() -> None:
    rng = random.Random(SEED)
    split = pd.read_csv(DATA / "sample_split.csv").query("split == 'test'")
    book_of = dict(zip(split.PageID, split.book))
    g = load_gold(ROOT / "gold" / "gold_mentions_gloria_test.csv")
    g = g[g.field.isin(["taxon", "person"])].copy()
    g["book"] = g.page_id.map(book_of)
    binom = g[(g.field == "taxon") & g.text.str.fullmatch(r"[A-Z][a-zA-Z]+\.? [a-z]{4,}")]
    changes = []
    for kind in ("typo", "swap"):
        (PROBE / kind).mkdir(parents=True, exist_ok=True)
        for pid in sorted(split.PageID):
            src = (DATA / "sample" / "expert" / f"{pid}.txt").read_text(encoding="utf-8")
            if kind == "typo":
                cands = g[(g.page_id == pid) & g.text.str.fullmatch(r"[A-Za-z][A-Za-z. ]{5,}")]
            else:
                cands = binom[binom.page_id == pid]
            picks = cands.sample(min(6, len(cands)), random_state=rng.randint(0, 10**6)) if len(cands) else cands
            edits = []
            for r in picks.itertuples():
                if kind == "typo":
                    words = r.text.split()
                    j = max(range(len(words)), key=lambda k: len(words[k]))
                    new_w = swap_letters(words[j], rng)
                    if not new_w:
                        continue
                    new = " ".join(words[:j] + [new_w] + words[j + 1:])
                else:
                    genus, ep = r.text.split(" ", 1)
                    others = binom[(binom.book == r.book) & (binom.page_id != pid)].text.str.split(" ").str[1]
                    others = [o for o in sorted(set(others)) if o != ep and o not in src]
                    if not others:
                        continue
                    new = f"{genus} {rng.choice(others)}"
                edits.append((r.start, r.end, r.text, new, r.field))
            out = src
            for s, e, old, new, field in sorted(edits, reverse=True):     # right to left keeps offsets valid
                out = out[:s] + new + out[e:]
            shift = 0
            for s, e, old, new, field in sorted(edits):
                changes.append({"kind": kind, "page_id": pid, "field": field, "orig_start": s, "orig": old,
                                "changed": new, "new_start": s + shift,
                                "original_elsewhere_on_page": src.count(old) > 1})
                shift += len(new) - len(old)
            (PROBE / kind / f"{pid}.txt").write_text(out, encoding="utf-8")
            # the runner reads non-sample versions from data/text/<version>/
            dst = TEXT / f"probe_{kind}"
            dst.mkdir(parents=True, exist_ok=True)
            shutil.copy(PROBE / kind / f"{pid}.txt", dst / f"{pid}.txt")
    pd.DataFrame(changes).to_csv(PROBE / "changes.csv", index=False)
    c = pd.DataFrame(changes)
    print(c.groupby(["kind", "field"]).size())


def analyse() -> None:
    ch = pd.read_csv(PROBE / "changes.csv")
    rows = []
    for d in sorted((ROOT / "results").glob("*_explore_G2*")):
        m = pd.read_csv(d / "test_mentions.csv", keep_default_na=False)
        m = m[m.version.astype(str).str.startswith("probe_")]
        if m.empty:
            continue
        model = __import__("json").loads((d / "config.json").read_text())["model"]
        for c in ch.itertuples():
            v = f"probe_{c.kind}"
            mm = m[(m.version == v) & (m.page_id == c.page_id)]
            end = c.new_start + len(c.changed)
            hit = mm[(pd.to_numeric(mm.start, errors="coerce") < end) & (pd.to_numeric(mm.end, errors="coerce") > c.new_start)]
            if hit.empty:
                outcome = "not_extracted"
            else:
                reading = norm_value(str(hit.iloc[0].value))
                outcome = ("restored" if norm_value(c.orig) in reading or reading in norm_value(c.orig) and reading
                           else "kept" if norm_value(c.changed) in reading else "other")
                if norm_value(c.orig) == reading:
                    outcome = "restored"
                elif norm_value(c.changed) == reading:
                    outcome = "kept"
            rows.append({"model": model, **c._asdict(), "outcome": outcome})
    if not rows:
        sys.exit("No G2 run on probe_typo / probe_swap yet.")
    r = pd.DataFrame(rows).drop(columns="Index")
    out = ROOT / "results" / "memorisation_probe"
    out.mkdir(parents=True, exist_ok=True)
    r.to_csv(out / "outcomes.csv", index=False)
    t = r.groupby(["model", "kind", "outcome"]).size().unstack(fill_value=0)
    t["n"] = t.sum(axis=1)
    t2 = r[r.kind == "swap"].groupby(["model", "original_elsewhere_on_page", "outcome"]).size().unstack(fill_value=0)
    lines = ["# Memorisation probe (exploratory)", "",
             "Changes to gold names in the 16 test pages' expert text, then G2 repair. `restored` on a *swap* "
             "(a fluent, error-free substitution) can only come from memory of the page, or from the original "
             "name printed elsewhere on the same page (split below).", "",
             t.to_markdown(), "", "Swaps, by whether the original name is printed elsewhere on the page:", "",
             t2.to_markdown(), ""]
    (out / "REPORT.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    {"make": make, "analyse": analyse}[sys.argv[1]]()
