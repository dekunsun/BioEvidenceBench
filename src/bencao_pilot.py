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
    """Kanripo markup removed: ¶ ends a manuscript line; brackets and the column slash of small notes go;
    a character outside Unicode (`&KR1171;`) becomes the placeholder 〓, one character."""
    kr = re.sub(r"&KR\d+;", "〓", kr)
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


# Characters outside the common CJK block that many fonts cannot show (they appear as a box):
# shown in the verification page with the usual character and the code point next to them.
RARE = {"𢎞": "弘", "𠻳": "嗽", "䍐": "罕", "䖅": "蘦", "䘖": "銜", "㗋": "喉"}


def verify_page(embed: bool = False, dest: Path | None = None) -> Path:
    """Scan next to the transcription, one numbered line per manuscript column. Rare characters carry
    their usual form and code point, e.g. 𢎞〔弘 U+2239E〕, so the page can be checked without a font that
    covers CJK extensions. embed=True puts the scans inside the file (to send it on its own)."""
    import base64
    import html as H
    pages = pd.read_csv(DATA / "pilot_pages.csv")

    def mark(line: str) -> str:
        out = []
        for ch in line:
            cp = ord(ch)
            if cp > 0xFFFF or 0x3400 <= cp <= 0x4DBF:
                hint = RARE.get(ch, "")
                out.append(f"<span class='rare'>{H.escape(ch)}</span><span class='hint'>〔{hint} U+{cp:04X}〕</span>")
            elif ch == "〓":
                out.append("<span class='rare'>〓</span><span class='hint'>〔Kanripo: character outside Unicode〕</span>")
            else:
                out.append(H.escape(ch))
        return "".join(out)

    parts = []
    for r in pages.itertuples():
        lines = (DATA / "kanripo_plain" / f"{r.half_leaf}.txt").read_text(encoding="utf-8").split("\n")
        src = f"pages/{r.half_leaf}.jpg"
        if embed:
            src = "data:image/jpeg;base64," + base64.b64encode((OUT / src).read_bytes()).decode()
        lis = "".join(f"<li><span class='n'>{i}</span>{mark(l)}</li>" for i, l in enumerate(lines, 1))
        parts.append(f"<section><h2>{r.half_leaf} · {H.escape(r.why)}</h2><div class='row'>"
                     f"<img src='{src}' alt='scan {r.half_leaf}'><ol>{lis}</ol></div>"
                     f"<p class='meta'>Internet Archive 06048793.cn image n{r.ia_image_n} · Commons DjVu page "
                     f"{r.commons_page_to_confirm} (to confirm)</p></section>")
    rare_rows = "".join(f"<tr><td class='big'>{c}</td><td>{h}</td><td>U+{ord(c):04X}</td></tr>" for c, h in RARE.items())
    page = f"""<!doctype html><html lang="zh"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>本草綱目 pilot: scan check</title><style>
:root{{--bg:#fff;--fg:#1b1b1b;--muted:#666;--rule:#ddd;--hint:#a0522d}}
@media (prefers-color-scheme: dark){{:root:not([data-theme="light"]){{--bg:#151515;--fg:#eee;--muted:#aaa;--rule:#333;--hint:#e0a070}}}}
:root[data-theme="dark"]{{--bg:#151515;--fg:#eee;--muted:#aaa;--rule:#333;--hint:#e0a070}}
body{{background:var(--bg);color:var(--fg);font-family:"Noto Serif CJK TC","Songti TC","HanaMinA","HanaMinB","Hanazono Mincho",serif;margin:0 16px 40px;max-width:1200px}}
h1{{font-size:1.3rem}} h2{{font-size:1.05rem;border-top:1px solid var(--rule);padding-top:12px}}
.row{{display:flex;gap:20px;align-items:flex-start;flex-wrap:wrap}} img{{max-width:520px;width:100%;border:1px solid var(--rule);background:#fff}}
ol{{list-style:none;padding:0;margin:0;flex:1;min-width:280px;font-size:1.15rem;line-height:1.9}}
.n{{display:inline-block;width:2em;color:var(--muted);font-size:.85rem}} .meta{{color:var(--muted);font-size:.85rem}}
.rare{{background:rgba(160,82,45,.15);border-radius:3px}} .hint{{color:var(--hint);font-size:.75rem}}
table{{border-collapse:collapse;margin:8px 0}} td{{border:1px solid var(--rule);padding:2px 10px}} .big{{font-size:1.3rem}}
</style></head><body><h1>本草綱目 卷十二上 · six-page pilot · transcription against scan</h1>
<p>Line 1 is the rightmost column of the scan; columns read right to left. Small two-column notes are joined (right column, then left). Record differences in <code>scan_verify.xlsx</code>. Transcription: Kanseki Repository (CC BY-SA 4.0). Scans: public domain.</p>
<p>Rare characters (CJK extensions) are marked; if your font shows a box, the hint in 〔 〕 gives the usual form and code point. 罕用字已标出：若显示为方框，看〔 〕里的常用字与编码。</p>
<table><tr><td>char</td><td>usual form</td><td>code point</td></tr>{rare_rows}</table>
{''.join(parts)}</body></html>"""
    dest = dest or OUT / "verify.html"
    dest.write_text(page, encoding="utf-8")
    return dest


LEVELS = {"legacy_ia": "Internet Archive Tesseract (horizontal, simplified)",
          "tesseract_chi_tra_vert": "Tesseract 5, chi_tra_vert, local",
          "claude_haiku": "Claude Haiku 5.5 reading the scan (src/bencao_ocr_claude.py)",
          "claude_opus": "Claude Opus 5.5 reading the scan (src/bencao_ocr_claude.py)"}


def score() -> None:
    """CER of every OCR level against the Kanripo transcription (markup removed), per half-leaf.
    Not yet scan-verified: differences include Kanripo's own gaps and variant-glyph choices."""
    pages = pd.read_csv(DATA / "pilot_pages.csv")
    rows = []
    for level, desc in LEVELS.items():
        for pb in pages.half_leaf:
            f = DATA / level / f"{pb}.txt"
            if f.exists():
                ref = (DATA / "kanripo_plain" / f"{pb}.txt").read_text(encoding="utf-8")
                rows.append({"level": level, "description": desc, "half_leaf": pb,
                             "cer": round(cer(f.read_text(encoding="utf-8"), ref), 3)})
    d = pd.DataFrame(rows)
    d.to_csv(OUT / "ocr_levels.csv", index=False)
    print(d.pivot(index="half_leaf", columns="level", values="cer").to_string())
    print(d.groupby("level").cer.median().round(3).to_string())


if __name__ == "__main__":
    import sys
    {"tesseract": tesseract_vert, "score": score, "verify": verify_page}.get((sys.argv[1:] or ["main"])[0], main)()
