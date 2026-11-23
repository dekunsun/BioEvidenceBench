"""本草綱目 case: the fixed variant table and glyph folding (guide v0.2, rule 10).

data/bencao/variant_table.csv lists pairs that may be folded without looking at context:
`glyph_variant` (the same character in another form, 隂/陰) and `taboo_missing_stroke` (𢎞/弘, 𤣥/玄).
Contextual substitutions such as 元 for 玄 are NOT in the table and are never folded: they are scored by
their own metric at gold mentions with normalization_type = taboo_substitution (the author's decision,
2026-11-23). The table is proposed; the author confirms rows in the `confirmed` column.

fold(text) maps every character in the table to one representative of its group (the `standard` of the
first row that names it), so two texts that differ only in table forms fold to the same string. Folding is
for the auxiliary OCR metric only; primary scores compare forms as written.
"""
from __future__ import annotations

import csv
from functools import lru_cache
from pathlib import Path

TABLE = Path(__file__).resolve().parents[1] / "data" / "bencao" / "variant_table.csv"


def rows() -> list[dict]:
    with open(TABLE, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def pairs(types: tuple[str, ...] = ("glyph_variant", "taboo_missing_stroke")) -> set[frozenset]:
    return {frozenset((r["form"], r["standard"])) for r in rows() if r["type"] in types}


@lru_cache(maxsize=1)
def _canon() -> dict[str, str]:
    parent: dict[str, str] = {}

    def find(c: str) -> str:
        while parent.setdefault(c, c) != c:
            c = parent[c]
        return c

    for r in rows():                               # union by row; the first standard seen stays the root
        a, b = find(r["standard"]), find(r["form"])
        if a != b:
            parent[b] = a
    return {c: find(c) for c in parent}


def fold(text: str) -> str:
    m = _canon()
    return "".join(m.get(c, c) for c in text)
