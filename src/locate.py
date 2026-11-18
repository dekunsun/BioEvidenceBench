"""Turn model output into spans of the source text.

The model never supplies the final value. For each mention we find where it
is in the exact text the model was given, and slice the value from there.
Each mention gets a status:

G1 (line + quote)
  exact              quote found verbatim in the cited line
  wrong_line         quote found verbatim, but on a different line
  silent_correction  no verbatim match; a close match (>= FUZZY_MIN) exists in
                     the cited line. The model "fixed" or altered the text.
                     The value is sliced from the source, never taken from the quote.
  invalid_evidence   line out of range, or nothing close in that line

G0 (value only; aligned afterwards)
  exact              value found verbatim on the page
  case_variant       found only when ignoring case
  fuzzy              close match (>= FUZZY_MIN) somewhere on the page: the model
                     normalised or corrected the text
  not_found          nothing close on the page: a value with no support in the source

`start`/`end` are character offsets into the page text the model saw (the
file under data/text/<version>/), Python slice convention.
"""
from __future__ import annotations

from rapidfuzz import fuzz

FUZZY_MIN = 85.0


def line_starts(text: str) -> list[int]:
    starts, pos = [], 0
    for line in text.split("\n"):
        starts.append(pos)
        pos += len(line) + 1
    return starts


def _fuzzy(needle: str, hay: str) -> tuple[float, int, int]:
    if not needle or not hay:
        return 0.0, 0, 0
    a = fuzz.partial_ratio_alignment(needle, hay)
    return a.score, a.dest_start, a.dest_end


def locate_g1(text: str, line: int, quote: str) -> dict:
    lines = text.split("\n")
    starts = line_starts(text)
    if not (1 <= line <= len(lines)) or not quote:
        return {"status": "invalid_evidence", "start": None, "end": None, "score": 0.0}
    l_text, l_start = lines[line - 1], starts[line - 1]
    i = l_text.find(quote)
    if i != -1:
        return {"status": "exact", "start": l_start + i, "end": l_start + i + len(quote), "score": 100.0}
    j = text.find(quote)
    if j != -1:
        return {"status": "wrong_line", "start": j, "end": j + len(quote), "score": 100.0}
    score, a, b = _fuzzy(quote, l_text)
    if score >= FUZZY_MIN:
        return {"status": "silent_correction", "start": l_start + a, "end": l_start + b, "score": round(score, 1)}
    return {"status": "invalid_evidence", "start": None, "end": None, "score": round(score, 1)}


def locate_g0(text: str, value: str, nth: int = 0) -> dict:
    """nth: this is the nth time the model reported this exact value on the
    page, so repeated mentions map to successive occurrences."""
    if not value:
        return {"status": "not_found", "start": None, "end": None, "score": 0.0}
    hits, i = [], text.find(value)
    while i != -1:
        hits.append(i)
        i = text.find(value, i + 1)
    if hits:
        k = hits[min(nth, len(hits) - 1)]
        return {"status": "exact", "start": k, "end": k + len(value), "score": 100.0}
    low = text.lower().find(value.lower())
    if low != -1:
        return {"status": "case_variant", "start": low, "end": low + len(value), "score": 100.0}
    score, a, b = _fuzzy(value, text)
    if score >= FUZZY_MIN:
        return {"status": "fuzzy", "start": a, "end": b, "score": round(score, 1)}
    return {"status": "not_found", "start": None, "end": None, "score": round(score, 1)}


def locate_all(text: str, condition: str, mentions: list[dict]) -> list[dict]:
    out, seen = [], {}
    for m in mentions:
        if condition == "G1":
            r = locate_g1(text, int(m.get("line", 0)), m.get("quote", ""))
            model_text = m.get("quote", "")
        else:
            key = (m.get("field"), m.get("value"))
            r = locate_g0(text, m.get("value", ""), seen.get(key, 0))
            seen[key] = seen.get(key, 0) + 1
            model_text = m.get("value", "")
        value = text[r["start"]:r["end"]] if r["start"] is not None else None
        out.append({"field": m.get("field"), "line": m.get("line"), "model_text": model_text,
                    "value": value, **r})
    return out
