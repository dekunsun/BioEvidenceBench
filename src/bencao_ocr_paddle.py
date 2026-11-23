"""本草綱目 pilot: a non-Claude OCR level, PaddleOCR (open source, runs locally on CPU, $0).

Why: if a Claude model later extracts from Claude's own transcription, OCR and extraction come from one
model family. A second, non-Claude OCR level removes that confound (agreed with the author, 2026-11-23,
"1-4 都做").

Two steps, because PaddleOCR lives in its own virtual environment:

    # once: python3 -m venv pvenv && pvenv/bin/pip install paddlepaddle paddleocr   (tested: 3.3.1 / 3.7.0)
    pvenv/bin/python src/bencao_ocr_paddle.py run          # OCR, raw boxes -> results/<stamp>_bencao_ocr_paddleocr/
    python src/bencao_ocr_paddle.py assemble <run folder>  # reading order -> data/bencao/paddleocr/<pb>.txt

Settings: lang="chinese_cht" (PaddleOCR picks its PP-OCRv6 medium detector and recogniser), text-line
orientation on, document unwarping off, detector input up to 1600 px (second run; the first, with the
default size, is kept for comparison), oneDNN off (with it, PaddlePaddle 3.3.1 stops with
"ConvertPirAttribute2RuntimeAttribute not support" on this machine).

Reading order. PaddleOCR returns one box per run of text, usually one sub-column of a small note or one
stretch of large text. `assemble` puts each box into one of the 8 ruled columns (界欄, located from the
scan as in probe B), drops boxes outside them (the fold margin with book title and leaf number), and
within a column reads top to bottom; boxes whose heights overlap are the two sub-columns of one note and
are read right first, then left. One output line per manuscript column, as for the other OCR levels.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "bencao"
FULL = ROOT / "data" / "cache" / "bencao" / "full"
PAGES = ["036-1b", "036-5a", "036-7b", "036-12b", "036-13a", "036-30a"]
SETTINGS = {"lang": "chinese_cht", "use_doc_orientation_classify": False, "use_doc_unwarping": False,
            "use_textline_orientation": True, "enable_mkldnn": False,
            # detector input up to 1600 px on the long side (default is smaller); the first run with the
            # default missed whole sub-columns (results/20261123-0539_bencao_ocr_paddleocr, CER median 0.36)
            "text_det_limit_type": "max", "text_det_limit_side_len": 1600}


def run() -> None:
    import os
    import hashlib
    os.environ.setdefault("PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK", "True")
    import paddle
    import paddleocr
    from paddleocr import PaddleOCR
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M")
    out = ROOT / "results" / f"{stamp}_bencao_ocr_paddleocr"
    out.mkdir(parents=True)
    ocr = PaddleOCR(**SETTINGS)
    hashes = {}
    for pb in PAGES:
        img = FULL / f"{pb}.jpg"
        hashes[pb] = hashlib.sha256(img.read_bytes()).hexdigest()
        res = ocr.predict(str(img))[0]
        boxes = [{"text": t, "score": round(float(s), 4), "poly": p.tolist()}
                 for t, s, p in zip(res["rec_texts"], res["rec_scores"], res["rec_polys"])]
        (out / f"{pb}.json").write_text(json.dumps(boxes, ensure_ascii=False, indent=0), encoding="utf-8")
        print(pb, len(boxes), "boxes")
    (out / "config.json").write_text(json.dumps({
        "run_id": out.name, "engine": "PaddleOCR", "paddleocr": paddleocr.__version__,
        "paddlepaddle": paddle.__version__, "settings": SETTINGS,
        "image_source": "Internet Archive 06048793.cn, full-size page (data/cache/bencao/full)",
        "image_sha256": hashes, "cost_usd": 0, "exploratory": True,
        "approved": "author, 2026-11-23 (\"1-4 都做\")"}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(out)


def order_column(boxes: list[dict]) -> str:
    """Top to bottom; boxes overlapping in height are one note's sub-columns, right one first."""
    boxes = sorted(boxes, key=lambda b: b["y0"])
    segs: list[list[dict]] = []
    for b in boxes:
        if segs and b["y0"] < max(x["y1"] for x in segs[-1]) - 10:
            segs[-1].append(b)
        else:
            segs.append([b])
    return "".join(b["text"] for s in segs for b in sorted(s, key=lambda b: -b["xc"]))


def assemble(run_dir: str) -> None:
    from PIL import Image
    sys.path.insert(0, str(ROOT / "src"))
    from bencao_probes import column_bounds
    run_dir = Path(run_dir)
    dest = DATA / "paddleocr"
    dest.mkdir(parents=True, exist_ok=True)
    report = []
    for pb in PAGES:
        raw = json.loads((run_dir / f"{pb}.json").read_text(encoding="utf-8"))
        cols = column_bounds(Image.open(FULL / f"{pb}.jpg"))          # right to left, (x_left, x_right)
        per = [[] for _ in cols]
        dropped = []
        for b in raw:
            xs = [p[0] for p in b["poly"]]
            ys = [p[1] for p in b["poly"]]
            b = {**b, "xc": (min(xs) + max(xs)) / 2, "y0": min(ys), "y1": max(ys)}
            k = next((i for i, (lo, hi) in enumerate(cols) if lo <= b["xc"] < hi), None)
            (dropped if k is None else per[k]).append(b)
        text = "\n".join(order_column(c) for c in per)
        (dest / f"{pb}.txt").write_text(text + "\n", encoding="utf-8")
        report.append({"half_leaf": pb, "boxes": len(raw), "dropped_outside_columns": [d["text"] for d in dropped]})
    (run_dir / "assemble.json").write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))


if __name__ == "__main__":
    {"run": lambda: run(), "assemble": lambda: assemble(sys.argv[2])}[sys.argv[1]]()
