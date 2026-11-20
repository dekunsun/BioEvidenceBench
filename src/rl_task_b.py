"""Task B of rl/PLAN_zh.md: OCR line repair. Data building, the two word alignments, Reward v1.0.

Library module (no main). Pieces:

  expert_text(pid), legacy_text(pid)   page texts, cached under data/cache/taskb/ (not committed).
                                       Legacy OCR: BHL open-data S3, decoded as UTF-8.
  line_pairs(pid)                      one unit per expert-transcription line: the line (target) and
                                       the legacy OCR slice aligned to it (input), with quality stats.
  word_status(ref, other)              alignment of a text to a reference line, word by word: is each
                                       reference word present in `other` exactly (NFC), as a whole word?
                                       Used twice: alignment A (legacy slice vs reference: which words
                                       are damaged) and alignment B (model output vs reference).
  make_unit(target, input, flags)      one task item from a reference line and its OCR input.
  reward(unit, output)                 Reward v1.1 (rl/env/task_b_ocr_repair/REWARD_DESIGN.md) plus the
                                       diagnostic fields, and the long-s reading metric.

Text handling: NFC only, never NFKC (long s, ligatures and similar characters must survive);
no case folding; punctuation is not a word and is not scored in v1.
Words: runs of letters or digits, joined by an apostrophe or a hyphen ("parva", "Linnæus",
"orange-chestnut"). A reference word counts as present only if the aligned characters spell it
exactly AND it stands as a whole word there: "ofthe" does not contain the word "the".
"""
from __future__ import annotations

import json
import re
from collections import Counter
import subprocess
import tempfile
import unicodedata
from functools import lru_cache
from pathlib import Path

import duckdb
import requests
from rapidfuzz.distance import Levenshtein

from common import CACHE, GT_PARQUET, MD_PAGE, legacy_ocr_url
from score import char_map, map_span

TB = CACHE / "taskb"
WORD = re.compile(r"[^\W_]+(?:['’\-‐][^\W_]+)*")
NAME_WEIGHT = 3.0
PENALTY_BROKEN = 0.5      # per correct word changed or deleted (Reward v1.1, Gloria 2026-11-20)
PENALTY_INSERT = 0.25     # per inserted word that matches no reference word
GNFINDER = "/tmp/claude-0/-home-user/b6a70ceb-f87e-5d66-a2c3-ae166d1e15d1/scratchpad/gobin/gnfinder"


# Typographic ligatures (Unicode presentation forms U+FB00-FB06) are glyphs, not spelling: the
# transcription sometimes types "ﬁ" where an OCR engine writes "fi". They are folded to letters in
# every text (reference, OCR input and model output). Letters that ARE spelling stay as they are:
# æ, œ, and the long s ſ (whether ſ ≡ s is Gloria's decision; the two English books have none).
# The Piscium querelae transcription types the same kind of ligature as MUFI private-use code
# points (Medieval Unicode Font Initiative). Readings were taken from the words they occur in
# (e.g. e+U+EADA = "eſt", fo+U+EBA7+libus = "foſſilibus"), 2026-11-20, step 4 audit.
_MUFI = {"\ueada": "ſt", "\ueba2": "ſi", "\ueba6": "ſſ", "\ueba7": "ſſi", "\ueec5": "ct"}
_PRESENTATION = str.maketrans({"\ufb00": "ff", "\ufb01": "fi", "\ufb02": "fl", "\ufb03": "ffi",
                               "\ufb04": "ffl", "\ufb05": "ſt", "\ufb06": "st"} | _MUFI)
# A reference line that still holds U+FFFD (a glyph the transcription could not encode: Greek in
# Piscium, sex symbols and fractions in Butler's plate captions) or an unidentified private-use
# character cannot be a target: no output can match it. Such lines are marked invalid.
_UNREADABLE = re.compile("[\ufffd\ue000-\uf8ff]")


def nfc(s: str) -> str:
    return unicodedata.normalize("NFC", s or "").translate(_PRESENTATION)


# ---------------------------------------------------------------- texts
@lru_cache(maxsize=None)
def page_meta() -> dict[int, tuple[int, int]]:
    """PageID -> (ItemID, SequenceOrder) for every bhl-impact-gt page (cached as CSV)."""
    f = TB / "page_meta.csv"
    if not f.exists():
        TB.mkdir(parents=True, exist_ok=True)
        con = duckdb.connect()
        con.sql(f"CREATE TABLE gt AS SELECT DISTINCT PageID FROM '{GT_PARQUET}'")
        con.sql(f"""COPY (SELECT DISTINCT p.PageID, any_value(p.ItemID) ItemID, any_value(p.SequenceOrder) Seq
                    FROM '{MD_PAGE}' p JOIN gt USING (PageID) GROUP BY p.PageID) TO '{f}' (HEADER)""")
    out = {}
    for line in f.read_text().splitlines()[1:]:
        pid, item, seq = line.split(",")
        out[int(pid)] = (int(item), int(seq))
    return out


def expert_text(pid: int) -> str:
    f = TB / "expert" / f"{pid}.txt"
    if not f.exists():                       # first call: cache every page's text in one query
        f.parent.mkdir(parents=True, exist_ok=True)
        for p, t in duckdb.connect().sql(f"SELECT PageID, text FROM '{GT_PARQUET}'").fetchall():
            (f.parent / f"{p}.txt").write_text(t or "", encoding="utf-8")
    return nfc(f.read_text(encoding="utf-8"))


def legacy_text(pid: int) -> str:
    f = TB / "legacy" / f"{pid}.txt"
    if not f.exists():
        f.parent.mkdir(parents=True, exist_ok=True)
        item, seq = page_meta()[pid]
        r = requests.get(legacy_ocr_url(item, pid, seq), timeout=60)
        r.raise_for_status()
        f.write_text(r.content.decode("utf-8", errors="replace"), encoding="utf-8")
    t = f.read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n")
    return nfc(re.sub(r"[ \t]+\n", "\n", t))


@lru_cache(maxsize=None)
def name_spans(pid: int) -> tuple[tuple[int, int], ...]:
    """Scientific-name candidates on the expert page (gnfinder v1.4.0, no verification)."""
    text = expert_text(pid)
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as fh:
        fh.write(text)
    out = subprocess.run([GNFINDER, "-f", "compact", fh.name], capture_output=True, text=True, check=True).stdout
    Path(fh.name).unlink()
    data = json.loads(out.strip().splitlines()[-1])
    spans = []
    for n in data.get("names") or []:
        core = n["verbatim"].rstrip(" .,;:)")
        spans.append((n["start"], n["start"] + len(core)))
    return tuple(spans)


# ---------------------------------------------------------------- alignment
def words(s: str) -> list[tuple[int, int, str]]:
    return [(m.start(), m.end(), m.group()) for m in WORD.finditer(s)]


def _whole(s: str, a: int, b: int) -> bool:
    left = s[a - 1] if a > 0 else " "
    right = s[b] if b < len(s) else " "
    return not (left.isalnum() or right.isalnum())


def lower_keep(s: str) -> str:
    """Lower case, one character for one (offsets survive), and never folding ſ: str.casefold()
    turns ſ into s and would erase the long-s distinction, so it is not used anywhere."""
    return "".join(c.lower() if len(c.lower()) == 1 else c for c in s)


def _akey(s: str) -> str:
    """Alignment key: case is ignored and the long s may align with s (same length, so offsets
    survive). Used only to FIND positions; scoring compares the real characters."""
    return lower_keep(s).replace("ſ", "s")


def _cmap(a: str, b: str) -> tuple:
    return tuple(range(len(a))) if a == b else char_map(_akey(a), _akey(b))


def _case_pattern(w: str) -> str:
    """'UPPER', 'Title' or 'lower' (ignoring non-letters): a word printed in small caps reads as
    UPPER in the transcription and as Title or lower in the OCR."""
    letters = [c for c in w if c.isalpha()]
    if letters and all(c.isupper() for c in letters):
        return "UPPER"
    return "Title" if letters and letters[0].isupper() else "lower"


def word_status(ref: str, other: str) -> tuple[list[dict], float]:
    """For each word of `ref`: is it present at the aligned place in `other`, as a whole word?
    `ok` compares exactly (the main reward); `ok_reading` treats ſ and s as the same letter (the
    reading metric). Returns (rows, coverage), coverage = share of ref characters aligned."""
    cmap = _cmap(ref, other)
    cov = sum(1 for c in cmap if c >= 0) / max(1, len(cmap))
    rows = []
    for a, b, w in words(ref):
        sp = map_span(cmap, a, b)
        got = other[sp[0]:sp[1]] if sp else ""
        whole = bool(sp) and _whole(other, sp[0], sp[1])
        rows.append({"start": a, "end": b, "word": w, "aligned": got,
                     "ok": whole and got == w,
                     "ok_reading": whole and got.replace("ſ", "s") == w.replace("ſ", "s"),
                     # case-insensitive comparisons (Reward v1.2): ſ stays distinct from s
                     "ok_case": whole and lower_keep(got) == lower_keep(w),
                     "ok_case_reading": whole and _akey(got) == _akey(w),
                     "case_differs": bool(got) and _case_pattern(got) != _case_pattern(w)})
    return rows, cov


def inserted_words(text: str, ref: str) -> list[str]:
    """Words of `text` whose characters align to no word character of `ref` (insertions). The
    alignment is one-to-one, so a word written twice leaves the second copy as an insertion."""
    cmap = _cmap(text, ref)
    out = []
    for a, b, w in words(text):
        sp = map_span(cmap, a, b)
        if sp is None or not any(ch.isalnum() for ch in ref[sp[0]:sp[1]]):
            out.append(w)
    return out


# ---------------------------------------------------------------- units
def make_unit(target: str, inp: str, name_word_flags: list[bool] | None = None, **meta) -> dict:
    """A task item: reference line `target`, OCR input `inp`. Damage is decided by alignment A."""
    rows, _ = word_status(target, inp)
    flags = name_word_flags if name_word_flags is not None else [False] * len(rows)
    kind = [word_kind(r) for r in rows]
    kind_r = [word_kind(r, reading=True) for r in rows]
    return meta | {"target": target, "input": inp, "n_words": len(rows),
                   "n_damaged": kind.count("damaged"),
                   "n_damaged_reading": kind_r.count("damaged"),
                   "n_case_only": kind.count("case_only"),
                   "n_name_damaged": sum(k == "damaged" and f for k, f in zip(kind, flags)),
                   "damaged": [r["word"] for r, k in zip(rows, kind) if k == "damaged"],
                   "case_only": [r["word"] for r, k in zip(rows, kind) if k == "case_only"],
                   "name_word_flags": flags}


def word_kind(row: dict, reading: bool = False) -> str:
    """How the OCR has a reference word (Reward v1.2): 'correct' (exactly), 'case_only' (same
    letters, only the case differs: neutral, neither damaged nor penalised for case) or 'damaged'."""
    if row["ok_reading" if reading else "ok"]:
        return "correct"
    if row["ok_case_reading" if reading else "ok_case"]:
        return "case_only"
    return "damaged"


def line_pairs(pid: int, min_chars: int = 15, min_words: int = 2) -> list[dict]:
    """One unit per expert line: target = the line; input = the legacy OCR aligned to it,
    widened to whole words, line breaks inside it turned into spaces. Quality stats decide
    whether the pair is usable (`valid`)."""
    ref, leg = expert_text(pid), legacy_text(pid)
    cmap = _cmap(ref, leg)
    names = name_spans(pid)
    units, pos = [], 0
    for li, line in enumerate(ref.split("\n")):
        a, b = pos, pos + len(line)
        pos = b + 1
        s = line.strip()
        if len(s) < min_chars or len(words(s)) < min_words:
            continue
        a += len(line) - len(line.lstrip())
        b = a + len(s)
        mapped = [cmap[i] for i in range(a, b) if cmap[i] >= 0]
        cov = len(mapped) / max(1, b - a)
        if not mapped:
            units.append({"page_id": pid, "line_no": li + 1, "target": s, "input": "", "coverage": 0.0,
                          "valid": False, "why_invalid": "no aligned legacy text"})
            continue
        la, lb = min(mapped), max(mapped) + 1
        while la > 0 and leg[la - 1].isalnum():
            la -= 1
        while lb < len(leg) and leg[lb].isalnum():
            lb += 1
        raw = leg[la:lb]
        inp = re.sub(r"\s*\n\s*", " ", raw).strip()
        span_ratio = (lb - la) / max(1, b - a)
        sim = 1 - Levenshtein.normalized_distance(lower_keep(s), lower_keep(inp))   # pairing ignores case
        rows = words(s)
        flags = [any(na <= a + ra and a + rb <= nb for na, nb in names) for ra, rb, _ in rows]
        why = []
        if cov < 0.9:
            why.append(f"coverage {cov:.2f}")
        if not 0.6 <= span_ratio <= 1.6:
            why.append(f"span ratio {span_ratio:.2f}")
        if sim < 0.3:
            why.append(f"similarity {sim:.2f}")
        if _UNREADABLE.search(s):
            why.append("unreadable character in reference")
        units.append(make_unit(s, inp, flags, page_id=pid, line_no=li + 1,
                               input_had_linebreak="\n" in raw.strip(), coverage=round(cov, 3),
                               span_ratio=round(span_ratio, 3), similarity=round(sim, 3),
                               valid=not why, why_invalid="; ".join(why)))
    return units


# ---------------------------------------------------------------- reward
_COMMENTARY = re.compile(r"^\s*(corrected|correction|repaired|fixed|here\s+is|here's|output|answer|"
                         r"the\s+corrected|restored|line)\b[^\n]{0,40}?:\s*", re.I)
_WRAPPERS = [("```", "```"), ("`", "`"), ("**", "**"), ("*", "*"), ('"', '"'), ("\u201c", "\u201d"), ("'", "'")]


def format_check(output, target: str) -> str:
    """'' if the output is a bare line of text; otherwise the reason it is not. The task asks for
    the repaired line only, so commentary, Markdown or quotation wrappers, several lines and empty
    answers are format errors (reward 0), not ordinary insertions."""
    if not isinstance(output, str) or not output.strip():
        return "empty"
    out = output.strip()
    if "\n" in out:
        return "several lines"
    m = _COMMENTARY.match(out)
    if m and not _COMMENTARY.match(target):
        return "commentary prefix"
    for a, b in _WRAPPERS:
        if len(out) > len(a) + len(b) and out.startswith(a) and out.endswith(b) \
                and not (target.startswith(a) and target.endswith(b)):
            return "wrapped in " + a
    return ""


def _score(unit, legacy_rows, out_rows, out, key, name_weight):
    """Repair rate, broken and inserted words under one comparison (`ok` or `ok_reading`).

    Reward v1.2, case: a reference word the OCR has with the right letters but another case is
    neutral: no repair credit, and any case in the output is accepted, but changing its letters,
    deleting it or replacing it is a broken word. A damaged word whose OCR case pattern differs
    (small caps read as Title) is repaired by the right letters in any case. Every other word is
    compared exactly, so changing the case of a word the OCR had right is a broken word."""
    nocase = "ok_case_reading" if key == "ok_reading" else "ok_case"
    w_tot = w_ok = 0.0
    repaired = name_rep = name_dmg = broken = preserved = 0
    case_n = case_right = 0
    out_tokens = Counter(w for _, _, w in words(out))
    ref_tokens = Counter(w for _, _, w in words(unit["target"]))
    for leg_r, out_r, is_name in zip(legacy_rows, out_rows, unit["name_word_flags"]):
        kind = word_kind(leg_r, reading=key == "ok_reading")
        if kind == "case_only" or (kind == "damaged" and leg_r["case_differs"]):
            case_n += 1
            case_right += bool(out_r[key])
        if kind == "case_only":                              # neutral: letters must survive
            if out_r[nocase]:
                preserved += 1
            else:
                broken += 1
            continue
        if kind == "damaged":                                # damaged in the OCR
            w = name_weight if is_name else 1.0
            w_tot += w
            name_dmg += is_name
            # A repair only counts if the damaged OCR token is gone: writing the right word next
            # to the wrong one keeps the damage in the text.
            kept_damage = (len(leg_r["aligned"]) > 1 and leg_r["aligned"] not in ref_tokens
                           and out_tokens.get(leg_r["aligned"], 0) > 0)
            hit = out_r[nocase] if leg_r["case_differs"] else out_r[key]
            if hit and not kept_damage:
                w_ok += w
                repaired += 1
                name_rep += is_name
        elif out_r[key]:
            preserved += 1
        else:
            broken += 1
    return w_tot, w_ok, repaired, name_rep, name_dmg, broken, preserved, case_n, case_right


def reward(unit: dict, output, name_weight: float = NAME_WEIGHT, p_broken: float = PENALTY_BROKEN,
           p_insert: float = PENALTY_INSERT) -> dict:
    """Reward v1.2 with diagnostic fields (REWARD_DESIGN.md). Damaged line:
    clip(weighted repair rate - p_broken*B - p_insert*I, -1, 1); clean line: clip(1 - p_broken*B -
    p_insert*I, -1, 1). B = correct OCR words changed or deleted; I = inserted words (not counting
    insertions already in the OCR). Format, integrity or alignment failure: 0, flagged.
    `reward_reading` is the same with the long s and s treated as one letter."""
    target = unit["target"]
    reason = format_check(output, target)
    diag = {"reward": 0.0, "reward_reading": 0.0, "format_valid": not reason, "format_reason": reason,
            "integrity_valid": False, "alignment_valid": False, "clean_line": unit["n_damaged"] == 0,
            "damaged_words": unit["n_damaged"], "repaired_words": 0, "scientific_name_damaged": 0,
            "scientific_name_repairs": 0, "correct_words": unit["n_words"] - unit["n_damaged"] - unit.get("n_case_only", 0),
            "preserved_correct_words": 0, "damaged_correct_words": 0, "extra_words": 0,
            "penalty": 0.0, "weighted_repair_rate": None, "cer_diagnostic": None,
            "case_only_words": unit.get("n_case_only", 0), "case_words": 0, "case_accuracy": None,
            "exact_repair_rate": None}
    if reason:
        return diag
    out = nfc(output).strip()
    diag["integrity_valid"] = 0.5 <= len(out) / max(1, len(target)) <= 1.5
    diag["cer_diagnostic"] = round(Levenshtein.normalized_distance(out, target), 4)
    if not diag["integrity_valid"]:
        return diag
    legacy_rows, _ = word_status(target, unit["input"])
    out_rows, cov = word_status(target, out)
    diag["alignment_valid"] = cov >= 0.5
    if not diag["alignment_valid"]:
        return diag
    added = Counter(inserted_words(out, target)) - Counter(inserted_words(unit["input"], target))
    n_ins = sum(added.values())
    diag["extra_words"] = n_ins
    for key, field in (("ok", "reward"), ("ok_reading", "reward_reading")):
        (w_tot, w_ok, rep, name_rep, name_dmg, broken, preserved,
         case_n, case_right) = _score(unit, legacy_rows, out_rows, out, key, name_weight)
        pen = p_broken * broken + p_insert * n_ins
        base = (w_ok / w_tot) if w_tot else 1.0
        diag[field] = round(max(-1.0, min(1.0, base - pen)), 4)
        if key == "ok":
            diag.update({"repaired_words": rep, "scientific_name_repairs": name_rep,
                         "scientific_name_damaged": name_dmg, "damaged_correct_words": broken,
                         "preserved_correct_words": preserved, "penalty": round(pen, 4),
                         "weighted_repair_rate": round(base, 4) if w_tot else None,
                         # diagnostics, not in the reward: exact case on the case-free words, and the
                         # unweighted repair rate over damaged words (neutral words not counted)
                         "case_words": case_n,
                         "case_accuracy": round(case_right / case_n, 4) if case_n else None,
                         "exact_repair_rate": round(rep / unit["n_damaged"], 4) if unit["n_damaged"] else None})
    return diag
