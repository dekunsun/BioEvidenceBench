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
  reward(unit, output)                 Reward v1.0 plus the diagnostic fields.

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
LAMBDA = 1.0
GNFINDER = "/tmp/claude-0/-home-user/b6a70ceb-f87e-5d66-a2c3-ae166d1e15d1/scratchpad/gobin/gnfinder"


# Typographic ligatures (Unicode presentation forms U+FB00-FB06) are glyphs, not spelling: the
# transcription sometimes types "ﬁ" where an OCR engine writes "fi". They are folded to letters in
# every text (reference, OCR input and model output). Letters that ARE spelling stay as they are:
# æ, œ, and the long s ſ (whether ſ ≡ s is Gloria's decision; the two English books have none).
_PRESENTATION = str.maketrans({"\ufb00": "ff", "\ufb01": "fi", "\ufb02": "fl", "\ufb03": "ffi",
                               "\ufb04": "ffl", "\ufb05": "ſt", "\ufb06": "st"})


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


def word_status(ref: str, other: str) -> tuple[list[dict], float]:
    """For each word of `ref`: is it present exactly, as a whole word, at the aligned place in
    `other`? Returns (rows, coverage) where coverage = share of ref characters with an aligned
    position in `other`."""
    cmap = char_map(ref, other) if ref != other else tuple(range(len(ref)))
    cov = sum(1 for c in cmap if c >= 0) / max(1, len(cmap))
    rows = []
    for a, b, w in words(ref):
        sp = map_span(cmap, a, b)
        got = other[sp[0]:sp[1]] if sp else ""
        ok = bool(sp) and got == w and _whole(other, sp[0], sp[1])
        rows.append({"start": a, "end": b, "word": w, "aligned": got, "ok": ok})
    return rows, cov


def inserted_words(text: str, ref: str) -> list[str]:
    """Words of `text` whose characters align to no word character of `ref` (insertions)."""
    cmap = char_map(text, ref) if text != ref else tuple(range(len(text)))
    out = []
    for a, b, w in words(text):
        sp = map_span(cmap, a, b)
        if sp is None or not any(ch.isalnum() for ch in ref[sp[0]:sp[1]]):
            out.append(w)
    return out


# ---------------------------------------------------------------- units
def line_pairs(pid: int, min_chars: int = 15, min_words: int = 2) -> list[dict]:
    """One unit per expert line: target = the line; input = the legacy OCR aligned to it,
    widened to whole words, line breaks inside it turned into spaces. Quality stats decide
    later whether the pair is usable (`valid`)."""
    ref, leg = expert_text(pid), legacy_text(pid)
    cmap = char_map(ref, leg)
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
        sim = 1 - Levenshtein.normalized_distance(s, inp)
        rows, _ = word_status(s, inp)
        name_words = [any(na <= a + r["start"] and a + r["end"] <= nb for na, nb in names) for r in rows]
        why = []
        if cov < 0.9:
            why.append(f"coverage {cov:.2f}")
        if not 0.6 <= span_ratio <= 1.6:
            why.append(f"span ratio {span_ratio:.2f}")
        if sim < 0.3:
            why.append(f"similarity {sim:.2f}")
        units.append({"page_id": pid, "line_no": li + 1, "target": s, "input": inp,
                      "input_had_linebreak": "\n" in raw.strip(), "coverage": round(cov, 3),
                      "span_ratio": round(span_ratio, 3), "similarity": round(sim, 3),
                      "n_words": len(rows), "n_damaged": sum(not r["ok"] for r in rows),
                      "n_name_damaged": sum((not r["ok"]) and f for r, f in zip(rows, name_words)),
                      "damaged": [r["word"] for r in rows if not r["ok"]],
                      "name_word_flags": name_words,
                      "valid": not why, "why_invalid": "; ".join(why)})
    return units


# ---------------------------------------------------------------- reward
def reward(unit: dict, output, lam: float = LAMBDA, name_weight: float = NAME_WEIGHT) -> dict:
    """Reward v1.0 (rl/PLAN_zh.md 6.3) with diagnostic fields. `unit` comes from line_pairs."""
    diag = {"reward": 0.0, "format_valid": isinstance(output, str) and bool(output.strip()),
            "integrity_valid": False, "alignment_valid": False, "clean_line": unit["n_damaged"] == 0,
            "damaged_words": unit["n_damaged"], "repaired_words": 0, "scientific_name_damaged": 0,
            "scientific_name_repairs": 0, "correct_words": unit["n_words"] - unit["n_damaged"],
            "preserved_correct_words": 0, "damaged_correct_words": 0, "extra_words": 0, "penalty": 0.0,
            "weighted_repair_rate": None, "cer_diagnostic": None}
    if not diag["format_valid"]:
        return diag
    out = nfc(output).strip()
    target = unit["target"]
    ratio = len(out) / max(1, len(target))
    diag["integrity_valid"] = "\n" not in out and 0.5 <= ratio <= 1.5
    diag["cer_diagnostic"] = round(Levenshtein.normalized_distance(out, target), 4)
    if not diag["integrity_valid"]:
        return diag
    legacy_rows, _ = word_status(target, unit["input"])
    out_rows, cov = word_status(target, out)
    diag["alignment_valid"] = cov >= 0.5
    if not diag["alignment_valid"]:
        return diag
    flags = unit["name_word_flags"]
    w_tot = w_ok = 0.0
    broken = 0
    for leg_r, out_r, is_name in zip(legacy_rows, out_rows, flags):
        if not leg_r["ok"]:                              # damaged in the OCR
            w = name_weight if is_name else 1.0
            w_tot += w
            diag["scientific_name_damaged"] += is_name
            if out_r["ok"]:
                w_ok += w
                diag["repaired_words"] += 1
                diag["scientific_name_repairs"] += is_name
        else:                                            # correct in the OCR
            if out_r["ok"]:
                diag["preserved_correct_words"] += 1
            else:
                broken += 1
    diag["damaged_correct_words"] = broken
    # Words the model INSERTED: output words that align to no reference word at all (an added
    # "Corrected:", an invented word). A wrong attempt at a word is a substitution, not an
    # insertion: it already costs the repair credit and is not penalised twice. Insertions that
    # were already in the OCR input are not counted, so returning the OCR unchanged scores
    # exactly 0 on a damaged line.
    added = Counter(inserted_words(out, target)) - Counter(inserted_words(unit["input"], target))
    diag["extra_words"] = sum(added.values())
    broken += diag["extra_words"]
    if diag["clean_line"]:
        diag["penalty"] = round(min(1.0, broken / max(1, diag["correct_words"])), 4)
        diag["reward"] = round(1.0 - diag["penalty"], 4)
    else:
        diag["weighted_repair_rate"] = round(w_ok / w_tot, 4)
        diag["penalty"] = round(lam * min(1.0, broken / max(1, diag["damaged_words"])), 4)
        diag["reward"] = round(diag["weighted_repair_rate"] - diag["penalty"], 4)
    return diag
