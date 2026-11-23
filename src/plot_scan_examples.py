"""Three more figures cut from the real pages, in the style of README figure 1 (src/plot_fig01_scan.py).

    python src/plot_scan_examples.py
    -> docs/assets/overview/fig07_fluent_error{,_zh}.png      a fluent OCR error looks like a real name
    -> docs/assets/overview/fig08_linking_names{,_zh}.png     read correctly, still not linked
    -> docs/assets/overview/fig09_transcription_typo{,_zh}.png  even the expert transcription can be wrong

Scans: Reeve (1849) and Butler (1907) pages from the IMPACT ground-truth set (finebooks/bhl-impact-gt,
CC BY 3.0; data/cache/images/). Name positions were found once with Tesseract word boxes and are fixed
below. Every text string is copied from a project file at run time (data/sample/, data/text/,
results/linking_test/link_outcomes.csv), never retyped. Asked for by the author on 2026-11-23 so that
readers from other fields can see the original page.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Rectangle  # noqa: E402
from PIL import Image  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "assets" / "overview"
BG, BAND, NAVY, GREY, EDGE = "#fffdf8", "#137f7d", "#1b2a3a", "#5b6573", "#d9dde2"
RED, TEAL = "#b23b3b", "#1f8683"
FILL = {"plain": "#ffffff", "bad": "#fcecea", "good": "#e8f3f1"}
COLOUR = {"bad": RED, "good": TEAL, "plain": NAVY}
MONO = "DejaVu Sans Mono"
FONT = {"en": "DejaVu Sans", "zh": "WenQuanYi Zen Hei"}
SCAN_NOTE = {"en": "Scan: Biodiversity Heritage Library via IMPACT ground truth (finebooks/bhl-impact-gt), CC BY 3.0.",
             "zh": "扫描图：Biodiversity Heritage Library，经 IMPACT 专家转录集（finebooks/bhl-impact-gt），CC BY 3.0。"}


def page(pid: str) -> Image.Image:
    return Image.open(ROOT / "data" / "cache" / "images" / f"{pid}.webp").convert("RGB")


def text_of(path: str, pid: str, key: str, span: tuple[str, str] | None = None) -> str:
    """The line of a project text file that holds `key`; optionally cut from span[0] to the end of span[1]."""
    for line in (ROOT / path / f"{pid}.txt").read_text(encoding="utf-8").splitlines():
        if key in line:
            if span:
                a = line.index(span[0])
                return line[a:line.index(span[1], a) + len(span[1])]
            return line.strip()
    raise ValueError(f"{key} not in {path}/{pid}")


def frame(lang: str, w: float, h: float, title: str, sub: str, notes: list[str]):
    fig = plt.figure(figsize=(w, h), dpi=150, facecolor=BG)
    fig.patches.append(Rectangle((0, 1 - 0.07 / h), 1, 0.07 / h, transform=fig.transFigure, color=BAND))
    fig.text(0.04, 1 - 0.3 / h, title, fontsize=21, fontweight="bold", color=NAVY, va="top", family=FONT[lang])
    fig.text(0.04, 1 - 0.75 / h, sub, fontsize=11.5, color=GREY, va="top", family=FONT[lang])
    for k, part in enumerate(notes):
        fig.text(0.04, (0.42 - k * 0.22) / h, part, fontsize=8.5, color=GREY, style="italic", family=FONT[lang])
    return fig


def scan_axes(fig, im: Image.Image, box_xy, crop, left, bottom, top, W, H, max_w=0.56):
    """The scan crop at its own aspect ratio, as tall as bottom..top allows but at most max_w wide,
    centred vertically in that band."""
    aspect = (crop[2] - crop[0]) / (crop[3] - crop[1])
    sh = top - bottom
    sw = sh * H * aspect / W
    if sw > max_w:
        sw, sh = max_w, max_w * W / aspect / H
    ax = fig.add_axes([left, (bottom + top - sh) / 2, sw, sh])
    ax.imshow(im.crop(crop))
    x0, y0, x1, y1 = box_xy
    ax.add_patch(Rectangle((x0 - crop[0], y0 - crop[1]), x1 - x0, y1 - y0, fill=False, ec=RED, lw=2.4))
    ax.set_xticks([]); ax.set_yticks([])
    for s in ax.spines.values():
        s.set_color(EDGE); s.set_linewidth(1.2)
    return left + sw


def card_stack(fig, lang, cards, x, right, bottom, top, W, H, name_img=None):
    """cards: (heading, value or None for the image, foot, kind). Arrows point down."""
    cw, gap = right - x, 0.04
    ch = (top - bottom - gap * (len(cards) - 1)) / len(cards)
    for i, (head, value, foot, kind) in enumerate(cards):
        y = top - (i + 1) * ch - i * gap
        fig.patches.append(FancyBboxPatch((x, y), cw, ch, boxstyle="round,pad=0,rounding_size=0.012",
                                          transform=fig.transFigure, fc=FILL[kind], ec=EDGE, lw=1.1))
        fig.text(x + cw / 2, y + ch - 0.018, head, ha="center", va="top", fontsize=11, fontweight="bold",
                 color=NAVY, family=FONT[lang], zorder=5)
        fig.text(x + cw / 2, y + 0.014, foot, ha="center", va="bottom", fontsize=9.5, color=GREY,
                 family=FONT[lang], zorder=5)
        mid = y + ch * 0.48
        if value is None:
            iw = cw * 0.78
            ih = iw * W / H * name_img.height / name_img.width
            if ih > ch * 0.40:                                   # keep clear of the heading and the foot line
                ih = ch * 0.40
                iw = ih * H / W * name_img.width / name_img.height
            ia = fig.add_axes([x + (cw - iw) / 2, mid - ih / 2, iw, ih])
            ia.imshow(name_img); ia.set_axis_off(); ia.set_zorder(5)
        else:
            fig.text(x + cw / 2, mid, value, ha="center", va="center", fontsize=14, fontweight="bold",
                     color=COLOUR[kind], family=MONO, zorder=5)
        if i < len(cards) - 1:
            fig.patches.append(FancyArrowPatch((x + cw / 2, y - 0.005), (x + cw / 2, y - gap + 0.005),
                                               transform=fig.transFigure, arrowstyle="-|>", mutation_scale=13,
                                               color=TEAL, lw=1.7))


def fluent_error(lang: str) -> Path:
    pid, crop, box = "8967281", (1250, 605, 2140, 750), (1350, 652, 1628, 694)
    legacy = text_of("data/sample/legacy", pid, "Turritella brevialis", ("Turritella", "brevialis"))
    dots = text_of("data/sample/modern_dots-mocr", pid, "Turritella brevialis", ("Turritella", "brevialis"))
    deep = text_of("data/text/modern_deepseek-ocr2", pid, "Turritella brevisis", ("Turritella", "brevisis"))
    assert legacy == dots == "Turritella brevialis"
    L = {"en": ("A fluent OCR error looks like a real name", "Reeve, Conchologia iconica (1849), BHL page 8967281",
                [("On the printed page", None, "scan, 1849", "plain"),
                 ("Library's older OCR", legacy, "letters intact (dots.mocr too)", "good"),
                 ("Modern OCR: DeepSeek-OCR-2", deep, "plausible, but not the printed name", "bad")],
                [SCAN_NOTE["en"], "Nothing in 'brevisis' looks broken, so neither a reader nor a model has a cue to check it."]),
         "zh": ("通顺的 OCR 错误看起来像个真学名", "Reeve《Conchologia iconica》（1849），BHL 第 8967281 页",
                [("印刷页上", None, "扫描原图，1849 年", "plain"),
                 ("图书馆旧 OCR", legacy, "字母完整（dots.mocr 也读对了）", "good"),
                 ("现代 OCR：DeepSeek-OCR-2", deep, "看似合理，但不是印刷的学名", "bad")],
                [SCAN_NOTE["zh"], "「brevisis」看不出任何破损，读者和模型都没有理由去怀疑它。"])}[lang]
    W, H = 12, 4.6
    fig = frame(lang, W, H, L[0], L[1], L[3])
    im = page(pid)
    right_of_scan = scan_axes(fig, im, box, crop, 0.04, 0.2, 0.8, W, H)
    card_stack(fig, lang, L[2], right_of_scan + 0.03, 0.96, 0.2, 0.8, W, H,
               name_img=im.crop((box[0] - 4, box[1] - 4, box[2] + 4, box[3] + 4)))
    return save(fig, "fig07_fluent_error", lang)


def transcription_typo(lang: str) -> Path:
    pid, crop, box = "8992489", (560, 560, 1560, 840), (758, 758, 1274, 816)
    legacy = text_of("data/sample/legacy", pid, "LiNX", ("Frin", "illii"))
    dots = text_of("data/sample/modern_dots-mocr", pid, "montifringilla", ("Fringilla", "montifringilla"))
    expert = text_of("data/sample/expert", pid, "nontifringilla", ("Fringilla", "nontifringilla"))
    L = {"en": ("Even the expert transcription can be wrong", "Butler, Birds of Great Britain and Ireland (1907), BHL page 8992489",
                [("On the printed page", None, "scan, 1907", "plain"),
                 ("Library's older OCR", legacy, "unreadable", "bad"),
                 ("Modern OCR (dots.mocr)", dots, "matches the scan", "good"),
                 ("Expert transcription", expert, "one-letter typo, found against the scan", "bad")],
                [SCAN_NOTE["en"], "Gold labels follow the transcription; the scan's reading is kept beside them (column scan_text)."]),
         "zh": ("专家转录也会出错", "Butler《Birds of Great Britain and Ireland》（1907），BHL 第 8992489 页",
                [("印刷页上", None, "扫描原图，1907 年", "plain"),
                 ("图书馆旧 OCR", legacy, "无法辨认", "bad"),
                 ("现代 OCR（dots.mocr）", dots, "与扫描一致", "good"),
                 ("专家转录", expert, "错了一个字母，对照扫描时发现", "bad")],
                [SCAN_NOTE["zh"], "金标准跟随专家转录；扫描上的读法另记在旁边一列（scan_text）。"])}[lang]
    W, H = 12, 5.6
    fig = frame(lang, W, H, L[0], L[1], L[3])
    im = page(pid)
    right_of_scan = scan_axes(fig, im, box, crop, 0.04, 0.16, 0.84, W, H)
    card_stack(fig, lang, L[2], right_of_scan + 0.03, 0.96, 0.16, 0.84, W, H,
               name_img=im.crop((box[0] - 4, box[1] - 4, box[2] + 4, box[3] + 4)))
    return save(fig, "fig09_transcription_typo", lang)


def linking_names(lang: str) -> Path:
    links = pd.read_csv(ROOT / "results" / "linking_test" / "link_outcomes.csv")
    links = links[(links.version == "expert") & (links.condition == "GOLD") & (links.linker == "printed")]
    rows = [("8992647", "Motacilla beema", (900, 1455, 1262, 1512)),
            ("8992644", "Lusciniola schwarzi", (803, 2472, 1225, 2530)),
            ("8992644", "Aedon familiaris", (926, 1795, 1292, 1857))]
    why = {"en": {"Motacilla beema": "now a race of this species", "Lusciniola schwarzi": "moved to another genus",
                  "Aedon familiaris": "now counted within this species"},
           "zh": {"Motacilla beema": "现在是这个种的亚种", "Lusciniola schwarzi": "已移到另一个属",
                  "Aedon familiaris": "现在归入这个种"}}[lang]
    L = {"en": ("Read correctly, still not linked", "Butler, Birds of Great Britain and Ireland (1907), BHL pages 8992647 and 8992644",
                ["Printed in 1907", "Plain GBIF name lookup", "Accepted name today (gold)"],
                [SCAN_NOTE["en"], "GBIF answers cached in results/linking_test/; accepted names decided by the author with Avibase."],
                "genus {g} only"),
         "zh": ("字读对了，学名照样关联不上", "Butler《Birds of Great Britain and Ireland》（1907），BHL 第 8992647、8992644 页",
                ["1907 年印刷的学名", "直接查 GBIF 得到的", "今天的有效学名（金标准）"],
                [SCAN_NOTE["zh"], "GBIF 查询结果缓存在 results/linking_test/；有效学名由作者对照 Avibase 判定。"],
                "只匹配到属 {g}")}[lang]
    W, H = 12, 5.4
    fig = frame(lang, W, H, L[0], L[1], L[3])
    xs, widths = [0.04, 0.375, 0.665], [0.30, 0.255, 0.295]
    top, rh, gap = 0.76, 0.17, 0.035
    for j, head in enumerate(L[2]):
        fig.text(xs[j] + widths[j] / 2, top + 0.025, head, ha="center", va="bottom", fontsize=11.5,
                 fontweight="bold", color=NAVY, family=FONT[lang])
    for i, (pid, name, box) in enumerate(rows):
        r = links[(links.page_id.astype(str) == pid) & (links.text == name)].iloc[0]
        genus = str(r.gbif_name).split()[0]
        y = top - (i + 1) * rh - i * gap
        for j, kind in enumerate(["plain", "bad", "good"]):
            fig.patches.append(FancyBboxPatch((xs[j], y), widths[j], rh, boxstyle="round,pad=0,rounding_size=0.012",
                                              transform=fig.transFigure, fc=FILL[kind], ec=EDGE, lw=1.1))
        im = page(pid).crop((box[0] - 4, box[1] - 4, box[2] + 4, box[3] + 4))
        iw = widths[0] * 0.8
        ih = min(rh * 0.7, iw * W / H * im.height / im.width)
        iw = ih * H / W * im.width / im.height
        ia = fig.add_axes([xs[0] + (widths[0] - iw) / 2, y + (rh - ih) / 2, iw, ih])
        ia.imshow(im); ia.set_axis_off(); ia.set_zorder(5)
        fig.text(xs[1] + widths[1] / 2, y + rh / 2, L[4].format(g=genus), ha="center", va="center",
                 fontsize=12, color=RED, family=FONT[lang] if lang == "zh" else MONO, zorder=5)
        fig.text(xs[2] + widths[2] / 2, y + rh * 0.6, r.accepted_name, ha="center", va="center", fontsize=13,
                 fontweight="bold", color=TEAL, family=MONO, style="italic", zorder=5)
        fig.text(xs[2] + widths[2] / 2, y + rh * 0.24, why[name], ha="center", va="center", fontsize=9.5,
                 color=GREY, family=FONT[lang], zorder=5)
        for j in (0, 1):                                         # arrows on every row
            fig.patches.append(FancyArrowPatch((xs[j] + widths[j] + 0.004, y + rh / 2), (xs[j + 1] - 0.004, y + rh / 2),
                                               transform=fig.transFigure, arrowstyle="-|>", mutation_scale=13,
                                               color=TEAL, lw=1.7))
    return save(fig, "fig08_linking_names", lang)


def save(fig, stem: str, lang: str) -> Path:
    p = OUT / (f"{stem}.png" if lang == "en" else f"{stem}_zh.png")
    fig.savefig(p, facecolor=BG)
    plt.close(fig)
    return p


if __name__ == "__main__":
    for lang in ("en", "zh"):
        for f in (fluent_error, linking_names, transcription_typo):
            print(f(lang))
