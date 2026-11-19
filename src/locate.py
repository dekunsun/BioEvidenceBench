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

Which occurrence? A G0 value comes without a position, and a G1 quote only names its
line (a whole paragraph in the modern OCR text), so a string printed several times has
to be assigned to one of its occurrences. `locate_all` places longer
values first and gives each value the first occurrence that is a whole word and is not
already taken by another mention. So "Jackdaw" is not placed inside "Jackdaws", "Crow"
not inside an already placed "Hooded Crow", and a person "Lilford" and a place
"Lilford" get different occurrences. What remains ambiguous by nature (a heading and a
running head with the same text) stays ambiguous: that is a cost of having no evidence.

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
               ignore_case: bool = False, skip: set[int] | None = None) -> tuple[int, int] | None:
    """Find needle in text ignoring layout; return original (start, end).
    skip: start positions already used by earlier mentions, not to be returned again."""
    for mode in ("join", "hyphen", "hyphen_space"):
        flat, idx = flatten(text, mode)
        nd = flatten(needle, mode)[0].strip()
        if not nd:
            return None
        hay, nd2 = (flat.lower(), nd.lower()) if ignore_case else (flat, nd)
        k = hay.find(nd2)
        while k != -1:
            start, end = idx[k], idx[k + len(nd2) - 1] + 1
            if (region is None or region[0] <= start < region[1]) and not (skip and start in skip):
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


def _find_all(hay: str, needle: str) -> list[int]:
    hits, i = [], hay.find(needle)
    while i != -1:
        hits.append(i)
        i = hay.find(needle, i + 1)
    return hits


def locate_g1(text: str, line: int, quote: str, nth: int = 0, taken: list | None = None) -> dict:
    """nth: this is the nth time the model gave this exact quote for this line
    (and field), so a word printed several times in one line maps to its
    successive occurrences instead of always the first. If the model gives the
    quote more often than the line contains it, the extra ones stay on the last
    occurrence (and show up as duplicate spans).

    taken: spans already given to other mentions. When given, the quote goes to
    its first occurrence in the line that is a whole word (if it has any) and
    overlaps none of them, exactly as for G0. This matters when a whole
    paragraph is one line, as in the modern OCR text."""
    lines = text.split("\n")
    starts = line_starts(text)
    if not (1 <= line <= len(lines)) or not quote:
        return {"status": "invalid_evidence", "start": None, "end": None, "score": 0.0}
    l_text, l_start = lines[line - 1], starts[line - 1]
    hits = _find_all(l_text, quote)
    if taken is not None and hits:
        n = len(quote)
        whole = [h for h in hits if _whole_word(l_text, h, n)]
        free = [h for h in (whole or hits)
                if not any(l_start + h < b and a < l_start + h + n for a, b in taken)]
        if free:
            return {"status": "exact", "start": l_start + free[0], "end": l_start + free[0] + n, "score": 100.0}
    if hits:
        i = hits[min(nth, len(hits) - 1)]
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


def _whole_word(text: str, i: int, n: int) -> bool:
    before = text[i - 1] if i > 0 else " "
    after = text[i + n] if i + n < len(text) else " "
    return not (before.isalnum() or after.isalnum())


def locate_g0(text: str, value: str, nth: int = 0, taken: list | None = None) -> dict:
    """nth: this is the nth time the model reported this exact value on the
    page, so repeated mentions map to successive occurrences. When the value is
    reported more often than it is printed exactly, a further occurrence broken
    by layout (such as "Ja-" / "maica" for "Jamaica") is used before falling
    back to the last exact one.

    taken: spans already given to other mentions, as (start, end). When given,
    the value goes to its first exact occurrence that is a whole word (if it has
    any) and overlaps none of them; only when there is no such occurrence do the
    rules above apply."""
    if not value:
        return {"status": "not_found", "start": None, "end": None, "score": 0.0}
    hits = _find_all(text, value)
    if taken is not None and hits:
        n = len(value)
        whole = [h for h in hits if _whole_word(text, h, n)]
        free = [h for h in (whole or hits) if not any(h < b and a < h + n for a, b in taken)]
        if free:
            return {"status": "exact", "start": free[0], "end": free[0] + n, "score": 100.0}
    if hits and nth >= len(hits):
        extra = _flat_find(text, value, skip=set(hits))
        if extra:
            return {"status": "layout_variant", "start": extra[0], "end": extra[1], "score": 100.0}
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
    cleaned = []
    for m in mentions:
        model_text = m.get("quote" if condition == "G1" else "value", "") or ""
        clean, had_label = strip_line_labels(model_text)
        cleaned.append((model_text, clean.strip() if had_label else clean, had_label))

    located: list[dict | None] = [None] * len(mentions)
    seen: dict = {}
    if condition in ("G0", "G1"):
        # Longer values first, then the model's own order; each takes a free occurrence.
        taken: list[tuple[int, int]] = []
        for i in sorted(range(len(mentions)), key=lambda k: (-len(cleaned[k][1]), k)):
            m, clean = mentions[i], cleaned[i][1]
            if condition == "G1":
                key = (m.get("field"), m.get("line"), clean)
                r = locate_g1(text, int(m.get("line", 0) or 0), clean, seen.get(key, 0), taken)
            else:
                key = (m.get("field"), clean)
                r = locate_g0(text, clean, seen.get(key, 0), taken)
            seen[key] = seen.get(key, 0) + 1
            if r["start"] is not None:
                taken.append((r["start"], r["end"]))
            located[i] = r

    out = []
    for i, m in enumerate(mentions):
        model_text, clean, had_label = cleaned[i]
        if condition == "RULE":
            # rule baseline: spans come with exact offsets, nothing to locate
            r = {"status": "exact", "start": m["start"], "end": m["end"], "score": 100.0}
            model_text = text[m["start"]:m["end"]]
        else:
            r = located[i]
        value = text[r["start"]:r["end"]] if r["start"] is not None else None
        out.append({"field": m.get("field"), "line": m.get("line"), "model_text": model_text,
                    "had_line_label": had_label, "value": value, **r})
    return out
