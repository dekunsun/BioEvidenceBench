"""Mistral OCR on the 22 sample pages, through OpenRouter's PDF parser (exploratory, DEVIATIONS.md).

    python src/fetch_mistral_ocr_openrouter.py [--max-usd 0.5]

Why OpenRouter: NHM re-OCRs BHL with Mistral OCR; FineBooks' bucket has no Mistral row, and no
Mistral key was available. OpenRouter's `file-parser` plugin with `pdf.engine = "mistral-ocr"` runs
Mistral's OCR on an uploaded PDF and returns the parsed text in the response's file annotation
(docs: openrouter.ai/docs/features/multimodal/pdfs). We send each page scan as a one-page PDF to a
small chat model with max_tokens 5; only the annotation is used, the chat reply is ignored.

What is NOT known: which Mistral OCR version OpenRouter calls (OCR 3 = mistral-ocr-2512, or OCR 4.1).
OpenRouter does not report it, so the text version is named `modern_mistral-ocr-openrouter` and the
run date is recorded; it is not presented as NHM's exact setting.

Input: the IMPACT/BHL page images in data/cache/images/ (CC BY 3.0), converted to a one-page PDF
without resizing. Output: data/text/modern_mistral-ocr-openrouter/<PageID>.txt (OCR text exactly as
returned, minus OpenRouter's <file> wrapper parts), and results/mistral_ocr_openrouter/ with the raw
responses, a manifest (SHA-256 of image, PDF and text; cost; timestamps) and the config.
The key is injected by the session's network proxy; it is never read or stored here.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import io
import json
from datetime import datetime, timezone

import pandas as pd
import requests
from PIL import Image

from common import DATA, ROOT, TEXT

URL = "https://openrouter.ai/api/v1/chat/completions"
CHAT_MODEL = "mistralai/mistral-small-3.2-24b-instruct"   # only carries the file; its reply is ignored
VERSION = "modern_mistral-ocr-openrouter"
OUT = ROOT / "results" / "mistral_ocr_openrouter"
IMAGES = DATA / "cache" / "images"


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def page_pdf(page_id: int) -> tuple[bytes, bytes]:
    img = next(IMAGES.glob(f"{page_id}.*")).read_bytes()
    buf = io.BytesIO()
    Image.open(io.BytesIO(img)).convert("RGB").save(buf, "PDF", resolution=300)
    return img, buf.getvalue()


def ocr_text(resp: dict) -> str:
    """The parsed text from the file annotation, without OpenRouter's <file ...> / </file> wrapper parts."""
    msg = (resp.get("choices") or [{}])[0].get("message", {})
    parts = []
    for a in msg.get("annotations") or []:
        for c in (a.get("file") or {}).get("content") or []:
            t = c.get("text", "") if c.get("type") == "text" else ""
            if t.startswith("<file name=") or t.strip() == "</file>":
                continue
            parts.append(t)
    return "\n".join(parts)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-usd", type=float, default=0.5)
    a = ap.parse_args()
    pages = pd.read_csv(DATA / "sample_split.csv")
    (OUT / "raw").mkdir(parents=True, exist_ok=True)
    (TEXT / VERSION).mkdir(parents=True, exist_ok=True)
    rows, spent = [], 0.0
    for p in pages.itertuples():
        pid = int(p.PageID)
        if spent > a.max_usd:
            raise SystemExit(f"cap ${a.max_usd} reached")
        img, pdf = page_pdf(pid)
        body = {"model": CHAT_MODEL, "max_tokens": 5,
                "messages": [{"role": "user", "content": [
                    {"type": "text", "text": "Reply with OK."},
                    {"type": "file", "file": {"filename": f"{pid}.pdf",
                                              "file_data": "data:application/pdf;base64," + base64.b64encode(pdf).decode()}}]}],
                "plugins": [{"id": "file-parser", "pdf": {"engine": "mistral-ocr"}}]}
        sent = datetime.now(timezone.utc).isoformat(timespec="seconds")
        r = requests.post(URL, json=body, headers={"Authorization": "Bearer proxy-injected"}, timeout=300)
        resp = r.json()
        (OUT / "raw" / f"{pid}.json").write_text(json.dumps(resp, indent=1, ensure_ascii=False), encoding="utf-8")
        text = ocr_text(resp)
        cost = float((resp.get("usage") or {}).get("cost") or 0.0)
        spent += cost
        (TEXT / VERSION / f"{pid}.txt").write_text(text, encoding="utf-8")
        rows.append({"PageID": pid, "book": p.book, "split": p.split, "http_status": r.status_code,
                     "sent_at": sent, "chat_model_served": resp.get("model"), "provider": resp.get("provider"),
                     "image_sha256": sha(img), "pdf_sha256": sha(pdf), "text_sha256": sha(text.encode()),
                     "chars": len(text), "cost_usd": round(cost, 6), "error": json.dumps(resp.get("error"))[:200]
                     if resp.get("error") else ""})
        print(pid, r.status_code, len(text), f"${cost:.4f}")
    man = pd.DataFrame(rows)
    man.to_csv(OUT / "manifest.csv", index=False)
    (OUT / "config.json").write_text(json.dumps({
        "written_at": datetime.now(timezone.utc).isoformat(timespec="seconds"), "endpoint": URL,
        "plugin": {"id": "file-parser", "pdf": {"engine": "mistral-ocr"}}, "chat_model": CHAT_MODEL,
        "text_version": VERSION, "pages": len(man), "usd_total": round(spent, 4),
        "mistral_ocr_version": "not reported by OpenRouter", "exploratory": True}, indent=2), encoding="utf-8")
    print(f"{len(man)} pages, ${spent:.4f}, empty texts: {(man.chars == 0).sum()}")


if __name__ == "__main__":
    main()
