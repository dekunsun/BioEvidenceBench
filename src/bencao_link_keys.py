"""本草綱目 pilot: lookup keys for place mentions (guide v0.5 rule 16), kept apart from the mention spans.

    python src/bencao_link_keys.py     -> data/bencao/locality_link_keys.csv

The gold span keeps what is written (`上黨山谷`); the key is what a historical gazetteer is queried with
(`上黨`). Keys are derived by one fixed rule, never by a model: a generic terrain word written after a name
(GENERIC below) is removed; everything else is kept as written. A single 山 stays, because there it is part
of a mountain's name (`積沙山`, `紫團山`). The file has an empty `confirmed` column for the author: a
derived key is a proposal until she confirms it; the gold file itself is not touched.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
GENERIC = ["川谷", "山谷"]          # "river valleys of", "mountain valleys of": the habitat, not the place name


def link_key(text: str) -> tuple[str, str]:
    t = text.replace("\n", "")
    for g in GENERIC:
        if t.endswith(g) and len(t) > len(g):
            return t[: -len(g)], f"generic word {g} removed"
    return t, "as written"


def main() -> None:
    gold = pd.read_csv(ROOT / "gold" / "gold_mentions_bencao_gloria.csv", keep_default_na=False)
    loc = gold[gold.field == "locality"].copy()
    loc["mention_text"] = loc.text.str.replace("\n", "", regex=False)
    rows = []
    for t, g in loc.groupby("mention_text", sort=False):
        key, how = link_key(t)
        rows.append({"mention_text": t, "link_key": key, "derived_by": how, "mentions": len(g),
                     "pages": " ".join(sorted(set(g.page_id))),
                     "expert_pending": "yes" if (g.adjudication == "expert_pending").any() else "",
                     "confirmed": "", "note": ""})
    out = ROOT / "data" / "bencao" / "locality_link_keys.csv"
    pd.DataFrame(rows).to_csv(out, index=False)
    d = pd.DataFrame(rows)
    print(out, len(d), "distinct place mentions;", (d.derived_by != "as written").sum(), "keys differ from the span")
    print(d[d.derived_by != "as written"][["mention_text", "link_key", "pages"]].to_string(index=False))


if __name__ == "__main__":
    main()
