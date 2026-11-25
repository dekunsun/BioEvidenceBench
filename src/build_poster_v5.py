"""Build poster/poster.html, version 5 (2026-11-25): the LiveLab poster's layout and CSS
(/home/user/dekunsun/livelab/poster/poster.html) with BioEvidenceBench content. The author found v4 too
wordy and the large yellow scans busy, and asked for the LiveLab look: tinted card headers, one bold line
per section, diagrams over text, scans small and in grey. The SVG diagrams are written here so their
coordinates are in one place. Charts: src/plot_poster_v5.py; grey scans made from poster/fig/v2.

    python src/build_poster_v5.py && node poster/render.js "$PWD/poster" poster A1
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIVELAB = Path("/home/user/dekunsun/livelab/poster/poster.html")
NAVY, SOFT, INK, RULE, RED = "#011F5B", "#4d5a55", "#15201c", "#d9dee6", "#a8463c"
FS = 30.2  # LiveLab's diagram text size


def css() -> str:
    """LiveLab's stylesheet, resized from 24 x 36 in to A1 (24 x 33.92 in zoomed to 594 x 841 mm)."""
    s = LIVELAB.read_text()
    c = s[s.index("<style>") + 7:s.index("</style>")]
    c = c.replace("@page { size: 24in 36in; margin: 0; }", "@page { size: 594mm 841mm; margin: 0; }")
    c = c.replace("html,body{margin:0;padding:0;width:24in;height:36in;",
                  "html,body{margin:0;padding:0;width:594mm;height:841mm;overflow:hidden;")
    c = c.replace(".poster{width:24in;height:36in;", ".poster{zoom:0.9744;width:24in;height:33.92in;")
    c = c.replace('"Noto Sans",sans-serif', '"Noto Sans","WenQuanYi Zen Hei",sans-serif')
    c += """
/* BioEvidenceBench additions */
#r1{grid-template-columns:0.5fr 0.5fr}
#r2{grid-template-columns:0.68fr 0.32fr}
#r3{grid-template-columns:0.6fr 0.4fr}
main{gap:0.16in !important}
main>.row{flex:1 1 auto}
main>#r3{flex:0 0 auto}  /* last row only as tall as its content, so 06 has no empty space */  /* share any spare page height between the rows */
.box>.in{padding:0.26in 0.34in 0.22in}
h1{font-size:72px}
.kicker .proj{color:#fff;font-weight:700;font-size:32px;margin-right:.06in}
.brand{display:flex !important;flex-direction:column;align-items:center;justify-content:center;gap:.34in}  /* Penn logo above, QR below (as in LiveLab) */
header{gap:.3in !important}
.brand .hqr{display:flex;flex-direction:column;align-items:center}
.brand .hqr img{width:1.05in !important;height:1.05in !important;margin:0}
.brand .hqr span{font-size:20px !important;margin-top:.06in;line-height:1.25;text-align:center}
.brand{position:relative}
.brand .hqr{position:relative}
.brand .logos{display:flex;gap:.3in;align-items:center;justify-content:center}
.brand .penn,.brand .cas{height:.8in !important;width:auto !important;display:block}  /* one row, same height */
.brand{justify-items:center}
h1{font-size:80px}
.concl-wrap{margin:auto 0}  /* 06: one block, centred in the card */
ol.concl2{margin:0;padding-left:.36in}
ol.concl2 li{margin:0;padding:.12in 0;line-height:1.3;border-bottom:1.5px solid var(--rule)}
ol.concl2 li:last-child{border-bottom:0}
.hqrs{display:grid;grid-template-columns:repeat(3,auto);gap:.18in}
.hqrs .hqr img{width:1.0in;height:1.0in}
.hqrs .hqr span{font-size:22px}
.pairs{display:grid;grid-template-columns:.4in 1fr 1fr;gap:.1in .12in;align-items:center}
.pairs .n{font-size:30px;font-weight:600;color:var(--accent);text-align:center}
.pairs div{border:2px solid var(--rule);border-radius:10px;padding:.08in .12in;background:#fafbfc;font-size:25px;line-height:1.2}
.pairs div i{color:var(--ink)}
/* 04: two light panels, one type scale (title 24 bold, body 24, notes 20) */
.quiz .panel{border:1.5px solid var(--rule);border-radius:10px;background:#f7f8fb;padding:.16in .2in}

.quiz .panel p{margin:0}
.quiz .ph{font-weight:700;color:var(--accent);margin-bottom:.12in !important}
.quiz .pn{font-size:20px;color:var(--soft);margin-top:.06in !important}
.quiz .pq{margin:.14in 0 .08in !important}
.quiz .pk{font-weight:600;color:var(--accent);margin-top:.12in !important}
.quiz .panel .flip{transform:rotate(180deg);text-align:right;background:none;border-radius:0;border-bottom:1.5px solid var(--rule);padding:0 0 .06in;margin-top:.14in !important}
.quiz .panel .bencao img{mix-blend-mode:multiply}
.quiz .panel .opts .opt{background:#fff}
.quiz .panel .opts .opt b,.quiz .panel .opts .opt i{font-size:24px}
.quiz .panel .zh{font-size:32px;color:var(--accent)}
.quiz .qh{font-size:34px;line-height:1.15;color:var(--accent);margin:0 0 .08in}
.quiz .ans.flipped{transform:rotate(180deg);text-align:right;border-top:0;border-bottom:1.5px solid var(--rule);padding:0 0 .08in;margin-top:.12in}
.quiz .opts{display:grid;grid-template-columns:1fr;gap:.1in}
.quiz .opts .opt{margin:0;padding:.1in .14in;gap:.12in}
.quiz .opts .opt b{font-size:26px}
.quiz .opts .opt i{font-size:26px}
.quiz .opt{display:flex;gap:.25in;align-items:baseline;border:2px solid var(--rule);border-radius:12px;padding:.14in .25in;margin:0 0 .14in;background:#fafbfc}
.quiz .opt b{font-size:36px;color:var(--accent);font-weight:600}
.quiz .opt i{font-size:40px;color:var(--ink)}
.quiz .qscan{width:100%;display:block;border:1.5px solid var(--rule);border-radius:6px}
.quiz .ans{margin-top:.08in;padding-top:.08in;border-top:1.5px solid var(--rule);font-size:22px;color:var(--soft)}
.quiz .ans b{color:var(--ink);font-weight:600}
.facts{display:grid;grid-template-columns:repeat(3,1fr);gap:.3in;margin-top:.1in;padding:.12in .2in;background:#f3f5f9;border-radius:10px}
.facts div{display:flex;flex-direction:column;gap:.02in}
.facts .v{font-size:34px;font-weight:600;color:var(--accent)}
.facts .d{color:var(--ink);line-height:1.25}
.facts .d small{display:block;font-size:22px;color:var(--soft)}
#r3 .box:first-child svg{display:block}
#r1 .two{grid-template-columns:minmax(0,0.45fr) minmax(0,0.55fr) !important}
#r1 .two>div:first-child svg{width:100% !important;display:block}
.zhbars{width:100%;display:block;margin:.08in 0 0;mix-blend-mode:multiply}
.zhtab{font-size:24px;margin:.1in 0 0;table-layout:auto}
.zhtab th,.zhtab td{padding:.03in .1in;font-size:24px}
.box.contact .cx-qr img{max-width:1.0in}
.box.contact .cw-left .ai4s{width:2.6in !important}
.box.contact>.in{padding:0.14in 0.34in 0.1in !important}
#r3 .stack .box:first-child>.in{padding-top:.22in;padding-bottom:.18in}
.box.contact .cw-line{margin-top:.08in;padding-top:.08in}
.big3 .agree{grid-column:1 / -1;border-top:1.5px solid var(--rule);padding-top:.1in}
.big3 .punch2{font-weight:600;color:var(--ink)}
.kpis{display:grid;grid-template-columns:repeat(3,1fr);gap:.18in;margin:.06in 0 0}
.kpis>div{background:#f1f3f7;border-radius:10px;padding:.14in .2in}
.kpis p{margin:0}
.kpis .lab{color:var(--soft)}
.kpis .num{font-size:52px;font-weight:700;color:var(--accent);line-height:1.15;margin:.04in 0 .06in;white-space:nowrap;font-variant-numeric:tabular-nums}
.kpis .kt{font-weight:700;color:var(--ink)}
.big3{display:grid;grid-template-columns:1fr 0.85fr 1.35fr;gap:.3in;margin:.08in 0 .05in;padding:.12in .25in;background:#f3f5f9;border-radius:10px}
.big3 p{margin:0}
.big3 .lab{color:var(--soft)}
.big3 .num{font-size:58px;font-weight:700;color:var(--accent);line-height:1.1;white-space:nowrap;font-variant-numeric:tabular-nums}
.big3 .what{color:var(--ink);line-height:1.3}
.punch{font-size:30px;font-weight:600;color:var(--accent);margin:.1in 0 .12in}
.grid3{display:grid;grid-template-columns:repeat(3,1fr);gap:.3in}
.grid3 figure{margin:.04in 0 0}
.dq{display:grid;grid-template-columns:auto 1.1fr 1fr;gap:.25in;align-items:center;margin-top:.14in;padding-top:.14in;border-top:1.5px solid var(--rule)}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:.3in .45in}
.grid2 figure{margin:.05in 0 0}
.plates{display:grid;grid-template-columns:auto auto;justify-content:center;gap:.3in;margin:.05in 0 .12in}
.plates figure{margin:0}
.plates img{height:3.75in;width:auto;display:block;border:1.5px solid var(--rule);border-radius:6px}
.plates figcaption{font-size:22px;margin-top:.04in}
img.line{width:100%;display:block;border:1.5px solid var(--rule);border-radius:6px;margin:0 0 .14in}
.scans{display:grid;grid-template-columns:auto 1fr;gap:.2in;align-items:center;margin:.05in 0 .2in}
.scans img{display:block;border:1.5px solid var(--rule);border-radius:6px}
.code{background:#f3f5f9;border:1.5px solid var(--rule);border-radius:10px;padding:.16in .2in;font-size:26px}
.code .ln{font-family:"DejaVu Sans Mono",monospace;font-size:23px;white-space:pre;color:var(--ink)}
.code .ln i{color:var(--faint);font-style:normal}
.code .hl{background:#dfe6f3;outline:2px solid var(--accent);border-radius:3px}
.code .out{font-family:"DejaVu Sans Mono",monospace;font-size:23px;color:var(--accent);margin:.1in 0}
.code p{margin:.08in 0 0;color:var(--soft)}
.choices{display:grid;grid-template-columns:1fr 1fr;gap:.15in;margin:.1in 0}
.choices div{border:2px solid var(--accent);border-radius:10px;padding:.1in;text-align:center;font-style:italic;font-weight:400;color:var(--accent)}
.flip{transform:rotate(180deg);color:var(--soft);background:#f3f5f9;border-radius:8px;padding:.1in .15in;margin:.1in 0 .2in}
.lost{color:#a8463c}
.dl .d b{font-weight:600}
.dl{display:grid;grid-template-columns:1.25in 1fr;gap:.12in .2in;align-items:baseline;margin:.1in 0 .1in}
.dl .v{font-size:34px;font-weight:600;color:var(--accent);text-align:right;font-variant-numeric:tabular-nums}
.dl .d b{display:block}
.dl .d span{color:var(--soft)}
.zh{font-family:"WenQuanYi Zen Hei",sans-serif}
.bencao{display:grid;grid-template-columns:auto auto 1fr;gap:.2in;align-items:center;margin-top:.1in}
.bencao img{height:.62in;display:block}
/* spacing (2026-11-25): spread spare height evenly instead of leaving it at the bottom of a box */
#r1 .two{align-items:center;flex:1}
#r1 .box:nth-child(2)>.in{display:flex;flex-direction:column}
#r3 .box:first-child>.in{display:flex;flex-direction:column;justify-content:flex-start}
#r3 .box:first-child>.in>svg{margin:auto 0}
#r3 .box:first-child>.in>h2{margin-bottom:0}
.grid2>div:nth-child(4){align-self:center}
"""
    # spread any spare height evenly inside each card instead of leaving it at the bottom
    c += "\n.box>.in{display:flex !important;flex-direction:column;justify-content:space-between !important}\n.box>.in>*{flex:none}\n"
    c += "#r1 .box:first-child svg{width:100% !important;margin:0 auto;display:block}\n"  # keep its text at body size
    # one smaller type scale for the whole poster (2026-11-25): body 24, notes 20, card headers 32
    for old, new in (("font-size:26px", "font-size:24px"), ("font-size:22px", "font-size:20px"),
                     ("font-size:34px", "font-size:32px"), ("font-size:23px", "font-size:20px")):
        c = c.replace(old, new)
    return c


def make_images() -> None:
    """Colour plates and the printed line for box 01 (2026-11-25, after a review that asked for the real
    books to be seen first). Plates: bhl-impact-gt page images, CC BY 3.0 (IMPACT / BHL): Butler plate 96,
    Jay (BHL page 8992569, fetched from the dataset's images/ folder into data/cache/images/), and Reeve
    plate XVII (docs/assets/overview/reeve_plate17.jpg). Margins are cropped; nothing else is changed."""
    from PIL import Image
    out = ROOT / "poster" / "fig" / "v5"
    jay = ROOT / "data" / "cache" / "images" / "butler_plate_0253.webp"
    if jay.exists():
        Image.open(jay).convert("RGB").crop((70, 240, 2110, 2940)).resize((680, 900)).save(out / "butler_jay.jpg", quality=90)
    Image.open(ROOT / "docs/assets/overview/reeve_plate17.jpg").convert("RGB").crop((80, 140, 920, 1120)).save(
        out / "reeve_plate17.jpg", quality=90)
    Image.open(out / "hook_scan_grey.png").crop((0, 52, 970, 150)).save(out / "bulimus_line.png")
    # quiz (box 04): the printed line with Bulimus granulosus, Reeve 1849, BHL page 8966790 (bhl-impact-gt
    # image, CC BY 3.0); position found once with Tesseract word boxes
    from PIL import ImageOps
    page = ROOT / "data" / "cache" / "images" / "8966790.webp"
    if page.exists():
        from PIL import ImageDraw
        q = ImageOps.autocontrast(Image.open(page).convert("L").crop((1300, 405, 2120, 498)), cutoff=1).convert("RGB")
        # box round the printed name, as in box 01 (Bulimus 1395-1513, granulosus 1524-1686, y 452-490 on the page)
        q = ImageOps.expand(q, border=(0, 0, 0, 6), fill="white")  # room under the box line
        ImageDraw.Draw(q).rounded_rectangle((1388 - 1300, 446 - 405, 1694 - 1300, 97), radius=4,
                                            outline=(0, 0, 0), width=4)
        q.save(out / "quiz_granulosus.png")


def box(x, y, w, h, lines, stroke=RULE, dash=False, fill="#fff", anchor="middle"):
    """A rounded box with centred lines; each line is (text, weight, colour)."""
    d = ' stroke-dasharray="9 7"' if dash else ""
    out = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="12" fill="{fill}" stroke="{stroke}" stroke-width="2"{d}/>']
    n = len(lines)
    y0 = y + h / 2 - (n - 1) * 16 + 10
    for i, (t, wt, col) in enumerate(lines):
        tx = x + w / 2 if anchor == "middle" else x + 22
        out.append(f'<text x="{tx}" y="{y0 + i * 32:.0f}" text-anchor="{anchor}" font-size="{FS}" '
                   f'font-weight="{wt}" fill="{col}">{t}</text>')
    return "\n".join(out)


def arrow(d, dash=False):
    s = ' stroke-dasharray="8 6"' if dash else ""
    return f'<path d="{d}" fill="none" stroke="{SOFT}" stroke-width="2.5"{s} marker-end="url(#ah)"/>'


DEFS = (f'<defs><marker id="ah" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" '
        f'orient="auto"><path d="M0 0L10 5L0 10z" fill="{SOFT}"/></marker></defs>')


def robot(cx, top, s=1.0):
    """A small robot for the model: antenna, head with eyes and mouth, ears, body."""
    x = cx - 34 * s
    def r(a, b, w, h, rx, fill=NAVY):
        return f'<rect x="{x + a * s:.1f}" y="{top + b * s:.1f}" width="{w * s:.1f}" height="{h * s:.1f}" rx="{rx * s:.1f}" fill="{fill}"/>'
    def c(a, b, rr, fill=NAVY):
        return f'<circle cx="{x + a * s:.1f}" cy="{top + b * s:.1f}" r="{rr * s:.1f}" fill="{fill}"/>'
    return "".join([
        f'<line x1="{cx}" y1="{top + 4 * s}" x2="{cx}" y2="{top + 18 * s}" stroke="{NAVY}" stroke-width="{4 * s}"/>',
        c(34, 4, 6), r(0, 18, 68, 52, 13), r(-8, 34, 7, 20, 3), r(69, 34, 7, 20, 3),
        c(21, 41, 8, "#fff"), c(47, 41, 8, "#fff"), c(23, 42, 3.5), c(49, 42, 3.5),
        r(22, 56, 24, 5, 2.5, "#fff"), r(12, 74, 44, 22, 7)])


def motivation_svg() -> str:
    W, H = 800, 252
    p = [DEFS]
    cards = [("Printed, 1849", "BULIMUS", "CHILENSIS", INK, RULE),
             ("Library OCR ✗", "BuLlMLS", "CiilLE.NSls", RED, RULE),
             ("Database needs ✓", "Bulimus", "chilensis", NAVY, NAVY)]
    for i, (h, a, b, col, st) in enumerate(cards):
        x = i * 280
        p.append(f'<rect x="{x}" y="0" width="240" height="122" rx="12" fill="#fff" stroke="{st}" stroke-width="2.5"/>')
        p.append(f'<text x="{x + 120}" y="32" text-anchor="middle" font-size="24" font-weight="400" fill="{SOFT}">{h}</text>')
        fam = 'style="font-family:\'DejaVu Sans Mono\',monospace"' if i < 2 else 'font-style="italic"'
        p.append(f'<text x="{x + 120}" y="72" text-anchor="middle" font-size="27" {fam} fill="{col}">{a}</text>')
        p.append(f'<text x="{x + 120}" y="104" text-anchor="middle" font-size="27" {fam} fill="{col}">{b}</text>')
        if i < 2:
            p.append(arrow(f"M{x + 246} 61 H{x + 274}"))
    # the five steps a record depends on; read and link are where most evidence was lost
    p.append(f'<text x="0" y="178" font-size="25" fill="{SOFT}">Five steps must hold; most evidence was lost at the two in red:</text>')
    for i, st in enumerate(["read", "extract", "ground", "link", "review"]):
        x, lost = i * 163, st in ("read", "link")
        col = RED if lost else NAVY
        p.append(f'<rect x="{x}" y="198" width="128" height="50" rx="25" fill="{"#f8eceb" if lost else "#fff"}" stroke="{col}" stroke-width="{3 if lost else 2}"/>')
        p.append(f'<text x="{x + 64}" y="232" text-anchor="middle" font-size="26" font-weight="{600 if lost else 500}" fill="{col}">{st}</text>')
        if i < 4:
            p.append(arrow(f"M{x + 131} 223 H{x + 159}"))
    return (f'<svg viewBox="-3 -3 {W + 6} {H + 6}" width="100%" role="img" aria-label="The printed name '
            f'BULIMUS CHILENSIS, the library OCR BuLlMLS CiilLE.NSls, and the name the database needs, Bulimus '
            f'chilensis. Five steps must hold: read, extract, ground, link, review; most evidence was lost at '
            f'read and link.">' + "\n".join(p) + "</svg>")


def methods_svg() -> str:
    W, H = 560, 600
    p = [DEFS]
    p.append(f'<rect x="120" y="0" width="320" height="56" rx="28" fill="#fff" stroke="{NAVY}" stroke-width="2.5"/>')
    p.append(f'<text x="280" y="37" text-anchor="middle" font-size="{FS}" font-weight="600" fill="{NAVY}">One scanned page</text>')
    p.append(f'<text x="280" y="94" text-anchor="middle" font-size="26" fill="{SOFT}">read three ways</text>')
    p.append(arrow("M280 58 V70"))
    for i, (a, b) in enumerate([("Library", "OCR"), ("Modern", "OCR"), ("Expert", "transcript")]):
        x = i * 190
        p.append(box(x, 112, 175, 90, [(a, 500, INK), (b, 500, INK)]))
        p.append(arrow(f"M{x + 87} 204 V250"))
    p.append(box(70, 256, 420, 90, [("Model returns", 600, INK), ("line + verbatim quote", 400, SOFT)],
                 stroke=SOFT, dash=True))
    p.append(arrow("M280 348 V384"))
    p.append(box(70, 390, 420, 90, [("Code checks the quote,", 600, INK), ("slices the value", 400, SOFT)]))
    p.append(arrow("M280 482 V518"))
    p.append(f'<rect x="20" y="524" width="520" height="64" rx="32" fill="{NAVY}"/>')
    p.append(f'<text x="280" y="566" text-anchor="middle" font-size="{FS}" font-weight="600" fill="#fff">Scored on 421 test-page labels</text>')
    return (f'<svg viewBox="-3 -3 {W + 6} {H + 6}" width="100%" role="img" aria-label="One scanned page, read '
            f'three ways: library OCR, modern OCR, expert transcription. The model returns a line and a verbatim '
            f'quote; code checks the quote and slices the value; scored against 607 hand labels.">'
            + "\n".join(p) + "</svg>")


def framework_svg() -> str:
    """Box 05, simplified 2026-11-25 from the author's sketch: few words, large type (viewBox about the box's
    width, so sizes are poster pixels). Left: the model writes the record (silent changes). Right: the
    evidence-aware workflow; solid steps were tested in this pilot, the dashed decision and its two exits
    are proposed. Each step carries the evidence measured for it (2026-11-25, the author: every step
    tied to evidence); red = evidence lost on the 16 test pages, * = exploratory."""
    W, H = 1460, 800
    TSTROKE, GREEN = "#9fb0d0", "#2e7d4f"
    LOSS_FILL = "#fbf1f0"
    p = [DEFS]

    def t(x, y, s, size=28, wt=400, col=INK, anchor="middle", extra=""):
        p.append(f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{wt}" fill="{col}" text-anchor="{anchor}"{extra}>{s}</text>')

    def rect(x, y, w, h, fill="#fff", stroke=TSTROKE, dash=False, r=12):
        d = ' stroke-dasharray="9 7"' if dash else ""
        p.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{fill}" stroke="{stroke}" stroke-width="2.5"{d}/>')

    # left: the model writes the record; each box can carry the evidence measured for it
    p.append(f'<rect x="0" y="0" width="430" height="{H - 2}" rx="16" fill="#f2f3f5" stroke="#c4cbd0" stroke-width="2"/>')
    t(215, 58, "Model writes", 32, 700, SOFT)
    left = [("Scanned page", None), ("Model repairs", ("~8% of changed", "values incorrect*")), ("Writes value", None), ("Record", None)]
    prev = None
    for i, (lab, ev) in enumerate(left):
        y = 92 if prev is None else prev + 64  # equal arrow gaps whatever the box height
        h = 124 if ev else 80
        rect(40, y, 350, h, fill=LOSS_FILL if ev else "#fff", stroke=RED if ev else "#c4cbd0")
        t(215, y + (40 if ev else 50), lab, 28, 400, INK)
        if ev:
            for k, line in enumerate(ev):
                t(215, y + 76 + k * 28, line, 22, 400, RED)
        if prev:
            p.append(arrow(f"M215 {prev + 2} V{y - 5}"))
        prev = y + h
    t(215, 728, "Silent changes", 28, 400, RED, extra=' font-style="italic"')
    t(215, 768, "* exploratory", 22, 400, SOFT)

    # right: evidence-aware workflow; red = where evidence was lost on the 16 test pages
    x0 = 460
    p.append(f'<rect x="{x0}" y="0" width="{W - x0 - 2}" height="{H - 2}" rx="16" fill="#f6f8fc" stroke="{TSTROKE}" stroke-width="2.5"/>')
    bx, bw, bh, cx = x0 + 40, 540, 92, x0 + 40 + 270
    t(cx, 58, "Evidence-aware workflow", 32, 700, NAVY)  # centred over its step column, like "Model writes"
    steps = [("OCR text", "value F1 0.60 → 0.95", True),
             ("Model points + quotes", "value F1 0.93–0.98", False),
             ("Code verifies + slices", "no recall lost to quoting", False),
             ("Resolve entity", "14 of 34 names not linked", True)]
    prev = None
    for i, (lab, ev, lost) in enumerate(steps):
        y = 86 + i * 112
        rect(bx, y, bw, bh, fill=LOSS_FILL if lost else "#fff", stroke=RED if lost else TSTROKE)
        t(cx - (22 if i == 1 else 0), y + 40, lab, 28, 500, NAVY)
        t(cx - (22 if i == 1 else 0), y + 75, ev, 22, 400, RED if lost else SOFT)
        if prev:
            p.append(arrow(f"M{cx} {prev + 2} V{y - 5}"))
        prev = y + bh
    p.append(robot(bx + bw - 28, 86 + 112 + 12, 0.52))
    # decision (proposed)
    dy, hw, hh = 600, 230, 68
    p.append(arrow(f"M{cx} {prev + 2} V{dy - hh - 5}"))
    p.append(f'<path d="M{cx} {dy - hh} L{cx + hw} {dy} L{cx} {dy + hh} L{cx - hw} {dy} Z" fill="#fff" stroke="{SOFT}" stroke-width="2.5" stroke-dasharray="9 7"/>')
    t(cx, dy - 6, "Evidence", 28, 700, NAVY)
    t(cx, dy + 28, "sufficient?", 28, 700, NAVY)
    # no -> re-check or defer
    rx, rw, ry, rh = 1120, 300, 400, 100
    rect(rx, ry, rw, rh, stroke=SOFT, dash=True)
    t(rx + rw / 2, ry + 42, "Re-check", 28, 500, NAVY)
    t(rx + rw / 2, ry + 76, "or defer", 28, 500, NAVY)
    p.append(arrow(f"M{cx + hw + 2} {dy} H{rx + rw / 2} V{ry + rh + 5}", dash=True))
    t(cx + hw + 60, dy - 14, "No", 26, col=RED)
    # yes -> auditable record
    ay = 712
    p.append(arrow(f"M{cx} {dy + hh + 2} V{ay - 5}", dash=True))
    t(cx + 20, dy + hh + 30, "Yes", 26, col=GREEN, anchor="start")
    rect(bx, ay, bw, 74, "#eef6f0", GREEN, dash=True)
    t(cx, ay + 48, "Auditable record", 28, 700, GREEN)
    # legend
    rect(rx, 660, 40, 26, "#fff", TSTROKE, r=6)
    t(rx + 52, 681, "tested", 22, col=SOFT, anchor="start")
    rect(rx, 702, 40, 26, "#fff", SOFT, dash=True, r=6)
    t(rx + 52, 723, "proposed", 22, col=SOFT, anchor="start")
    rect(rx, 744, 40, 26, LOSS_FILL, RED, r=6)
    t(rx + 52, 765, "evidence lost", 22, col=SOFT, anchor="start")
    return (f'<svg viewBox="-3 -3 {W + 6} {H + 6}" width="100%" role="img" aria-label="Two designs. Model writes: '
            f'scanned page, model repairs, writes value, record; silent changes. Evidence-aware workflow: OCR text, '
            f'the model (drawn as a robot) points and quotes, code verifies the quote and slices the value, resolve '
            f'entity; these steps were tested. Proposed: if the evidence is sufficient, an auditable record; if not, '
            f're-check or defer.">' + "\n".join(p) + "</svg>")


def page() -> str:
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>BioEvidenceBench poster · Deep Matters 2026</title>
<!-- Version 5, built by src/build_poster_v5.py (LiveLab layout and CSS). Do not edit by hand. -->
<style>{css()}</style>
</head>
<body>
<div class="poster">

<header>
  <div>
    <p class="kicker"><span class="proj">BioEvidenceBench</span> · Work in progress · Deep Matters 2026 · Agents for Science · London</p>
    <h1>From historical page to database record:<br>where do AI agents lose evidence?</h1>
    <p class="key"><b>Key finding:</b> modern OCR lifted value F1 from 0.60–0.64 to 0.95–0.98, yet 14 of 34 correctly extracted bird names still failed direct database linking. Accurate extraction is not enough for trustworthy scientific evidence.</p>
    <p class="authors"><b>Dekun Sun</b> <span class="aff">· University of Pennsylvania, MAS-CS · Research Collaborator, California Academy of Sciences, Scientific Computing</span></p>
  </div>
  <div class="brand">
    <div class="logos"><img class="penn" src="fig/penn_logo_reverse.png" alt="University of Pennsylvania"></div>
    <div class="hqr"><img src="fig/qr_repo.svg" alt="QR code to the BioEvidenceBench repository"><span>GitHub</span></div>
  </div>
</header>

<main>
<div class="row" id="r1">
<div class="box">
  <p class="act">01 · Motivation</p>
  <div class="in">
    <h2>An agent that quotes the OCR faithfully can still file the wrong species.</h2>
    <div class="scans">
      <img src="fig/v5/hook_shell_grey.png" alt="Bulimus chilensis, Reeve plate XVII" style="height:2.3in">
      <img src="fig/v5/hook_scan_grey.png" alt="BULIMUS CHILENSIS printed in Reeve 1849, BHL page 8966790" style="width:100%">
    </div>
    {motivation_svg()}
    <p class="note" style="margin:.08in 0 0">Reeve, 1849 · BHL page 8966790</p>
  </div>
</div>
<div class="box">
  <p class="act">02 · Methodology</p>
  <div class="in">
    <h2>Same page, three texts: the model points, code writes the value</h2>
    <div class="two">
      <div>{methods_svg()}</div>
      <div>
        <p class="sub-h">Point, not write</p>
        <div class="code">
          <div class="ln"><i>1 </i> Species 102. (Mus. Cuming.)</div>
          <div class="ln"><i>2 </i> <span class="hl">BULIMUS CHILENSIS</span>. Bul. testâ</div>
          <div class="ln"><i>3 </i> oblongo-ovatâ, tenui, subtiliter</div>
          <div class="out">model → {{"line": 2, "quote": "BULIMUS CHILENSIS"}}</div>
          <p>Code finds the quote in line 2 and slices the value from the text. A quote that differs from the text is logged as a silent correction.</p>
        </div>

      </div>
    </div>
    <div class="facts">
      <div><span class="v">16</span><span class="d">Locked test pages</span></div>
      <div><span class="v">421</span><span class="d">Test mentions<small>607 total</small></span></div>
      <div><span class="v">0.90</span><span class="d">Exact-span agreement</span></div>
    </div>
    <p class="note" style="margin:.08in 0 0">Pre-registered · Evaluation design informed by Lei, Docherty &amp; Cooper (2024).</p>
  </div>
</div>
</div>

<div class="row" id="r2">
<div class="box">
  <p class="act">03 · Results</p>
  <div class="in">
    <h2>Where does reliability break down?</h2>
    <div class="kpis">
      <div><p class="lab">01 · Reading</p><p class="num">0.60 → 0.95</p><p class="kt">Better OCR</p><p class="lab">Value F1 on Butler's pages</p></div>
      <div><p class="lab">02 · Linking</p><p class="num">14 / 34</p><p class="kt">Failed links</p><p class="lab">Despite correct extraction</p></div>
      <div><p class="lab">03 · Verification</p><p class="num">99–100%</p><p class="kt">Model agreement</p><p class="lab">Yet shared errors persist</p></div>
    </div>
    <p class="note" style="margin:.06in 0 0">On legacy OCR, proposed auto-accept sets contained 50 (Butler) and 75 (Reeve) errors.</p>
    <div class="grid3">
      <div><p class="sub-h">A · OCR quality matters</p>
        <figure><img src="fig/v5/f1_by_text.png" alt="Value F1 by text: library OCR 0.60 and 0.64, modern OCR 0.95 and 0.98, expert transcription 0.98 and 0.98, with 95% intervals"></figure></div>
      <div><p class="sub-h">B · Name preservation vs F1</p>
        <figure><img src="fig/v5/names_vs_f1.png" alt="Value F1 against share of names intact after OCR, Spearman 0.95 Butler and 1.00 Reeve"></figure>
        <p class="note" style="margin:.06in 0 0"><b class="ink">Name preservation tracks F1 more closely than CER</b> <span style="white-space:nowrap">(ρ = −0.11 / −0.61)</span></p></div>
      <div><p class="sub-h">C · Correct names, failed links</p>
        <figure><img src="fig/v5/link_recall.png" alt="Link recall: plain GBIF lookup 0.59, with context hint 0.62, LLM linker Haiku 0.76, Opus 0.91 (exploratory)"></figure>
        <p class="note" style="margin:.06in 0 0"><b class="ink">* LLM-assisted linking: exploratory</b></p></div>
    </div>
  </div>
</div>
<div class="box quiz">
  <p class="act">04 · Try it</p>
  <div class="in">
    <div class="panel">
      <p class="ph">Printed, or written by OCR?</p>
      <img class="qscan" src="fig/v5/quiz_granulosus.png" alt="The printed lines: Lesson, Voy. de la Coquille, pl. 8. f. 3. Bulimus granulosus, Broderip.">
      <p class="pn">Reeve 1849, BHL page 8966790</p>
      <p class="pq">Which name is on the page?</p>
      <div class="opts"><div class="opt"><b>A</b><i>Bulimus granulatus</i></div><div class="opt"><b>B</b><i>Bulimus granulosus</i></div></div>
      <p class="pk">Both look plausible. Only one is supported by the source.</p>
      <p class="pn flip">Answer: B. A is a modern OCR model's reading.</p>
    </div>
    <div class="panel">
      <p class="ph">Exploratory: classical Chinese</p>
      <div class="bencao"><img src="fig/v2/bencao_chars.png" alt="陶弘景 as written in the Siku quanshu manuscript of the Bencao gangmu, 弘 one stroke short"><span class="zh">→ 陶弘景</span></div>
      <p class="pn">本草綱目: the model writes the modern form.</p>
      <img class="zhbars" src="fig/v5/bencao_bars.png" alt="Value F1 on six development half-leaves of the Bencao gangmu: scan-verified text 0.98 (CER 0), Opus OCR 0.87 (CER 0.03), Haiku OCR 0.68 (CER 0.15), PaddleOCR 0.72 (CER 0.26)">
      <p class="pn">Six development half-leaves; exploratory.</p>
    </div>
  </div>
</div>
</div>

<div class="row" id="r3">
<div class="box">
  <p class="act">05 · Proposed Framework</p>
  <div class="in">
    <h2>Code owns the text; the model points, quotes, and defers.</h2>
    {framework_svg()}
  </div>
</div>
<div class="stack">
<div class="box">
  <p class="act">06 · Conclusion</p>
  <div class="in">
    <div class="concl-wrap">
    <p class="sub-h" style="margin:0 0 .08in">Three rules for evidence-grounded scientific agents</p>
    <ol class="concl2">
      <li><b>Gate reading on name survival, not average error.</b> Page CER did not predict F1 (ρ = −0.11 / −0.61).</li>
      <li><b>Prioritise linking once extraction is reliable.</b> Small models extract almost as well at ~1/15 the cost; an LLM linker raised recall 0.59 → 0.91.*</li>
      <li><b>Verify against the source, not consensus.</b> 99–100% model agreement still passed 50 and 75 errors.</li>
    </ol>
    <p class="note" style="margin:.06in 0 0">Scope: two English printed books, pre-registered. * Exploratory.</p>
    </div>
  </div>
</div>
<div class="box contact">
  <p class="act">Connect &amp; Explore</p>
  <div class="in">
    <div class="cw">
      <div class="cw-left">
        <img class="ai4s" src="fig/ai4s_logo.png" alt="AI4S.fyi">
        <p>A map of AI4S people, research,<br>companies and capital, read at source.</p>
      </div>
      <div class="cw-qrs">
        <div class="cx-qr"><img src="fig/qr_ai4s.svg" alt="QR code to ai4s.fyi"><span>ai4s.fyi</span></div>
        <div class="cx-qr"><img src="fig/qr_linkedin.svg" alt="QR code to Dekun Sun's LinkedIn profile"><span>LinkedIn</span></div>
      </div>
    </div>
    <p class="cw-line">Dekun (Gloria) Sun on LinkedIn · @gloria_sun on X</p>
  </div>
</div>
</div>
</div>
</main>

</div>
<script>
/* Diagrams are SVG drawn in their own units, so their text would print at many sizes.
   Snap each label to the poster scale: 24 px if it would print at 22 px or more, else 20 px. */
for (const svg of document.querySelectorAll('svg[viewBox]')) {{
  const scale = svg.getBoundingClientRect().width / svg.viewBox.baseVal.width;
  for (const t of svg.querySelectorAll('text')) {{
    const px = parseFloat(t.getAttribute('font-size')) * scale;
    t.setAttribute('font-size', ((px >= 22 ? 24 : 20) / scale).toFixed(2));
  }}
}}
</script>
</body>
</html>
"""


if __name__ == "__main__":
    make_images()
    (ROOT / "poster" / "poster.html").write_text(page())
    print("written poster/poster.html")
