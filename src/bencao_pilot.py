"""Bencao gangmu (本草綱目) feasibility pilot: six half-leaves of 卷十二上, Siku quanshu (文淵閣) edition.

    python src/bencao_pilot.py

No model is called and nothing is labelled. For each pilot half-leaf it writes
  data/bencao/kanripo/<pb>.txt        Kanripo transcription, markup kept (CC BY-SA 4.0, see data/bencao/LICENSE.md)
  data/bencao/kanripo_plain/<pb>.txt  the same with Kanripo markup removed: one manuscript line per line
  data/bencao/legacy_ia/<pb>.txt      Internet Archive's Tesseract OCR of the same image (legacy OCR)
  results/bencao_pilot/pages/<pb>.jpg the scan (public domain: Commons, {{PD-scan|PD-old-100-expired}})
and results/bencao_pilot/summary.csv (characters, legacy-OCR CER against the transcription) plus a
verification sheet (results/bencao_pilot/scan_verify.xlsx) for checking the transcription line by line.

Sources (docs/notes/bencao_feasibility.md):
- transcription: github.com/kanripo/KR3e0079, file KR3e0079_036.txt (卷十二上), base edition WYG;
  `<pb:KR3e0079_WYG_036-1b>` marks a half-leaf, `¶` a manuscript line, `(a/b)` a two-column small-character
  note (right column / left column);
- scan and OCR: Internet Archive item 06048793.cn, the CADAL scan that Commons holds as
  "File:CADAL06048793 本草綱目·卷十二上~卷十二下.djvu". Image n (0-based) = half-leaf index + 10
  (n10 = 036-1a, checked by eye on n10-n12); the Commons DjVu page is n + 1 (to confirm in a browser:
  Commons' image servers refused this environment with HTTP 429).
"""
from __future__ import annotations

import re
import urllib.request
from pathlib import Path

import pandas as pd
import rapidfuzz.distance.Levenshtein as Lev

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "bencao"
OUT = ROOT / "results" / "bencao_pilot"
CACHE = ROOT / "data" / "cache" / "bencao"
KR_URL = "https://raw.githubusercontent.com/kanripo/KR3e0079/master/KR3e0079_036.txt"
IA = "06048793.cn"
OFFSET = 10                      # image n of half-leaf 036-1a
COMMONS_FILE = "File:CADAL06048793 本草綱目·卷十二上~卷十二下.djvu"
UA = {"User-Agent": "Mozilla/5.0 (compatible; research-pilot/0.1)"}

# six half-leaves chosen for variety (see results/bencao_pilot/REPORT.md)
PAGES = {
    "036-1b": "甘草 集解: places, cited authors, cited works",
    "036-5a": "甘草 附方: prescriptions (ingredient names test the scope rules)",
    "036-7b": "黃耆 opens: entry heading, 釋名, 集解",
    "036-12b": "人參 釋名: many alternative names",
    "036-13a": "人參 集解: producing regions",
    "036-30a": "桔梗 opens: a name a plain GBIF lookup gets wrong",
}


def get(url: str, dest: Path) -> bytes:
    if not dest.exists():
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=120).read())
    return dest.read_bytes()


def split_half_leaves(text: str) -> dict[str, str]:
    parts = re.split(r"<pb:KR3e0079_WYG_(036-\d+[ab])>¶\n", text)
    return {parts[i]: parts[i + 1] for i in range(1, len(parts), 2)}


def plain(kr: str) -> str:
    """Kanripo markup removed: ¶ ends a manuscript line; brackets and the column slash of small notes go."""
    lines = [re.sub(r"[()/]", "", ln).strip("　 ") for ln in kr.split("¶\n")]
    return "\n".join(ln for ln in lines if ln)


def hocr_pages(html: str) -> list[str]:
    """Text of each hOCR page, one OCR line per line."""
    out = []
    for page in re.split(r"<div class=['\"]ocr_page['\"]", html)[1:]:
        lines = []
        for line in re.findall(r"<span class=['\"]ocr_line['\"].*?</span>\s*</span>", page, re.S):
            words = re.findall(r"<span class=['\"]ocrx_word['\"][^>]*>([^<]*)</span>", line)
            if words:
                lines.append("".join(w.strip() for w in words))
        out.append("\n".join(lines))
    return out


def cer(hyp: str, ref: str) -> float:
    strip = lambda s: re.sub(r"\s", "", s)
    return Lev.distance(strip(hyp), strip(ref)) / max(1, len(strip(ref)))


def main() -> None:
    kr = split_half_leaves(get(KR_URL, CACHE / "KR3e0079_036.txt").decode("utf-8"))
    order = list(kr)
    hocr = hocr_pages(get(f"https://archive.org/download/{IA}/{IA}_hocr.html", CACHE / f"{IA}_hocr.html").decode("utf-8"))
    rows, sheet = [], []
    for pb, why in PAGES.items():
        n = OFFSET + order.index(pb)
        raw, txt = kr[pb], plain(kr[pb])
        for sub, body in (("kanripo", raw), ("kanripo_plain", txt), ("legacy_ia", hocr[n])):
            (DATA / sub).mkdir(parents=True, exist_ok=True)
            (DATA / sub / f"{pb}.txt").write_text(body, encoding="utf-8")
        img = get(f"https://archive.org/download/{IA}/page/n{n}_w1200.jpg", OUT / "pages" / f"{pb}.jpg")
        rows.append({"half_leaf": pb, "ia_item": IA, "ia_image_n": n, "commons_file": COMMONS_FILE,
                     "commons_page_to_confirm": n + 1, "why": why, "lines": txt.count("\n") + 1,
                     "chars": len(re.sub(r"\s", "", txt)), "legacy_cer": round(cer(hocr[n], txt), 3),
                     "image_bytes": len(img)})
        for i, line in enumerate(txt.split("\n"), 1):
            sheet.append({"half_leaf": pb, "line": i, "kanripo_text": line, "matches_scan": "",
                          "scan_reading": "", "note": ""})
    OUT.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(DATA / "pilot_pages.csv", index=False)
    pd.DataFrame(rows).to_csv(OUT / "summary.csv", index=False)
    pd.DataFrame(sheet).to_excel(OUT / "scan_verify.xlsx", index=False)
    print(pd.DataFrame(rows)[["half_leaf", "ia_image_n", "lines", "chars", "legacy_cer"]].to_string(index=False))


def tesseract_vert() -> None:
    """Free local OCR level: Tesseract 5 with the vertical traditional-Chinese model (`chi_tra_vert`, psm 5)
    on the full-resolution Internet Archive images. Needs `apt-get install tesseract-ocr tesseract-ocr-chi-tra-vert`.
    Writes data/bencao/tesseract_chi_tra_vert/<pb>.txt and adds its CER to the summary."""
    import subprocess
    pages = pd.read_csv(DATA / "pilot_pages.csv")
    out = DATA / "tesseract_chi_tra_vert"
    out.mkdir(parents=True, exist_ok=True)
    cers = []
    for r in pages.itertuples():
        img = CACHE / "full" / f"{r.half_leaf}.jpg"
        get(f"https://archive.org/download/{IA}/page/n{r.ia_image_n}.jpg", img)
        text = subprocess.run(["tesseract", str(img), "-", "-l", "chi_tra_vert", "--psm", "5"],
                              capture_output=True, text=True, check=True).stdout
        (out / f"{r.half_leaf}.txt").write_text(text, encoding="utf-8")
        ref = (DATA / "kanripo_plain" / f"{r.half_leaf}.txt").read_text(encoding="utf-8")
        cers.append(round(cer(text, ref), 3))
    pages["tesseract_vert_cer"] = cers
    pages.to_csv(DATA / "pilot_pages.csv", index=False)
    pages.to_csv(OUT / "summary.csv", index=False)
    print(pages[["half_leaf", "legacy_cer", "tesseract_vert_cer"]].to_string(index=False))


if __name__ == "__main__":
    import sys
    tesseract_vert() if sys.argv[1:] == ["tesseract"] else main()
