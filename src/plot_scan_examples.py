"""Figures cut from the real pages, one shared card style.

    python src/plot_scan_examples.py
    -> docs/assets/overview/fig01_scan_name{,_zh}.png          one species name misread (README figure 1)
    -> docs/assets/overview/fig07_fluent_error{,_zh}.png       a fluent OCR error looks like a real name
    -> docs/assets/overview/fig08_linking_names{,_zh}.png      read correctly, still not linked
    -> docs/assets/overview/fig09_transcription_typo{,_zh}.png even the expert transcription can be wrong

Scans: Reeve (1849) and Butler (1907) pages from the IMPACT ground-truth set (finebooks/bhl-impact-gt,
CC BY 3.0; data/cache/images/). Name positions were found once with Tesseract word boxes and are fixed
below. Every text string is copied from a project file at run time (data/sample/, data/text/,
results/linking_test/link_outcomes.csv), never retyped. Names are set in a monospaced font so that l and I
stay distinguishable; in a wrong reading only the letters that differ from the printed name are red.
Asked for by the author on 2026-11-23 so that readers from other fields can see the original page.
"""
from __future__ import annotations

import difflib
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Rectangle  # noqa: E402
from PIL import Image  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "assets" / "overview"
BG, BAND, NAVY, GREY, EDGE = "#fffdf8", "#137f7d", "#1b2a3a", "#5b6573", "#dfe3e8"
RED, TEAL, STONE = "#b23b3b", "#1f8683", "#9aa3ad"
TINT = {"plain": "#ffffff", "bad": "#f9dedb", "good": "#dcefe9"}
ACCENT = {"plain": STONE, "bad": RED, "good": TEAL}
MARK = {"plain": "", "bad": "✗", "good": "✓"}
MONO = "DejaVu Sans Mono"
FONT = {"en": "DejaVu Sans", "zh": "WenQuanYi Zen Hei"}
SCAN_NOTE = {"en": "Scan: Biodiversity Heritage Library via IMPACT ground truth (finebooks/bhl-impact-gt), CC BY 3.0.",
             "zh": "扫描图：Biodiversity Heritage Library，经 IMPACT 专家转录集（finebooks/bhl-impact-gt），CC BY 3.0。"}


# ---------- helpers -----------------------------------------------------------------------------------

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


def frame(lang: str, W: float, H: float, title: str, sub: str, notes: list[str]):
    fig = plt.figure(figsize=(W, H), dpi=150, facecolor=BG)
    fig.patches.append(Rectangle((0, 1 - 0.07 / H), 1, 0.07 / H, transform=fig.transFigure, color=BAND))
    fig.text(0.04, 1 - 0.32 / H, title, fontsize=21, fontweight="bold", color=NAVY, va="top", family=FONT[lang])
    fig.text(0.04, 1 - 0.78 / H, sub, fontsize=11.5, color=GREY, va="top", family=FONT[lang])
    for k, part in enumerate(notes):
        fig.text(0.04, (0.42 - k * 0.22) / H, part, fontsize=8.5, color=GREY, style="italic", family=FONT[lang])
    return fig


def scan_axes(fig, im, box_xy, crop, left, bottom, top, W, H, max_w=0.56) -> float:
    """The scan crop at its own aspect ratio, as tall as bottom..top allows but at most max_w wide,
    centred vertically in that band; returns its right edge."""
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


def card(fig, lang, x, y, w, h, kind, head=None, foot=None, pad=(0.02, 0.018), head_size=10.5):
    """White card with a tint, a coloured stripe on the left and a ✓/✗ mark top right.
    pad = (left, top) inner padding in figure fractions."""
    px, py = pad
    fig.patches.append(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=0.010",
                                      transform=fig.transFigure, fc=TINT[kind], ec=EDGE, lw=1.0))
    fig.patches.append(Rectangle((x + 0.002, y + 0.66 * py), 0.0045, h - 1.32 * py, transform=fig.transFigure,
                                 color=ACCENT[kind], zorder=3))
    if MARK[kind]:
        fig.text(x + w - 0.7 * px, y + h - 0.9 * py, MARK[kind], ha="right", va="top", fontsize=head_size + 2.5,
                 fontweight="bold", color=ACCENT[kind], family="DejaVu Sans", zorder=5)
    if head:
        fig.text(x + px, y + h - py, head, ha="left", va="top", fontsize=head_size, fontweight="bold",
                 color=NAVY, family=FONT[lang], zorder=5)
    if foot:
        fig.text(x + 0.02, y + 0.016, foot, ha="left", va="bottom", fontsize=9, color=GREY,
                 family=FONT[lang], zorder=5)


def value(fig, xc, yc, text: str, kind: str, ref: str | None, max_w: float, W: float, size: float = 15,
          italic: bool = False):
    """A name in monospace, centred; in a wrong reading only the letters that differ from `ref` are red
    (all red when the reading shares little with it)."""
    n = len(text)
    fs = min(size, max_w * W * 72 / (n * 0.602))           # DejaVu Sans Mono advance = 0.602 em
    step = fs * 0.602 / 72 / W
    colours = [TEAL if kind == "good" else NAVY] * n
    if kind == "bad":
        sm = difflib.SequenceMatcher(None, ref or "", text)
        if ref is None or sm.ratio() < 0.6:
            colours = [RED] * n
        else:
            for op, _, _, j1, j2 in sm.get_opcodes():
                if op != "equal":
                    for j in range(j1, j2):
                        colours[j] = RED
    x0 = xc - n * step / 2
    for i, ch in enumerate(text):
        fig.text(x0 + i * step, yc, ch, ha="left", va="center", fontsize=fs, fontweight="bold", color=colours[i],
                 family=[MONO, "WenQuanYi Zen Hei"], style="italic" if italic else "normal", zorder=5)


def image_in(fig, im, xc, yc, max_w, max_h, W, H):
    iw = max_w
    ih = iw * W / H * im.height / im.width
    if ih > max_h:
        ih = max_h
        iw = ih * H / W * im.width / im.height
    ax = fig.add_axes([xc - iw / 2, yc - ih / 2, iw, ih])
    ax.imshow(im); ax.set_axis_off(); ax.set_zorder(5)


def card_stack(fig, lang, cards, ref, x, right, bottom, top, W, H, name_img):
    """cards: (heading, value or None for the cut-out name, foot, kind); arrows point down."""
    cw, gap = right - x, 0.05
    ch = (top - bottom - gap * (len(cards) - 1)) / len(cards)
    for i, (head, val, foot, kind) in enumerate(cards):
        y = top - (i + 1) * ch - i * gap
        card(fig, lang, x, y, cw, ch, kind, head, foot)
        mid = y + ch * 0.47
        if val is None:
            image_in(fig, name_img, x + cw / 2, mid, cw * 0.80, ch * 0.36, W, H)
        else:
            value(fig, x + cw / 2, mid, val, kind, ref, cw * 0.86, W)
        if i < len(cards) - 1:
            fig.patches.append(FancyArrowPatch((x + cw / 2, y - 0.008), (x + cw / 2, y - gap + 0.008),
                                               transform=fig.transFigure, arrowstyle="-|>", mutation_scale=14,
                                               color=STONE, lw=1.6))


def save(fig, stem: str, lang: str) -> Path:
    p = OUT / (f"{stem}.png" if lang == "en" else f"{stem}_zh.png")
    fig.savefig(p, facecolor=BG)
    plt.close(fig)
    return p


def scan_and_stack(lang, stem, pid, crop, box, title, sub, notes, cards, ref, H):
    W = 12
    fig = frame(lang, W, H, title, sub, notes)
    im = page(pid)
    right = scan_axes(fig, im, box, crop, 0.04, 0.16, 1 - 1.15 / H, W, H)
    card_stack(fig, lang, cards, ref, right + 0.035, 0.96, 0.62 / H + 0.04, 1 - 1.15 / H, W, H,
               name_img=im.crop((box[0] - 4, box[1] - 4, box[2] + 4, box[3] + 4)))
    return save(fig, stem, lang)


# ---------- the figures -------------------------------------------------------------------------------

def scan_name(lang: str) -> Path:
    pid = "8966790"
    legacy = text_of("data/sample/legacy", pid, "CiilLE", ("BuL", "CiilLE.NSls"))
    expert = text_of("data/sample/expert", pid, "CHILENSIS", ("BULIMUS", "CHILENSIS"))
    L = {"en": ("When one species name is misread", "Reeve, Conchologia iconica (1849), Biodiversity Heritage Library page 8966790",
                [("On the printed page", None, "scan, 1849", "plain"),
                 ("Library's older OCR", legacy, "corrupted letters", "bad"),
                 ("What the record needs", expert, "exact name preserved", "good")],
                [SCAN_NOTE["en"], "OCR text copied unchanged; modern OCR and the expert transcription both read the name intact."]),
         "zh": ("一个学名被读错时", "Reeve《Conchologia iconica》（1849），Biodiversity Heritage Library 第 8966790 页",
                [("印刷页上", None, "扫描原图，1849 年", "plain"),
                 ("图书馆旧 OCR", legacy, "字母被读坏", "bad"),
                 ("数据记录需要的", expert, "学名完整保留", "good")],
                [SCAN_NOTE["zh"], "OCR 文字原样复制；现代 OCR 和专家转录都把学名读对了。"])}[lang]
    return scan_and_stack(lang, "fig01_scan_name", pid, (330, 530, 1290, 960), (388, 608, 760, 652),
                          L[0], L[1], L[3], L[2], expert, 5.6)


def fluent_error(lang: str) -> Path:
    pid = "8967281"
    legacy = text_of("data/sample/legacy", pid, "Turritella brevialis", ("Turritella", "brevialis"))
    dots = text_of("data/sample/modern_dots-mocr", pid, "Turritella brevialis", ("Turritella", "brevialis"))
    deep = text_of("data/text/modern_deepseek-ocr2", pid, "Turritella brevisis", ("Turritella", "brevisis"))
    assert legacy == dots
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
    return scan_and_stack(lang, "fig07_fluent_error", pid, (1250, 605, 2140, 750), (1350, 652, 1628, 694),
                          L[0], L[1], L[3], L[2], legacy, 5.2)


def transcription_typo(lang: str) -> Path:
    pid = "8992489"
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
    return scan_and_stack(lang, "fig09_transcription_typo", pid, (560, 600, 1560, 840), (758, 758, 1274, 816),
                          L[0], L[1], L[3], L[2], dots, 6.6)


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
    W, H = 12, 5.8
    fig = frame(lang, W, H, L[0], L[1], L[3])
    xs, widths, kinds = [0.04, 0.375, 0.665], [0.30, 0.255, 0.295], ["plain", "bad", "good"]
    top, rh, gap = 1 - 1.45 / H, 0.18, 0.035
    for j, head in enumerate(L[2]):
        fig.text(xs[j] + 0.02, top + 0.022, head, ha="left", va="bottom", fontsize=11, fontweight="bold",
                 color=NAVY, family=FONT[lang])
    for i, (pid, name, box) in enumerate(rows):
        r = links[(links.page_id.astype(str) == pid) & (links.text == name)].iloc[0]
        genus = str(r.gbif_name).split()[0]
        y = top - (i + 1) * rh - i * gap
        for j in range(3):
            card(fig, lang, xs[j], y, widths[j], rh, kinds[j])
        image_in(fig, page(pid).crop((box[0] - 4, box[1] - 4, box[2] + 4, box[3] + 4)),
                 xs[0] + widths[0] / 2 + 0.004, y + rh / 2, widths[0] * 0.78, rh * 0.62, W, H)
        fig.text(xs[1] + widths[1] / 2 + 0.004, y + rh / 2, L[4].format(g=genus), ha="center", va="center",
                 fontsize=12, color=RED, family=FONT[lang], zorder=5)
        value(fig, xs[2] + widths[2] / 2 + 0.004, y + rh * 0.60, r.accepted_name, "good", None,
              widths[2] * 0.85, W, size=13, italic=True)
        fig.text(xs[2] + widths[2] / 2 + 0.004, y + rh * 0.25, why[name], ha="center", va="center", fontsize=9.5,
                 color=GREY, family=FONT[lang], zorder=5)
        for j in (0, 1):                                         # arrows on every row
            fig.patches.append(FancyArrowPatch((xs[j] + widths[j] + 0.005, y + rh / 2),
                                               (xs[j + 1] - 0.005, y + rh / 2), transform=fig.transFigure,
                                               arrowstyle="-|>", mutation_scale=13, color=STONE, lw=1.6))
    return save(fig, "fig08_linking_names", lang)


def _icon(fig, kind: str, x: float, y: float, s: float, W: float, H: float, colour: str) -> None:
    """A small line icon in a circle, drawn with plain shapes (no icon font): ocr, tag, quote, link, check,
    leaf, key, pin, calendar. (x, y) = centre in figure fractions, s = diameter in inches."""
    from matplotlib.patches import Circle, Polygon, Ellipse, FancyBboxPatch as FB
    from matplotlib.lines import Line2D
    ax = fig.add_axes([x - s / 2 / W, y - s / 2 / H, s / W, s / H])
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.set_axis_off(); ax.set_zorder(6)
    ax.add_patch(Circle((0.5, 0.5), 0.5, color=colour, alpha=0.14))
    lw, c = 1.8, colour
    L = lambda xs, ys: ax.add_line(Line2D(xs, ys, color=c, lw=lw, solid_capstyle="round"))
    if kind == "ocr":
        for (x0, y0, dx, dy) in [(.25, .72, 1, -1), (.75, .72, -1, -1), (.25, .28, 1, 1), (.75, .28, -1, 1)]:
            L([x0, x0 + .1 * dx], [y0, y0]); L([x0, x0], [y0, y0 + .1 * dy])
        for yy in (.42, .5, .58):
            L([.34, .66], [yy, yy])
    elif kind == "tag":
        ax.add_patch(Polygon([(.28, .62), (.5, .78), (.74, .54), (.52, .3), (.28, .46)], closed=True, fill=False, ec=c, lw=lw))
        ax.add_patch(Circle((.38, .56), .035, color=c))
    elif kind == "quote":
        ax.text(.5, .42, "\u201c", ha="center", va="center", fontsize=s * 40, color=c, fontweight="bold", family="DejaVu Serif")
    elif kind == "link":
        pts = [(.5, .72), (.3, .34), (.7, .34)]
        L([pts[0][0], pts[1][0]], [pts[0][1], pts[1][1]]); L([pts[0][0], pts[2][0]], [pts[0][1], pts[2][1]])
        L([pts[1][0], pts[2][0]], [pts[1][1], pts[2][1]])
        for q in pts:
            ax.add_patch(Circle(q, .075, fc="white", ec=c, lw=lw))
    elif kind == "check":
        ax.add_patch(FB((.3, .3), .4, .4, boxstyle="round,pad=0,rounding_size=.06", fill=False, ec=c, lw=lw))
        L([.38, .47, .63], [.5, .4, .6])
    elif kind == "leaf":
        ax.add_patch(Ellipse((.5, .52), .26, .48, angle=-35, fill=False, ec=c, lw=lw))
        L([.36, .62], [.32, .7])
    elif kind == "key":
        ax.text(.5, .5, "#", ha="center", va="center", fontsize=s * 26, color=c, fontweight="bold")
    elif kind == "pin":
        ax.add_patch(Polygon([(.33, .56), (.5, .26), (.67, .56)], closed=True, fc=c, ec=c))
        ax.add_patch(Circle((.5, .6), .17, color=c)); ax.add_patch(Circle((.5, .6), .07, color="white"))
    elif kind == "calendar":
        ax.add_patch(FB((.3, .3), .4, .38, boxstyle="round,pad=0,rounding_size=.04", fill=False, ec=c, lw=lw))
        L([.3, .7], [.56, .56]); L([.4, .4], [.66, .74]); L([.6, .6], [.66, .74])


def pipeline_trace(lang: str) -> Path:
    """README header, in the design language of the concept cover (scan → five steps with icons → record
    table), but every value real: Butler 1907, BHL page 8992647, followed through the pipeline on the
    library's older OCR text. Values are read from the run files; one result per step (the author,
    2026-11-24: less text, more design)."""
    pid = "8992647"
    legacy_name = text_of("data/sample/legacy", pid, "Motacilla beema", ("Motacilla", "beema"))
    legacy_place = text_of("data/sample/legacy", pid, "Rottingdean", ("Rottingdean", "Sussex"))
    legacy_date = text_of("data/sample/legacy", pid, "Rottingdean", ("April", "1898"))
    m = pd.read_csv(ROOT / "results" / "20261119-2052_claude-opus-5-5_test_batch" / "test_mentions.csv",
                    keep_default_na=False)
    m = m[(m.page_id.astype(str) == pid) & (m.version == "legacy") & (m.condition == "G1")]
    ex_name = m[(m.field == "taxon") & (m.value == legacy_name)].iloc[0]
    links = pd.read_csv(ROOT / "results" / "linking_test" / "link_outcomes.csv", keep_default_na=False)
    lk = links[(links.page_id.astype(str) == pid) & (links.text == "Motacilla beema") & (links.version == "expert")
               & (links.condition == "GOLD") & (links.linker == "printed")].iloc[0]
    gl = pd.read_csv(ROOT / "gold" / "gold_links_gloria.csv", keep_default_na=False)
    gl = gl[(gl.page_id.astype(str) == pid) & (gl.text == "Motacilla beema")].iloc[0]
    gm = pd.read_csv(ROOT / "gold" / "gold_mentions_gloria_test.csv", keep_default_na=False)
    scan_date = gm[(gm.page_id.astype(str) == pid) & (gm.field == "date") & (gm.scan_text != "")].iloc[0].scan_text
    genus = str(lk.gbif_name).split()[0]
    line = int(float(ex_name.line))
    steps = {"en": [("OCR", "ocr", legacy_date, "date misread", "bad"),
                    ("Extract", "tag", ex_name.value, "copied as printed", "good"),
                    ("Evidence", "quote", f"line {line}", "quote found in text", "good"),
                    ("Link", "link", genus, "GBIF: genus only", "bad"),
                    ("Review", "check", gl.accepted_name, "curator decides", "good")],
             "zh": [("OCR", "ocr", legacy_date, "日期读错", "bad"),
                    ("抽取", "tag", ex_name.value, "按原文抽出", "good"),
                    ("证据", "quote", f"第 {line} 行", "引文在原文中找到", "good"),
                    ("关联", "link", genus, "GBIF 只到属", "bad"),
                    ("审核", "check", gl.accepted_name, "人工核定", "good")]}[lang]
    title, sub, heads = {
        "en": ("One record, five steps", "Butler, Birds of Great Britain and Ireland (1907) · BHL page 8992647 · real outputs",
               ["accepted taxon", "GBIF key", "locality", "date"]),
        "zh": ("一条记录，五个环节", "Butler《Birds of Great Britain and Ireland》（1907）· BHL 第 8992647 页 · 真实输出",
               ["有效学名", "GBIF 编号", "地点", "日期"])}[lang]
    W, H = 12, 6.6
    fig = frame(lang, W, H, title, sub, [SCAN_NOTE[lang]])
    # left: the page, with a soft shadow; three values boxed (red = misread by the older OCR)
    crop = (255, 1255, 1950, 1700)
    band = 1.95 / H                                          # vertical band for the page and the record table
    sw = min(0.55, band * H * (crop[2] - crop[0]) / (crop[3] - crop[1]) / W)   # keep room for the table
    sh = sw * W * (crop[3] - crop[1]) / (crop[2] - crop[0]) / H
    px, py = 0.04, 1 - 1.2 / H - band + (band - sh) / 2
    fig.patches.append(FancyBboxPatch((px + 0.006, py - 0.012), sw, sh, boxstyle="round,pad=0,rounding_size=0.006",
                                      transform=fig.transFigure, fc="#e6e1d6", ec="none", zorder=-1))
    ax = fig.add_axes([px, py, sw, sh])
    ax.set_zorder(3)
    ax.imshow(page(pid).crop(crop))
    for x0, y0, x1, y1, c in [(900, 1460, 1243, 1512, TEAL), (866, 1586, 1335, 1640, TEAL), (1436, 1586, 1826, 1640, RED)]:
        ax.add_patch(FancyBboxPatch((x0 - crop[0], y0 - crop[1]), x1 - x0, y1 - y0, boxstyle="round,pad=4",
                                    fill=True, fc=c, alpha=0.13, ec=c, lw=2.0))
    ax.set_xticks([]); ax.set_yticks([])
    for s in ax.spines.values():
        s.set_color(EDGE); s.set_linewidth(1.0)
    # right of the page: the record it should end as, a table with icon headers
    tx, tw = px + sw + 0.05, 0.96 - (px + sw + 0.05)
    th, tb = band, 1 - 1.2 / H - band                        # the table fills the whole band
    fig.patches.append(FancyBboxPatch((tx, tb), tw, th, boxstyle="round,pad=0,rounding_size=0.012",
                                      transform=fig.transFigure, fc="#ffffff", ec=EDGE, lw=1.1))
    rec = [(heads[0], "leaf", gl.accepted_name), (heads[1], "key", str(gl.accepted_usage_key)),
           (heads[2], "pin", legacy_place), (heads[3], "calendar", scan_date)]
    fig.text(tx + 0.018, tb + th - 0.2 / H, {"en": "Final record", "zh": "最终记录"}[lang], va="top", fontsize=12,
             fontweight="bold", color=NAVY, family=FONT[lang])
    rowh = (th - 0.55 / H) / 4
    for k, (head, icon, val) in enumerate(rec):
        yc = tb + th - 0.55 / H - (k + 0.5) * rowh
        if k % 2 == 0:
            fig.patches.append(Rectangle((tx + 0.008, yc - rowh / 2 + 0.004), tw - 0.016, rowh - 0.008,
                                         transform=fig.transFigure, color=TINT["good"], alpha=0.55, lw=0))
        _icon(fig, icon, tx + 0.035, yc, 0.34, W, H, TEAL)
        fig.text(tx + 0.065, yc, head, va="center", fontsize=9, color=GREY, family=FONT[lang])
        fig.text(tx + tw * 0.42, yc, val, va="center", fontsize=11.5, fontweight="bold", color=TEAL, family=MONO)
    # curved arrow from the page into the steps
    n, gap = 5, 0.022
    cw = (0.92 - gap * (n - 1)) / n
    ch = 1.95 / H
    cy = tb - 0.5 / H - ch
    fig.patches.append(FancyArrowPatch((px + sw * 0.22, py - 0.02), (0.04 + cw * 0.5, cy + ch + 0.012),
                                       transform=fig.transFigure, connectionstyle="arc3,rad=0.25",
                                       arrowstyle="-|>", mutation_scale=16, color=TEAL, lw=2.4))
    fig.patches.append(FancyArrowPatch((0.04 + 4 * (cw + gap) + cw * 0.5, cy + ch + 0.012), (tx + tw * 0.5, tb - 0.02),
                                       transform=fig.transFigure, connectionstyle="arc3,rad=0.25",
                                       arrowstyle="-|>", mutation_scale=16, color=TEAL, lw=2.4))
    for i, (name, icon, val, cap, kind) in enumerate(steps):
        x = 0.04 + i * (cw + gap)
        fig.patches.append(FancyBboxPatch((x, cy), cw, ch, boxstyle="round,pad=0,rounding_size=0.012",
                                          transform=fig.transFigure, fc="#ffffff", ec=EDGE, lw=1.1))
        fig.patches.append(Rectangle((x + 0.01, cy + ch - 0.05 / H), cw - 0.02, 0.05 / H, transform=fig.transFigure,
                                     color=ACCENT[kind]))
        _icon(fig, icon, x + cw / 2, cy + ch - 0.45 / H, 0.48, W, H, ACCENT[kind] if kind == "bad" else TEAL)
        fig.text(x + cw / 2, cy + ch - 0.8 / H, name, ha="center", va="top", fontsize=12, fontweight="bold",
                 color=NAVY, family=FONT[lang])
        fig.text(x + cw - 0.012, cy + ch - 0.14 / H, MARK[kind], ha="right", va="top", fontsize=13, fontweight="bold",
                 color=ACCENT[kind], family="DejaVu Sans")
        fig.patches.append(FancyBboxPatch((x + 0.012, cy + 0.42 / H), cw - 0.024, 0.36 / H,
                                          boxstyle="round,pad=0,rounding_size=0.008", transform=fig.transFigure,
                                          fc=TINT[kind], ec="none"))
        value(fig, x + cw / 2, cy + 0.6 / H, val, kind, None, cw * 0.84, W, size=11.5)
        fig.text(x + cw / 2, cy + 0.14 / H, cap, ha="center", va="bottom", fontsize=9, color=GREY, family=FONT[lang])
        if i < n - 1:
            fig.patches.append(FancyArrowPatch((x + cw + 0.003, cy + ch / 2), (x + cw + gap - 0.003, cy + ch / 2),
                                               transform=fig.transFigure, arrowstyle="-|>", mutation_scale=12,
                                               color=TEAL, lw=1.6))
    return save(fig, "fig00_pipeline_trace", lang)

def poster_strip() -> Path:
    """Compact horizontal version of figure 1 for the poster's Motivation box: name cut from the scan,
    BHL's legacy OCR, the exact name; same card style, no title (the poster box has its own)."""
    pid, box = "8966790", (388, 608, 760, 652)
    legacy = text_of("data/sample/legacy", pid, "CiilLE", ("BuL", "CiilLE.NSls"))
    expert = text_of("data/sample/expert", pid, "CHILENSIS", ("BULIMUS", "CHILENSIS"))
    W, H = 8.4, 1.25
    fig = plt.figure(figsize=(W, H), dpi=300, facecolor="#ffffff")
    cards = [("Printed, Reeve 1849", "plain"), ("BHL's legacy OCR", "bad"), ("What the record needs", "good")]
    w, gap, y, h = 0.292, 0.058, 0.04, 0.92
    for i, (head, kind) in enumerate(cards):
        x = 0.002 + i * (w + gap)
        card(fig, "en", x, y, w, h, kind, head, pad=(0.024, 0.13), head_size=12)
        mid = y + h * 0.36
        if i == 0:
            image_in(fig, page(pid).crop((box[0] - 4, box[1] - 4, box[2] - 18, box[3] + 4)), x + w / 2 + 0.004, mid,
                     w * 0.80, h * 0.46, W, H)
        else:
            value(fig, x + w / 2 + 0.004, mid, legacy if i == 1 else expert, kind, expert, w * 0.84, W, size=16)
        if i < 2:
            fig.patches.append(FancyArrowPatch((x + w + 0.006, y + h / 2), (x + w + gap - 0.006, y + h / 2),
                                               transform=fig.transFigure, arrowstyle="-|>", mutation_scale=12,
                                               color=STONE, lw=1.5))
    p = ROOT / "poster" / "fig" / "misread_poster.png"
    fig.savefig(p, facecolor="#ffffff")
    plt.close(fig)
    return p


if __name__ == "__main__":
    print(poster_strip())
    for lang in ("en", "zh"):
        for f in (pipeline_trace, scan_name, fluent_error, linking_names, transcription_typo):
            print(f(lang))
