"""README figure 1 from the real page: the printed name on the scan and the same line in three text versions.

    python src/plot_fig01_scan.py
    -> docs/assets/overview/fig01_scan_name.png      (English labels)
    -> docs/assets/overview/fig01_scan_name_zh.png   (Chinese labels)

Scan: Reeve, Conchologia iconica vol. 5 (1849), BHL page 8966790, image from the IMPACT ground-truth set
(finebooks/bhl-impact-gt, CC BY 3.0; data/cache/images/8966790.webp). The three text lines are copied from
data/sample/{legacy,modern_dots-mocr,expert}/8966790.txt, never retyped. Replaces the schematic
fig01_misread_name.png (the author asked for the real page, 2026-11-23).
"""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import Rectangle  # noqa: E402
from PIL import Image  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "assets" / "overview"
PAGE = "8966790"
CROP = (330, 590, 1290, 885)              # left column: species heading, Latin diagnosis, English name
NAME_BOX = (388, 608, 760, 652)           # "BULIMUS CHILENSIS." on the scan, page pixels
BG, BAND, NAVY, GREY = "#fffdf8", "#137f7d", "#1b2a3a", "#5b6573"
RED, TEAL = "#b23b3b", "#1f8683"

LABELS = {
    "en": {"title": "One printed name, three text versions",
           "sub": "Reeve, Conchologia iconica (1849), BHL page 8966790: the scan and the same line as text",
           "rows": ["Library's older OCR", "Modern OCR (dots.mocr)", "Expert transcription"],
           "note": "Scan: Biodiversity Heritage Library via IMPACT ground truth (finebooks/bhl-impact-gt), "
                   "CC BY 3.0. Text lines copied unchanged from the project's files."},
    "zh": {"title": "同一个印刷学名，三种文字版本",
           "sub": "Reeve《Conchologia iconica》（1849），BHL 第 8966790 页：扫描原图与同一行文字",
           "rows": ["图书馆旧 OCR", "现代 OCR（dots.mocr）", "专家转录"],
           "note": "扫描图：Biodiversity Heritage Library，经 IMPACT 专家转录集（finebooks/bhl-impact-gt），"
                   "CC BY 3.0。文字行从项目文件原样复制。"},
}


def first_line(version: str, key: str) -> str:
    for line in (ROOT / "data" / "sample" / version / f"{PAGE}.txt").read_text(encoding="utf-8").splitlines():
        if key in line:
            return line.strip()
    raise ValueError(f"{key} not in {version}")


def draw(lang: str) -> Path:
    lab = LABELS[lang]
    cjk = "WenQuanYi Zen Hei" if lang == "zh" else "DejaVu Sans"
    legacy = first_line("legacy", "CiilLE")
    modern = first_line("modern_dots-mocr", "CHILENSIS")
    modern = modern[:len("BULIMUS CHILENSIS. Bul. testâ oblongo-ovatâ, tenui,")] + " …"
    expert = first_line("expert", "CHILENSIS")
    rows = [(legacy, "BuLlMLS CiilLE.NSls", RED), (modern, "BULIMUS CHILENSIS", TEAL), (expert, "BULIMUS CHILENSIS", TEAL)]

    fig = plt.figure(figsize=(12, 8.2), dpi=150, facecolor=BG)
    fig.patches.append(Rectangle((0, 0.985), 1, 0.015, transform=fig.transFigure, color=BAND))
    fig.text(0.04, 0.95, lab["title"], fontsize=24, fontweight="bold", color=NAVY, va="top", family=cjk)
    fig.text(0.04, 0.895, lab["sub"], fontsize=13, color=GREY, va="top", family=cjk)

    im = Image.open(ROOT / "data" / "cache" / "images" / f"{PAGE}.webp").convert("RGB").crop(CROP)
    ax = fig.add_axes([0.04, 0.40, 0.92, 0.46])
    ax.imshow(im)
    x0, y0, x1, y1 = NAME_BOX
    ax.add_patch(Rectangle((x0 - CROP[0], y0 - CROP[1]), x1 - x0, y1 - y0, fill=False, ec=RED, lw=2.5))
    ax.set_axis_off()

    for i, (line, name, colour) in enumerate(rows):
        y = 0.30 - i * 0.075
        fig.text(0.04, y, lab["rows"][i], fontsize=13, color=GREY, va="center", family=cjk)
        rest = line[len(name):] if line.startswith(name) else ""
        t = fig.text(0.30, y, name if rest else line, fontsize=14, color=colour, va="center",
                     family="DejaVu Sans Mono", fontweight="bold")
        if rest:
            fig.canvas.draw()
            bb = t.get_window_extent().transformed(fig.transFigure.inverted())
            fig.text(bb.x1, y, rest, fontsize=14, color=NAVY, va="center", family="DejaVu Sans Mono")
    fig.text(0.04, 0.04, lab["note"], fontsize=10, color=GREY, style="italic", family=cjk)
    name = "fig01_scan_name.png" if lang == "en" else "fig01_scan_name_zh.png"
    fig.savefig(OUT / name, facecolor=BG)
    plt.close(fig)
    return OUT / name


if __name__ == "__main__":
    for lang in ("en", "zh"):
        print(draw(lang))
