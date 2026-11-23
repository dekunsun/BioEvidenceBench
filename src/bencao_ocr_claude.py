"""本草綱目 pilot, modern-OCR option A: a Claude model transcribes each pilot half-leaf from the scan.

    python src/bencao_ocr_claude.py --model claude-opus-5-5 --max-usd 1
    python src/bencao_ocr_claude.py --model claude-haiku-5-5 --max-usd 1

Approved by the author on 2026-11-23 ("跑", option A of the pilot report: Opus and Haiku, six pages,
estimate about $0.35). Exploratory. The model reads the image only; it gets no transcription and no
OCR text. Note for every use of this output: if a Claude model later extracts from it, OCR and
extraction come from the same model family.

Run folder results/<stamp>_bencao_ocr_<model>/: config.json (model, prompt, decoding, image SHA-256),
outputs.jsonl (raw answers, usage, cost), summary.csv (CER against the Kanripo transcription, markup
removed). Texts go to data/bencao/claude_<short model>/<pb>.txt, one manuscript column per line.
"""
from __future__ import annotations

import argparse
import os
import base64
import hashlib
import io
import json
import re
from datetime import datetime, timezone
from pathlib import Path

import anthropic
import pandas as pd
import rapidfuzz.distance.Levenshtein as Lev
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "bencao"
FULL = ROOT / "data" / "cache" / "bencao" / "full"        # full-size Internet Archive images (bencao_pilot.py tesseract)
PRICES = {"claude-opus-5-5": (4.0, 20.0), "claude-sonnet-5-5": (2.0, 10.0), "claude-haiku-5-5": (0.10, 0.50)}

SYSTEM = ("You transcribe pages of a hand-copied Chinese manuscript (the Siku quanshu copy of 本草綱目, 18th "
          "century) exactly as written.")
TASK = ("Transcribe this half-leaf. It is written in vertical columns read from right to left. Return one entry "
        "per column, in reading order (rightmost column first). Rules: copy the characters as written, keeping "
        "traditional and variant forms (do not modernise or simplify); add no punctuation; where a column has "
        "small characters in two sub-columns, write the right sub-column first, then the left one, in the same "
        "entry; write □ for a character you cannot read; leave out the page-edge margin text (book title and "
        "leaf number in the fold).")
SCHEMA = {"type": "object", "properties": {"columns": {"type": "array", "items": {"type": "string"}}},
          "required": ["columns"], "additionalProperties": False}


def image_block(path: Path) -> tuple[dict, str]:
    im = Image.open(path).convert("RGB")
    im.thumbnail((2000, 2000))
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=90)
    b = buf.getvalue()
    return ({"type": "image", "source": {"type": "base64", "media_type": "image/jpeg",
                                         "data": base64.b64encode(b).decode()}}, hashlib.sha256(b).hexdigest())


def cer(hyp: str, ref: str) -> float:
    strip = lambda s: re.sub(r"\s", "", s)
    return Lev.distance(strip(hyp), strip(ref)) / max(1, len(strip(ref)))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True, choices=list(PRICES))
    ap.add_argument("--max-usd", type=float, default=1.0)
    a = ap.parse_args()
    short = a.model.removeprefix("claude-").rsplit("-", 2)[0]          # opus / haiku / sonnet
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M")
    run = ROOT / "results" / f"{stamp}_bencao_ocr_{a.model}"
    run.mkdir(parents=True)
    out_txt = DATA / f"claude_{short}"
    out_txt.mkdir(parents=True, exist_ok=True)
    pages = pd.read_csv(DATA / "pilot_pages.csv")
    client = anthropic.Anthropic(api_key=os.environ["EVAL_ANTHROPIC_API_KEY"], max_retries=4)   # project key, as in run_extraction.py
    spent, recs, rows, hashes = 0.0, [], [], {}
    for r in pages.itertuples():
        if spent > a.max_usd:
            recs.append({"half_leaf": r.half_leaf, "error": "cap reached, not sent"})
            continue
        img, sha = image_block(FULL / f"{r.half_leaf}.jpg")
        hashes[r.half_leaf] = sha
        rec = {"half_leaf": r.half_leaf, "model": a.model, "sent_at": datetime.now(timezone.utc).isoformat(timespec="seconds")}
        m = client.messages.create(model=a.model, max_tokens=8000, system=SYSTEM,
                                   messages=[{"role": "user", "content": [img, {"type": "text", "text": TASK}]}],
                                   output_config={"effort": "medium", "format": {"type": "json_schema", "schema": SCHEMA}})
        raw = "".join(b.text for b in m.content if b.type == "text")
        usd = (m.usage.input_tokens * PRICES[a.model][0] + m.usage.output_tokens * PRICES[a.model][1]) / 1e6
        spent += usd
        cols = json.loads(raw)["columns"]
        text = "\n".join(c.strip() for c in cols)
        (out_txt / f"{r.half_leaf}.txt").write_text(text, encoding="utf-8")
        ref = (DATA / "kanripo_plain" / f"{r.half_leaf}.txt").read_text(encoding="utf-8")
        rec |= {"raw": raw, "stop_reason": m.stop_reason, "usd": round(usd, 5),
                "usage": {"input_tokens": m.usage.input_tokens, "output_tokens": m.usage.output_tokens}}
        recs.append(rec)
        rows.append({"half_leaf": r.half_leaf, "columns": len(cols), "chars": len(re.sub(r"\s", "", text)),
                     "unreadable_marks": text.count("□"), "cer": round(cer(text, ref), 3), "usd": round(usd, 4)})
        print(rows[-1])
    (run / "outputs.jsonl").write_text("\n".join(json.dumps(x, ensure_ascii=False) for x in recs) + "\n", encoding="utf-8")
    pd.DataFrame(rows).to_csv(run / "summary.csv", index=False)
    (run / "config.json").write_text(json.dumps({
        "run_id": run.name, "model": a.model, "effort": "medium", "max_tokens": 8000, "temperature": "provider default",
        "system": SYSTEM, "task": TASK, "schema": SCHEMA, "image_source": "Internet Archive 06048793.cn, full-size page, "
        "long side scaled to 2000 px, JPEG q90", "image_sha256": hashes, "max_usd": a.max_usd,
        "usd_total": round(spent, 4), "exploratory": True, "approved": "author, 2026-11-23 (\"跑\")"},
        ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{run.name}: ${spent:.4f} for {len(rows)} pages")


if __name__ == "__main__":
    main()
