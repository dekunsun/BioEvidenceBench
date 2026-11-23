"""README figure 1 from the real page: the scan on the left, three stacked cards on the right (printed name,
old OCR, what the record needs), in the style of the author's original card figure.

    python src/plot_fig01_scan.py
    -> docs/assets/overview/fig01_scan_name.png      (English labels)
    -> docs/assets/overview/fig01_scan_name_zh.png   (Chinese labels)

Scan: Reeve, Conchologia iconica vol. 5 (1849), BHL page 8966790, image from the IMPACT ground-truth set
(finebooks/bhl-impact-gt, CC BY 3.0; data/cache/images/8966790.webp). The OCR string and the expert reading
are copied from data/sample/{legacy,expert}/8966790.txt, never retyped. Names are set in a monospaced font
so that l and I stay distinguishable. Replaces the schematic fig01_misread_name.png (the author asked for
the real page, 2026-11-23; layout: scan left, cards stacked right, smaller overall).
"""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Rectangle  # noqa: E402
from PIL import Image  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "assets" / "overview"
PAGE = "8966790"
CROP = (330, 530, 1290, 960)              # left column: species number, heading, Latin diagnosis, English name
NAME_BOX = (388, 608, 760, 652)           # "BULIMUS CHILENSIS." on the scan, page pixels
W, H = 12, 5.2                            # figure size, inches
BG, BAND, NAVY, GREY, EDGE = "#fffdf8", "#137f7d", "#1b2a3a", "#5b6573", "#d9dde2"
RED, TEAL = "#b23b3b", "#1f8683"
FILL = ["#ffffff", "#fcecea", "#e8f3f1"]
MONO = "DejaVu Sans Mono"

LABELS = {
    "en": {"font": "DejaVu Sans",
           "title": "When one species name is misread",
           "sub": "Reeve, Conchologia iconica (1849), Biodiversity Heritage Library page 8966790",
           "cards": [("On the printed page", "scan, 1849"), ("Library's older OCR", "corrupted letters"),
                     ("What the record needs", "exact name preserved")],
           "note": ["Scan: Biodiversity Heritage Library via IMPACT ground truth (finebooks/bhl-impact-gt), CC BY 3.0.",
                    "OCR text copied unchanged; modern OCR and the expert transcription both read the name intact."]},
    "zh": {"font": "WenQuanYi Zen Hei",
           "title": "一个学名被读错时",
           "sub": "Reeve《Conchologia iconica》（1849），Biodiversity Heritage Library 第 8966790 页",
           "cards": [("印刷页上", "扫描原图，1849 年"), ("图书馆旧 OCR", "字母被读坏"), ("数据记录需要的", "学名完整保留")],
           "note": ["扫描图：Biodiversity Heritage Library，经 IMPACT 专家转录集（finebooks/bhl-impact-gt），CC BY 3.0。",
                    "OCR 文字原样复制；现代 OCR 和专家转录都把学名读对了。"]},
}


def find(version: str, key: str) -> str:
    for line in (ROOT / "data" / "sample" / version / f"{PAGE}.txt").read_text(encoding="utf-8").splitlines():
        if key in line:
            return line
    raise ValueError(f"{key} not in {version}")


def draw(lang: str) -> Path:
    lab = LABELS[lang]
    font = lab["font"]
    legacy = find("legacy", "CiilLE")
    legacy_name = legacy[legacy.index("BuL"):legacy.index("CiilLE") + len("CiilLE.NSls")]
    expert = find("expert", "CHILENSIS")
    expert_name = expert[:expert.index("CHILENSIS") + len("CHILENSIS")]
    page = Image.open(ROOT / "data" / "cache" / "images" / f"{PAGE}.webp").convert("RGB")

    fig = plt.figure(figsize=(W, H), dpi=150, facecolor=BG)
    fig.patches.append(Rectangle((0, 0.982), 1, 0.018, transform=fig.transFigure, color=BAND))
    fig.text(0.04, 0.94, lab["title"], fontsize=21, fontweight="bold", color=NAVY, va="top", family=font)
    fig.text(0.04, 0.855, lab["sub"], fontsize=11.5, color=GREY, va="top", family=font)

    # left: the scan, framed, with the name boxed
    top, bottom = 0.785, 0.165
    sw = (top - bottom) * H * (CROP[2] - CROP[0]) / (CROP[3] - CROP[1]) / W     # width that fits the crop
    ax = fig.add_axes([0.04, bottom, sw, top - bottom])
    ax.imshow(page.crop(CROP))
    x0, y0, x1, y1 = NAME_BOX
    ax.add_patch(Rectangle((x0 - CROP[0], y0 - CROP[1]), x1 - x0, y1 - y0, fill=False, ec=RED, lw=2.4))
    ax.set_xticks([]); ax.set_yticks([])
    for s in ax.spines.values():
        s.set_color(EDGE); s.set_linewidth(1.2)

    # right: three cards stacked, arrows pointing down
    cx = 0.04 + sw + 0.035
    cw = 0.96 - cx
    gap = 0.045
    ch = (top - bottom - 2 * gap) / 3
    ys = [top - ch, top - 2 * ch - gap, bottom]
    for i, y in enumerate(ys):
        fig.patches.append(FancyBboxPatch((cx, y), cw, ch, boxstyle="round,pad=0,rounding_size=0.012",
                                          transform=fig.transFigure, fc=FILL[i], ec=EDGE, lw=1.1))
        head, foot = lab["cards"][i]
        fig.text(cx + cw / 2, y + ch - 0.02, head, va="top", ha="center", fontsize=11.5, fontweight="bold",
                 color=NAVY, family=font, zorder=5)
        fig.text(cx + cw / 2, y + 0.016, foot, va="bottom", ha="center", fontsize=9.5, color=GREY,
                 family=font, zorder=5)
        if i < 2:
            fig.patches.append(FancyArrowPatch((cx + cw / 2, y - 0.006), (cx + cw / 2, y - gap + 0.006),
                                               transform=fig.transFigure, arrowstyle="-|>", mutation_scale=14,
                                               color=TEAL, lw=1.8))
    mid = lambda i: ys[i] + ch * 0.47                                            # value line inside a card
    # card 1: the name as printed, cut from the scan
    nx0, ny0, nx1, ny1 = NAME_BOX
    name_img = page.crop((nx0 - 4, ny0 - 4, nx1 - 22, ny1 + 4))
    iw = cw * 0.80                                                               # fits inside the card
    ih = iw * W / H * name_img.height / name_img.width
    ia = fig.add_axes([cx + (cw - iw) / 2, mid(0) - ih / 2, iw, ih])
    ia.imshow(name_img); ia.set_axis_off(); ia.set_zorder(5)                    # above the card shape
    # cards 2 and 3: the strings, copied from the files
    fig.text(cx + cw / 2, mid(1), legacy_name, ha="center", va="center", fontsize=15, fontweight="bold",
             color=RED, family=MONO, zorder=5)
    fig.text(cx + cw / 2, mid(2), expert_name, ha="center", va="center", fontsize=15, fontweight="bold",
             color=TEAL, family=MONO, zorder=5)

    for k, part in enumerate(lab["note"]):
        fig.text(0.04, 0.085 - k * 0.042, part, fontsize=8.5, color=GREY, style="italic", family=font)
    name = "fig01_scan_name.png" if lang == "en" else "fig01_scan_name_zh.png"
    fig.savefig(OUT / name, facecolor=BG)
    plt.close(fig)
    return OUT / name


if __name__ == "__main__":
    for lang in ("en", "zh"):
        print(draw(lang))
