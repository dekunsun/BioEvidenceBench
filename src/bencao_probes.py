"""本草綱目 pilot: does the OCR model read the image or recall the text? Two dev-only probes.

    python src/bencao_probes.py a                         # edition probe, no API call
    python src/bencao_probes.py b --model claude-opus-5-5 --max-usd 0.5   # occlusion probe (paid)

Designed with the author on 2026-11-23. Both are reported as evidence about image dependence, not as
proof for or against memorisation.

A. Edition probe. The manuscript (Siku quanshu, 文淵閣) differs in places from the text that circulates
   online. Wikisource's 本草綱目/草之一 stands for the circulating text (the most likely source of anything
   memorised). On each pilot half-leaf the Kanripo transcription (what the manuscript shows, pending the
   author's scan check), the Wikisource text and the model's OCR output are aligned character by
   character. At every place where Siku and Wikisource differ, the OCR output either follows the
   manuscript, follows the circulating text, or neither. Sites are split into likely glyph variants
   (the same character written another way), interchangeable usages (different characters for the
   same word, e.g. 暴/曝) and different words; only the last is a clean test, because a model may
   normalise glyphs or usages without recalling anything. The split is proposed from fixed lists
   below; the author confirms it in `kind_confirmed`.
   Output: results/bencao_pilot/probe_a_sites.csv (one row per site, `site_confirmed` for the author)
   and probe_a_summary.csv.

B. Occlusion probe. Two columns of each half-leaf are painted white (the 2nd and 5th column from the
   right, a rule fixed before any run), everything else is unchanged, and the model transcribes the
   page again with the same prompt as src/bencao_ocr_claude.py. If it reads the image, the hidden
   columns' text should be missing or marked □; if it reproduces them, that text came from memory or
   from context. Output: run folder results/<stamp>_bencao_probe_b_<model>/ and probe_b_summary.csv.
   Main measure: of each column's own 3-character sequences (those that occur in no other column of the
   page), the share found in the output, hidden against visible columns. Character overlap alone
   (`share`) is inflated by formulaic wording repeated across columns (甘草二兩水三升煑…).
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import io
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from PIL import Image, ImageDraw
from rapidfuzz.distance import Levenshtein as L

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import bencao_ocr_claude as OCR  # noqa: E402  (same prompt, schema, prices)

DATA = ROOT / "data" / "bencao"
OUT = ROOT / "results" / "bencao_pilot"
WS_CACHE = ROOT / "data" / "cache" / "bencao" / "ws_草之一.txt"
WS_URL = "https://zh.wikisource.org/wiki/%E6%9C%AC%E8%8D%89%E7%B6%B1%E7%9B%AE/%E8%8D%89%E4%B9%8B%E4%B8%80?action=raw"
PAGES = ["036-1b", "036-5a", "036-7b", "036-12b", "036-13a", "036-30a"]
HIDE = (2, 5)                       # columns painted white in probe B, counted from the right, 1-based

# glyph-variant and missing-stroke taboo pairs: one fixed table shared with the OCR scoring (guide v0.2 rule 10)
from bencao_variants import pairs as _variant_pairs  # noqa: E402
VARIANTS = _variant_pairs()
# different characters used interchangeably for the same word in this text (proposed; the author confirms)
USAGE = {frozenset(p) for p in ["暴曝", "註注", "鍾鐘", "欬咳", "詞辭", "枹抱"]}
PUNCT = r"[\s，。、；：︰！？「」『』（）()《》〈〉·．,.;:!?\"'—…=*#|〓□]"


def clean(s: str) -> str:
    return re.sub(PUNCT, "", s)


def ref_map(ref: str, hyp: str) -> list[str | None]:
    """For each character of ref, the character hyp has at that place (None if hyp has nothing)."""
    out: list[str | None] = [None] * len(ref)
    for op, i1, i2, j1, j2 in L.opcodes(ref, hyp):
        if op in ("equal", "replace") and (i2 - i1) == (j2 - j1):
            for k in range(i2 - i1):
                out[i1 + k] = hyp[j1 + k]
        elif op == "replace":                       # unequal block: pair what lines up, rest None
            for k in range(min(i2 - i1, j2 - j1)):
                out[i1 + k] = hyp[j1 + k]
    return out


def ws_segment(ref: str, wsc: str) -> str:
    """The stretch of the Wikisource text that lines up with this half-leaf."""
    for k in range(0, max(1, len(ref) - 8), 4):
        i = wsc.find(ref[k:k + 8])
        if i >= 0:
            break
    else:
        return ""
    lo, hi = max(0, i - k - 30), i - k + len(ref) + 30
    win = wsc[lo:hi]
    best = min(((L.distance(ref, win[a:b]), a, b) for a in range(0, 61, 1) for b in range(len(win) - 60, len(win) + 1, 1)
                if b > a), key=lambda x: x[0])
    return win[best[1]:best[2]]


# the author's line-by-line scan check (received file + her later decisions, data/bencao/scan_verify_changes.csv)
SCAN_VERIFY = DATA / "scan_verify_working.csv"
KINDS = DATA / "received" / "2026-11-23_probe_a_kinds_gloria.xlsx"         # her kind decisions for the 15 non-glyph sites


def site_line(pb: str, pos: int) -> int:
    """Manuscript line (1-based) that holds cleaned position `pos` of the half-leaf."""
    n = 0
    for k, line in enumerate((DATA / "kanripo_plain" / f"{pb}.txt").read_text(encoding="utf-8").splitlines(), 1):
        n += len(clean(line))
        if pos < n:
            return k
    return k


def scan_line_verdict(pb: str, line: int, pos: int, siku: str) -> str:
    """site_confirmed from the author's scan check. A site on a line she marked Y matches the scan as
    transcribed. On a line she marked N, the site counts as confirmed when her scan_reading has the same
    character at the aligned position. Anything else is left empty for her to decide."""
    if not SCAN_VERIFY.exists():
        return ""
    v = pd.read_csv(SCAN_VERIFY)
    hit = v[(v.half_leaf == pb) & (v.line == line)]
    if not len(hit):
        return ""
    verdict, reading = str(hit.matches_scan.iloc[0]).strip().upper(), hit.scan_reading.iloc[0]
    if verdict == "Y":
        return "Y (line verified)"
    if verdict == "N" and isinstance(reading, str):
        lines = (DATA / "kanripo_plain" / f"{pb}.txt").read_text(encoding="utf-8").splitlines()
        start = sum(len(clean(x)) for x in lines[:line - 1])
        got = ref_map(clean(lines[line - 1]), clean(reading))[pos - start]
        return "Y (her scan_reading)" if got == siku else ""
    return ""


def probe_a(models=("claude_opus", "claude_haiku")) -> None:
    if not WS_CACHE.exists():
        import urllib.request
        WS_CACHE.write_bytes(urllib.request.urlopen(urllib.request.Request(WS_URL, headers=OCR_UA), timeout=60).read())
    ws = WS_CACHE.read_text(encoding="utf-8")
    ws = re.sub(r"\{\{[^}]*\}\}|\[\[[^\]]*\]\]|<[^>]+>", "", ws)
    wsc = clean(ws)
    sites = []
    for pb in PAGES:
        ref = clean((DATA / "kanripo_plain" / f"{pb}.txt").read_text(encoding="utf-8"))
        seg = ws_segment(ref, wsc)
        (DATA / "common_ws").mkdir(parents=True, exist_ok=True)
        (DATA / "common_ws" / f"{pb}.txt").write_text(seg, encoding="utf-8")
        wmap = ref_map(ref, seg)
        hyps = {m: ref_map(ref, clean((DATA / m / f"{pb}.txt").read_text(encoding="utf-8"))) for m in models}
        for i, c in enumerate(ref):
            w = wmap[i]
            if w is None or w == c:
                continue
            row = {"half_leaf": pb, "pos": i, "context": ref[max(0, i - 4):i + 5], "siku": c, "wikisource": w,
                   "kind": ("glyph_variant" if frozenset((c, w)) in VARIANTS else "interchangeable_usage"
                           if frozenset((c, w)) in USAGE else "different_word"),
                   "kind_confirmed": "", "site_confirmed": ""}
            for m, hm in hyps.items():
                h = hm[i]
                row[m] = h or ""
                same = lambda x, y: x == y or frozenset((x, y)) in VARIANTS     # same character, any glyph
                row[f"{m}_follows"] = ("missing" if h is None else "siku" if h == c else "wikisource" if h == w
                                       else "siku (other glyph)" if row["kind"] != "glyph_variant" and same(h, c)
                                       else "neither")
            sites.append(row)
    d = pd.DataFrame(sites)
    d.insert(2, "line", [site_line(r.half_leaf, r.pos) for r in d.itertuples()])
    d["site_confirmed"] = [scan_line_verdict(r.half_leaf, r.line, r.pos, r.siku) for r in d.itertuples()]
    # the author's kinds: `kind` stays the proposal, `kind_final` is her decision ("Y" = proposal accepted);
    # a site she queried ("?") is not counted as scan-confirmed until she settles it.
    if KINDS.exists():
        k = pd.read_excel(KINDS)[["half_leaf", "pos", "kind_confirmed", "note"]].rename(columns={"note": "her_note"})
        d = d.drop(columns=["kind_confirmed"]).merge(k, on=["half_leaf", "pos"], how="left")
        d["kind_confirmed"] = d.kind_confirmed.fillna("")
        d["kind_final"] = [kd if kc in ("", "Y") else ("pending" if kc == "?" else kc)
                           for kd, kc in zip(d.kind, d.kind_confirmed)]
        d.loc[d.kind_confirmed == "?", "site_confirmed"] = ""
    else:
        d["kind_final"] = d.kind
    changes = DATA / "probe_a_changes.csv"                  # her later decisions on single sites, logged
    if changes.exists():
        for c in pd.read_csv(changes).itertuples():
            m = (d.half_leaf == c.half_leaf) & (d.pos == c.pos)
            d.loc[m, c.column] = c.value
            if c.column == "kind_confirmed":
                d.loc[m, "kind_final"] = c.value
    # one variation event = a run of adjacent non-glyph sites (即是/地近 is one event, not two; her note)
    ev, last = [], None
    for r in d.itertuples():
        same = (last is not None and r.kind_final != "glyph_variant" and r.kind_final == last[2]
                and r.half_leaf == last[0] and r.pos == last[1] + 1)
        ev.append(ev[-1] if same else (ev[-1] + 1 if ev else 0))
        last = (r.half_leaf, r.pos, r.kind_final)
    d["event"] = ev
    OUT.mkdir(parents=True, exist_ok=True)
    d.to_csv(OUT / "probe_a_sites.csv", index=False)
    summ = []
    for m in models:
        for kind, g in d.groupby("kind_final"):
            vc = g[f"{m}_follows"].value_counts()
            summ.append({"model": m, "kind": kind, "sites": len(g), "events": g.event.nunique(),
                         **{k: int(vc.get(k, 0)) for k in
                            ("siku", "siku (other glyph)", "wikisource", "neither", "missing")}})
    s = pd.DataFrame(summ)
    s.to_csv(OUT / "probe_a_summary.csv", index=False)
    print(s.to_string(index=False))


OCR_UA = {"User-Agent": "Mozilla/5.0 (compatible; research-pilot/0.1)"}


def column_bounds(img: Image.Image) -> list[tuple[int, int]]:
    """The 8 text columns of a half-leaf, right to left, between its 9 ruled vertical lines (界欄).
    Candidate lines are x positions that are dark over much of the page height; the 9 rules are the
    chain of candidates about one column width apart that matches best, starting from each candidate.
    Where a rule is faint, the expected position is used."""
    g = np.asarray(img.convert("L"), dtype=float)
    h, _ = g.shape
    dark = (g[int(h * 0.15):int(h * 0.85)] < 120).mean(axis=0)
    xs = np.where(dark > 0.35)[0]
    groups: list[list[int]] = []
    for x in xs:
        if groups and x - groups[-1][-1] <= 6:
            groups[-1].append(int(x))
        else:
            groups.append([int(x)])
    cand = sorted((int(np.mean(gr)) for gr in groups), reverse=True)
    diffs = [a - b for a, b in zip(cand, cand[1:]) if 170 < a - b < 230]
    step = float(np.median(diffs)) if diffs else 200.0
    best = None
    for start in cand:
        chain, hits = [start], 0
        for _ in range(8):
            want = chain[-1] - step
            near = [c for c in cand if abs(c - want) <= 25]
            if near:
                chain.append(min(near, key=lambda c: abs(c - want)))
                hits += 1
            else:
                chain.append(int(want))
        if best is None or hits > best[0]:
            best = (hits, chain)
    rules = best[1]
    return [(rules[k + 1], rules[k]) for k in range(8)]


def probe_b(model: str, max_usd: float) -> None:
    import anthropic
    client = anthropic.Anthropic(api_key=os.environ["EVAL_ANTHROPIC_API_KEY"], max_retries=4)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M")
    run = ROOT / "results" / f"{stamp}_bencao_probe_b_{model}"
    (run / "masked").mkdir(parents=True)
    spent, recs, rows = 0.0, [], []
    for pb in PAGES:
        if spent > max_usd:
            break
        img = Image.open(OCR.FULL / f"{pb}.jpg").convert("RGB")
        cols = column_bounds(img)
        draw = ImageDraw.Draw(img)
        top, bottom = int(img.height * 0.03), int(img.height * 0.97)
        for c in HIDE:
            x0, x1 = cols[c - 1]
            draw.rectangle([x0 + 3, top, x1 - 3, bottom], fill="white")
        img.save(run / "masked" / f"{pb}.jpg", quality=90)
        block, sha = OCR.image_block(run / "masked" / f"{pb}.jpg")
        m = client.messages.create(model=model, max_tokens=8000, system=OCR.SYSTEM,
                                   messages=[{"role": "user", "content": [block, {"type": "text", "text": OCR.TASK}]}],
                                   output_config={"effort": "medium", "format": {"type": "json_schema", "schema": OCR.SCHEMA}})
        raw = "".join(b.text for b in m.content if b.type == "text")
        usd = (m.usage.input_tokens * OCR.PRICES[model][0] + m.usage.output_tokens * OCR.PRICES[model][1]) / 1e6
        spent += usd
        out = "".join(json.loads(raw)["columns"])
        recs.append({"half_leaf": pb, "raw": raw, "usd": round(usd, 5), "image_sha256": sha, "columns_px": cols,
                     "usage": {"input_tokens": m.usage.input_tokens, "output_tokens": m.usage.output_tokens}})
        lines = (DATA / "kanripo_plain" / f"{pb}.txt").read_text(encoding="utf-8").split("\n")
        hyp = clean(out)
        out_grams = grams(hyp)
        for k, line in enumerate(lines, 1):
            ref = clean(line)
            if not ref:
                continue
            # share of this column's characters found in the output, in order (longest common subsequence)
            lcs = _lcs(ref, hyp)
            # 3-character sequences of this column that occur in no other column of the page: if they
            # appear in the output, they came from this column (or from outside the image)
            others = set().union(*(grams(clean(x)) for j, x in enumerate(lines, 1) if j != k))
            own = grams(ref) - others
            rows.append({"model": model, "half_leaf": pb, "column": k, "hidden": k in HIDE, "chars": len(ref),
                         "reproduced": lcs, "share": round(lcs / len(ref), 3), "own_trigrams": len(own),
                         "own_trigrams_in_output": len(own & out_grams)})
        print(pb, f"${usd:.4f}")
    (run / "outputs.jsonl").write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in recs) + "\n", encoding="utf-8")
    (run / "config.json").write_text(json.dumps({
        "run_id": run.name, "model": model, "probe": "B occlusion", "hidden_columns_from_right": HIDE,
        "system": OCR.SYSTEM, "task": OCR.TASK, "schema": OCR.SCHEMA, "effort": "medium", "max_tokens": 8000,
        "usd_total": round(spent, 4), "exploratory": True, "dev_only": True,
        "approved": "author, 2026-11-23 (probe design in chat; '继续')"}, ensure_ascii=False, indent=1), encoding="utf-8")
    d = pd.DataFrame(rows)
    prev = OUT / "probe_b_summary.csv"
    allrows = pd.concat([pd.read_csv(prev)[lambda x: x.model != model], d]) if prev.exists() else d
    allrows.to_csv(prev, index=False)
    s = d.groupby("hidden").agg(chars=("chars", "sum"), reproduced=("reproduced", "sum"),
                                own_trigrams=("own_trigrams", "sum"), found=("own_trigrams_in_output", "sum"))
    s["share"] = (s.reproduced / s.chars).round(3)
    s["own_trigram_share"] = (s.found / s.own_trigrams).round(3)
    print(s.to_string())
    print(f"{run.name}: ${spent:.4f}")


def grams(s: str, n: int = 3) -> set[str]:
    return {s[i:i + n] for i in range(len(s) - n + 1)}


def rescore_b() -> None:
    """Recompute probe_b_summary.csv from the saved outputs of every probe-B run (no API call)."""
    rows = []
    for run in sorted((ROOT / "results").glob("*_bencao_probe_b_*")):
        model = json.loads((run / "config.json").read_text(encoding="utf-8"))["model"]
        for line in (run / "outputs.jsonl").read_text(encoding="utf-8").splitlines():
            r = json.loads(line)
            hyp = clean("".join(json.loads(r["raw"])["columns"]))
            out_grams = grams(hyp)
            lines = (DATA / "kanripo_plain" / f"{r['half_leaf']}.txt").read_text(encoding="utf-8").split("\n")
            for k, text in enumerate(lines, 1):
                ref = clean(text)
                if not ref:
                    continue
                others = set().union(*(grams(clean(x)) for j, x in enumerate(lines, 1) if j != k))
                own = grams(ref) - others
                lcs = _lcs(ref, hyp)
                rows.append({"model": model, "half_leaf": r["half_leaf"], "column": k, "hidden": k in HIDE,
                             "chars": len(ref), "reproduced": lcs, "share": round(lcs / len(ref), 3),
                             "own_trigrams": len(own), "own_trigrams_in_output": len(own & out_grams)})
    d = pd.DataFrame(rows)
    d.to_csv(OUT / "probe_b_summary.csv", index=False)
    s = d.groupby(["model", "hidden"]).agg(chars=("chars", "sum"), own=("own_trigrams", "sum"),
                                            found=("own_trigrams_in_output", "sum"))
    s["own_trigram_share"] = (s.found / s.own).round(3)
    print(s.to_string())


def _lcs(a: str, b: str) -> int:
    """Length of the longest common subsequence of a in b (characters of a found in order in b),
    restricted to the stretch of b that best matches a, so text from elsewhere on the page does not count."""
    from rapidfuzz.distance import LCSseq
    from rapidfuzz import fuzz
    al = fuzz.partial_ratio_alignment(a, b)
    lo, hi = max(0, al.dest_start - 5), min(len(b), al.dest_end + 5)
    return LCSseq.similarity(a, b[lo:hi])


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("probe", choices=["a", "b", "rescore_b"])
    ap.add_argument("--model", default="claude-opus-5-5")
    ap.add_argument("--max-usd", type=float, default=0.5)
    a = ap.parse_args()
    {"a": probe_a, "rescore_b": rescore_b}.get(a.probe, lambda: probe_b(a.model, a.max_usd))()
