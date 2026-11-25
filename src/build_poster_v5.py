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
#r1{grid-template-columns:0.44fr 0.56fr}
#r2{grid-template-columns:0.635fr 0.365fr}
#r3{grid-template-columns:0.56fr 0.44fr}
main{gap:0.16in !important}
main>.row{flex:1 1 auto}  /* share any spare page height between the rows */
.box>.in{padding:0.26in 0.34in 0.22in}
h1{font-size:72px}
.brand{gap:.3in}
.brand .logos{display:flex;gap:.3in;align-items:center;justify-content:center}
.brand .penn,.brand .cas{height:.95in !important;width:auto !important;display:block}  /* one row, same height */
.brand{justify-items:center}
h1{font-size:80px}
ol.concl2{margin:0;padding-left:.36in}
ol.concl2 li{margin:0 0 .07in;line-height:1.3}
.hqrs{display:grid;grid-template-columns:repeat(3,auto);gap:.18in}
.hqrs .hqr img{width:1.0in;height:1.0in}
.hqrs .hqr span{font-size:22px}
.pairs{display:grid;grid-template-columns:.4in 1fr 1fr;gap:.1in .12in;align-items:center}
.pairs .n{font-size:30px;font-weight:600;color:var(--accent);text-align:center}
.pairs div{border:2px solid var(--rule);border-radius:10px;padding:.08in .12in;background:#fafbfc;font-size:25px;line-height:1.2}
.pairs div i{color:var(--ink)}
.quiz .qh{font-size:34px;line-height:1.15;color:var(--accent);margin:0 0 .08in}
.quiz .ans.flipped{transform:rotate(180deg);text-align:right;border-top:0;border-bottom:1.5px solid var(--rule);padding:0 0 .08in;margin-top:.12in}
.quiz .opts{display:grid;grid-template-columns:1fr 1fr;gap:.12in}
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
.facts div{display:flex;gap:.14in;align-items:baseline}
.facts .v{font-size:34px;font-weight:600;color:var(--accent)}
.facts .d{color:var(--soft);line-height:1.25}
#r3 .box:first-child svg{max-height:7.4in}
#r1 .two{grid-template-columns:0.45fr 0.55fr !important}
.zhtab{font-size:24px;margin:0 0 .06in;table-layout:auto}
.zhtab th,.zhtab td{padding:.03in .1in;font-size:24px}
.box.contact .cx-qr img{max-width:1.0in}
.box.contact .cw-left .ai4s{width:2.6in !important}
.box.contact>.in{padding:0.14in 0.34in 0.1in !important}
#r3 .stack .box:first-child>.in{padding-top:.22in;padding-bottom:.18in}
.box.contact .cw-line{margin-top:.08in;padding-top:.08in}
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
    """Box 05, redrawn 2026-11-25 for legibility: the viewBox is about as wide as the box on the poster, so
    text sizes are poster pixels (26 titles, 24 box text, 22 notes). Left: the model writes the record.
    Right: code owns the text (tested steps, solid) and a proposed decision that routes each value to an
    accepted record or to review (dashed). * = exploratory (LLM linker)."""
    W, H = 1110, 690
    TINT, TSTROKE, GREEN = "#eef1f7", "#9fb0d0", "#2e7d4f"
    p = [DEFS]

    def t(x, y, s, size=24, wt=400, col=INK, anchor="middle", extra=""):
        p.append(f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{wt}" fill="{col}" text-anchor="{anchor}"{extra}>{s}</text>')

    def rect(x, y, w, h, fill="#fff", stroke=RULE, dash=False, r=12, sw=2):
        d = ' stroke-dasharray="9 7"' if dash else ""
        p.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"{d}/>')

    # legend
    rect(560, 4, 44, 26, TINT, TSTROKE, r=7)
    t(614, 25, "tested in this pilot", 22, col=SOFT, anchor="start")
    rect(820, 4, 44, 26, "#fff", SOFT, dash=True, r=7)
    t(874, 25, "proposed", 22, col=SOFT, anchor="start")

    top = 48
    # left: the model writes the record
    p.append(f'<rect x="0" y="{top}" width="300" height="{H - top - 2}" rx="16" fill="#f5f6f7" stroke="#c4cbd0" stroke-width="2"/>')
    t(150, top + 44, "Model writes", 26, 700, SOFT)
    t(150, top + 76, "the record", 26, 700, SOFT)
    L = [(150, 60, ["Scanned page"]), (250, 96, ["Model reads,", "repairs, writes"]),
         (386, 96, ["Record", "<tspan font-style='italic'>Turritella</tspan> <tspan font-style='italic' fill='" + RED + "'>brevisis</tspan>"]),
         (522, 60, ["Researcher trusts it"])]
    prev = None
    for y, h, lines in L:
        rect(22, y, 256, h)
        y0 = y + h / 2 - (len(lines) - 1) * 15 + 8
        for i, s in enumerate(lines):
            t(150, y0 + i * 30, s, 24, 600 if i == 0 else 400, INK if i == 0 else SOFT)
        if prev:
            p.append(arrow(f"M150 {prev + 2} V{y - 4}"))
        prev = y + h
    t(150, 630, "no trace of changes", 22, col=SOFT, extra=' font-style="italic"')

    # right: code owns the text
    x0 = 326
    p.append(f'<rect x="{x0}" y="{top}" width="{W - x0 - 2}" height="{H - top - 2}" rx="16" fill="#fff" stroke="{NAVY}" stroke-width="2.5"/>')
    t(x0 + 24, top + 44, "Code owns the text", 26, 700, NAVY, "start")
    bx, bw, bh = x0 + 24, 360, 84
    R = [(120, "OCR text", ("value F1 0.60 → 0.95", RED)),
         (244, "Model points to a quote", ("value F1 0.93–0.98", NAVY)),
         (368, "Code checks the quote", ("slices the value from the text", SOFT)),
         (492, "Link to GBIF", ("recall 0.59 → 0.91*", RED))]
    prev = None
    for y, title, (val, col) in R:
        rect(bx, y, bw, bh, TINT, TSTROKE)
        t(bx + 20, y + 36, title, 24, 600, INK, "start")
        t(bx + 20, y + 67, val, 22, 400, col, "start")
        if prev:
            p.append(arrow(f"M{bx + bw / 2} {prev + 2} V{y - 4}"))
        prev = y + bh
    p.append(robot(bx + bw - 34, 244 + 12, 0.62))
    # decision (proposed)
    cx, cy, hw, hh = 935, 410, 150, 74
    p.append(arrow(f"M{bx + bw + 2} {492 + bh / 2} H{bx + bw + 28} V{cy} H{cx - hw - 4}"))
    p.append(f'<path d="M{cx} {cy - hh} L{cx + hw} {cy} L{cx} {cy + hh} L{cx - hw} {cy} Z" fill="#fff" stroke="{SOFT}" stroke-width="2" stroke-dasharray="9 7"/>')
    t(cx, cy - 6, "Evidence", 24, 600, NAVY)
    t(cx, cy + 24, "sufficient?", 24, 600, NAVY)
    # no: review (above)
    ry = 150
    rect(cx - 152, ry, 304, 96, dash=True, stroke=SOFT)
    t(cx, ry + 38, "Review", 24, 700, NAVY)
    t(cx, ry + 70, "re-check scan, or a person", 21, col=SOFT)
    p.append(arrow(f"M{cx} {cy - hh - 2} V{ry + 96 + 4}", dash=True))
    t(cx + 14, cy - hh - 20, "no", 22, col=RED, anchor="start")
    # yes: accept (below)
    ay = 540
    p.append(arrow(f"M{cx} {cy + hh + 2} V{ay - 4}", dash=True))
    t(cx + 14, cy + hh + 30, "yes", 22, col=GREEN, anchor="start")
    rect(cx - 152, ay, 304, 96, "#eef6f0", GREEN, dash=True)
    t(cx, ay + 38, "Accept record", 24, 700, INK)
    t(cx, ay + 70, "page, line, quote kept", 22, col=SOFT)
    return (f'<svg viewBox="-3 -3 {W + 6} {H + 6}" width="100%" role="img" aria-label="Two designs. Model writes the '
            f'record: scanned page, the model reads, repairs and writes, record Turritella brevisis, researcher trusts '
            f'it; no trace of changes. Code owns the text: OCR text, value F1 0.60 to 0.95; the model, drawn as a '
            f'robot, points to a quote, value F1 0.93 to 0.98; code checks the quote and slices the value from the '
            f'text; link to GBIF, recall 0.59 to 0.91 with an exploratory LLM linker. These steps were tested. '
            f'Proposed: if the evidence is sufficient, accept the record with page, line and quote kept; if not, '
            f'review by re-checking the scan or by a person.">' + "\n".join(p) + "</svg>")


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
    <p class="kicker">Work in progress · Deep Matters 2026 · Agents for Science · London</p>
    <h1>Where do AI agents lose evidence in historical scientific literature?</h1>
    <p class="key"><b>Key finding:</b> modern OCR lifted value F1 from 0.60–0.64 to 0.95–0.98, yet 14 of 34 correctly extracted bird names still failed direct database linking. Accurate extraction is not enough for trustworthy scientific evidence.</p>
    <p class="authors"><b>Dekun Sun</b> <span class="aff">· University of Pennsylvania, MAS-CS · volunteer, California Academy of Sciences, Scientific Computing</span></p>
  </div>
  <div class="brand">
    <div class="logos"><img class="penn" src="fig/penn_logo_reverse.png" alt="University of Pennsylvania"></div>
    <div class="hqr"><img src="fig/qr_repo.svg" alt="QR code to the BioEvidenceBench repository"><span>github.com/dekunsun/BioEvidenceBench</span></div>
  </div>
</header>

<main>
<div class="row" id="r1">
<div class="box">
  <p class="act">01 · Motivation</p>
  <div class="in">
    <h2>An agent that quotes the OCR faithfully can still file the wrong species.</h2>
    <div class="scans">
      <img src="fig/v5/hook_shell_grey.png" alt="Bulimus chilensis, Reeve plate XVII" style="height:1.75in">
      <img src="fig/v5/hook_scan_grey.png" alt="BULIMUS CHILENSIS printed in Reeve 1849, BHL page 8966790" style="width:100%">
    </div>
    {motivation_svg()}
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
      <div><span class="v">16</span><span class="d">test pages, Reeve 1849 and Butler 1907</span></div>
      <div><span class="v">421</span><span class="d">test mentions labelled first (607 in all)</span></div>
      <div><span class="v">0.90</span><span class="d">agreement between two labellers</span></div>
    </div>
  </div>
</div>
</div>

<div class="row" id="r2">
<div class="box">
  <p class="act">03 · Results</p>
  <div class="in">
    <h2>Most evidence was lost at reading and linking; extraction lost little on these pages</h2>
    <div class="big3">
      <div><p class="lab">OCR · Butler</p><p class="num">0.60 → 0.95</p><p class="what">value F1, same pages, better OCR</p></div>
      <div><p class="lab">Entity linking</p><p class="num">14 / 34</p><p class="what">read right, still not linked</p></div>
      <div><p class="lab">Shared errors</p><p class="num">99–100%</p><p class="what">model agreement; auto-accept set on library OCR still held 50 (Butler) and 75 (Reeve) errors</p></div>
    </div>
    <div class="grid3">
      <div><p class="sub-h">A · Three texts: OCR decides F1</p>
        <figure><img src="fig/v5/f1_by_text.png" alt="Value F1 by text: library OCR 0.60 and 0.64, modern OCR 0.95 and 0.98, expert transcription 0.98 and 0.98, with 95% intervals"></figure></div>
      <div><p class="sub-h">B · Names intact predict F1</p>
        <figure><img src="fig/v5/names_vs_f1.png" alt="Value F1 against share of names intact after OCR, Spearman 0.95 Butler and 1.00 Reeve"></figure>
        <p class="note" style="margin:.06in 0 0"><b class="ink">Page CER does not</b> <span style="white-space:nowrap">(ρ = −0.11 / −0.61)</span></p></div>
      <div><p class="sub-h">C · Linking 34 correctly read names</p>
        <figure><img src="fig/v5/link_recall.png" alt="Link recall: plain GBIF lookup 0.59, with context hint 0.62, LLM linker Haiku 0.76, Opus 0.91"></figure></div>
    </div>
  </div>
</div>
<div class="box quiz">
  <p class="act">04 · Try it</p>
  <div class="in">
    <h2 class="qh">Printed, or written by OCR?</h2>
    <p class="note" style="margin:0 0 .12in">Can you spot the error a scientific agent might miss?</p>
    <img class="qscan" src="fig/v5/quiz_granulosus.png" alt="The printed lines: Lesson, Voy. de la Coquille, pl. 8. f. 3. Bulimus granulosus, Broderip.">
    <p class="note" style="margin:.04in 0 .12in;font-size:22px">Reeve, <i>Conchologia iconica</i> (1849), BHL page 8966790</p>
    <p style="margin:0 0 .08in">Which name is on the page?</p>
    <div class="opts"><div class="opt"><b>A</b><i>Bulimus granulatus</i></div>
    <div class="opt"><b>B</b><i>Bulimus granulosus</i></div></div>
    <p style="margin:.1in 0 0;font-weight:600;color:var(--accent)">Both look scientifically plausible. Only one is supported by the source.</p>
    <p class="ans flipped">Answer: B. A is a modern OCR model's reading.</p>
    <p class="sub-h" style="margin:.14in 0 .02in">Exploratory extension: classical Chinese</p>
    <div class="bencao"><img src="fig/v2/bencao_chars.png" alt="陶弘景 as written in the Siku quanshu manuscript of the Bencao gangmu, 弘 one stroke short"><span class="zh" style="font-size:34px;color:var(--accent)">→ 陶弘景</span></div>
    <p class="note" style="margin:.02in 0 0">本草綱目 manuscript: the model writes the modern form.</p>

  </div>
</div>
</div>

<div class="row" id="r3">
<div class="box">
  <p class="act">05 · Proposed Framework</p>
  <div class="in">
    <h2>Code owns the text; the model points, quotes, and defers</h2>
    {framework_svg()}
    <p class="note" style="margin:.08in 0 0">* Exploratory. When the model repairs the text (left), ~8% of the values it changes are wrong.</p>
  </div>
</div>
<div class="stack">
<div class="box">
  <p class="act">06 · Conclusion</p>
  <div class="in">
    <p class="sub-h" style="margin:0 0 .08in">Three rules for evidence-grounded scientific agents</p>
    <ol class="concl2">
      <li><b>Gate reading on name survival, not average error.</b> Page CER did not predict F1 (ρ = −0.11 / −0.61).</li>
      <li><b>Spend reasoning on linking, not extraction.</b> Small models extract almost as well at ~1/15 the cost; an LLM linker raised recall 0.59 → 0.91.*</li>
      <li><b>Verify against the source, not consensus.</b> 99–100% model agreement still passed 50 and 75 errors.</li>
    </ol>
    <p class="note" style="margin:.06in 0 0">Two English printed books, 16 locked test pages, pre-registered; * exploratory. Next: a hand-copied Chinese manuscript and timed audits.</p>
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
</body>
</html>
"""


if __name__ == "__main__":
    make_images()
    (ROOT / "poster" / "poster.html").write_text(page())
    print("written poster/poster.html")
