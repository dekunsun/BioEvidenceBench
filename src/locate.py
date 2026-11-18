"""Turn model output into spans of the source text.

The model never supplies the final value. For each mention we find where it
is in the exact text the model was given, and slice the value from there.
Each mention gets a status:

G1 (line + quote)
  exact              quote found verbatim in the cited line
  cross_line         quote found starting in the cited line once line breaks,
                     indentation and end-of-line hyphenation are ignored (the
                     mention runs onto the next line). Valid evidence.
  wrong_line         quote found verbatim, but on a different line
  silent_correction  no verbatim match; a close match (>= FUZZY_MIN) exists in
                     the cited line. The model "fixed" or altered the text.
                     The value is sliced from the source, never taken from the quote.
  invalid_evidence   line out of range, or nothing close in that line

G0 (value only; aligned afterwards)
  exact              value found verbatim on the page
  case_variant       found only when ignoring case
  layout_variant     found once line breaks, indentation and end-of-line
                     hyphenation are ignored (in either text), e.g. the page has
                     "blak-<newline>istoni" and the model wrote "blakistoni".
                     The value is still the source's own characters.
  fuzzy              close match (>= FUZZY_MIN) somewhere on the page: the model
                     normalised or corrected the text
  not_found          nothing close on the page: a value with no support in the source

Line-number labels such as "L074|" that a model copies from our numbered
input are removed from its text before locating (they cannot be source text);
`had_line_label` records that it happened.

`start`/`end` are character offsets into the page text the model saw (the
file under data/text/<version>/), Python slice convention.
"""
from __future__ import annotations

import re

from rapidfuzz import fuzz

FUZZY_MIN = 85.0
_LINE_LABEL = re.compile(r"\s*L\d+\|\s?")
_HYPHENS = "-\u2010\u00ad"


def strip_line_labels(s: str) -> tuple[str, bool]:
    out = _LINE_LABEL.sub(" ", s)
    return out, out != s


def flatten(text: str, mode: str) -> tuple[str, list[int]]:
    """Text with layout removed, plus a map from each kept char to its offset.

    Every run of whitespace (including line breaks) becomes one space. A hyphen
    at the end of a line is handled by `mode`:
      "join"         dropped with the break: "blak-\nistoni" -> "blakistoni"
      "hyphen"       kept, break dropped:    "Hedge-\nSparrow" -> "Hedge-Sparrow"
      "hyphen_space" kept, break as a space: "blak-\nistoni" -> "blak- istoni"
    All three are tried, because a printed line-end hyphen can be a break
    inside a word or a real hyphen, and models write either form.
    """
    out, idx, i, n = [], [], 0, len(text)
    while i < n:
        ch = text[i]
        if ch in _HYPHENS:
            j = i + 1
            while j < n and text[j] in " \t":
                j += 1
            if j < n and text[j] == "\n":
                k = j
                while k < n and text[k].isspace():
                    k += 1
                if mode == "join":
                    i = k
                    continue
                out.append(ch); idx.append(i)
                if mode == "hyphen_space":
                    out.append(" "); idx.append(j)
                i = k
                continue
        if ch.isspace():
            k = i
            while k < n and text[k].isspace():
                k += 1
            if out and out[-1] != " ":
                out.append(" "); idx.append(i)
            i = k
            continue
        out.append(ch); idx.append(i)
        i += 1
    return "".join(out), idx


def _flat_find(text: str, needle: str, region: tuple[int, int] | None = None,
               ignore_case: bool = False) -> tuple[int, int] | None:
    """Find needle in text ignoring layout; return original (start, end)."""
    for mode in ("join", "hyphen", "hyphen_space"):
        flat, idx = flatten(text, mode)
        nd = flatten(needle, mode)[0].strip()
        if not nd:
            return None
        hay, nd2 = (flat.lower(), nd.lower()) if ignore_case else (flat, nd)
        k = hay.find(nd2)
        while k != -1:
            start, end = idx[k], idx[k + len(nd2) - 1] + 1
            if region is None or region[0] <= start < region[1]:
                return start, end
            k = hay.find(nd2, k + 1)
    return None


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
    hit = _flat_find(text, quote, region=(l_start, l_start + len(l_text) + 1))
    if hit:
        return {"status": "cross_line", "start": hit[0], "end": hit[1], "score": 100.0}
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
    hit = _flat_find(text, value) or _flat_find(text, value, ignore_case=True)
    if hit:
        return {"status": "layout_variant", "start": hit[0], "end": hit[1], "score": 100.0}
    score, a, b = _fuzzy(value, text)
    if score >= FUZZY_MIN:
        return {"status": "fuzzy", "start": a, "end": b, "score": round(score, 1)}
    return {"status": "not_found", "start": None, "end": None, "score": round(score, 1)}


def locate_all(text: str, condition: str, mentions: list[dict]) -> list[dict]:
    out, seen = [], {}
    for m in mentions:
        model_text = m.get("quote" if condition == "G1" else "value", "") or ""
        clean, had_label = strip_line_labels(model_text)
        clean = clean.strip() if had_label else clean
        if condition == "G1":
            r = locate_g1(text, int(m.get("line", 0)), clean)
        else:
            key = (m.get("field"), clean)
            r = locate_g0(text, clean, seen.get(key, 0))
            seen[key] = seen.get(key, 0) + 1
        value = text[r["start"]:r["end"]] if r["start"] is not None else None
        out.append({"field": m.get("field"), "line": m.get("line"), "model_text": model_text,
                    "had_line_label": had_label, "value": value, **r})
    return out
