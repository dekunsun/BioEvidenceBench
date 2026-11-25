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
#r2{grid-template-columns:0.71fr 0.29fr}
#r3{grid-template-columns:0.60fr 0.40fr}
main{gap:0.25in !important}
main>.row{flex:1 1 auto}  /* share any spare page height between the rows */
.box>.in{padding:0.34in 0.34in 0.30in}
h1{font-size:72px}
.brand{gap:.3in}
.brand .penn,.brand .cas{width:2.75in !important;height:auto;display:block}  /* same width, so the two logos share left and right edges */
.brand{justify-items:center}
h1{font-size:80px}
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
.bencao{display:grid;grid-template-columns:auto 1fr;gap:.2in;align-items:center;margin-top:.1in}
.bencao img{height:.62in;display:block}
/* spacing (2026-11-25): spread spare height evenly instead of leaving it at the bottom of a box */
#r1 .two{align-items:center;flex:1}
#r1 .box:nth-child(2)>.in{display:flex;flex-direction:column}
#r3 .box:first-child>.in{display:flex;flex-direction:column;justify-content:space-around}
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
    W, H = 800, 124
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
    return (f'<svg viewBox="-3 -3 {W + 6} {H + 6}" width="100%" role="img" aria-label="The printed name '
            f'BULIMUS CHILENSIS, the library OCR BuLlMLS CiilLE.NSls, and the name the database needs, Bulimus '
            f'chilensis.">' + "\n".join(p) + "</svg>")


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
    p.append(f'<text x="280" y="566" text-anchor="middle" font-size="{FS}" font-weight="600" fill="#fff">Scored against 607 hand labels</text>')
    return (f'<svg viewBox="-3 -3 {W + 6} {H + 6}" width="100%" role="img" aria-label="One scanned page, read '
            f'three ways: library OCR, modern OCR, expert transcription. The model returns a line and a verbatim '
            f'quote; code checks the quote and slices the value; scored against 607 hand labels.">'
            + "\n".join(p) + "</svg>")


def framework_svg() -> str:
    """Box 05 (2026-11-25, from a reviewer's suggestion the author sent): an evidence-aware agent workflow
    with a decision and a loop. Solid boxes are the steps this study measured; the decision, the re-check
    and the person are proposed and untested end to end (dashed). Numbers on the left are the measured
    losses on the 16 test pages; the signals note is the exploratory review-signal result."""
    W, H = 1419, 742
    TINT, LINE = "#eef1f7", "#c4cbd0"
    p = [DEFS]
    cx, x0, bw, bh = 700, 440, 520, 76

    def step(y, title, sub, fill=TINT, tc=NAVY, sc=SOFT, stroke=LINE, dash=False):
        d = ' stroke-dasharray="9 7"' if dash else ""
        p.append(f'<rect x="{x0}" y="{y}" width="{bw}" height="{bh}" rx="12" fill="{fill}" stroke="{stroke}" stroke-width="2"{d}/>')
        p.append(f'<text x="{cx}" y="{y + 33}" text-anchor="middle" font-size="{FS}" font-weight="600" fill="{tc}">{title}</text>')
        if sub:
            p.append(f'<text x="{cx}" y="{y + 63}" text-anchor="middle" font-size="25" fill="{sc}">{sub}</text>')

    def note(y, text, col=SOFT):
        p.append(f'<text x="{x0 - 26}" y="{y}" text-anchor="end" font-size="26" fill="{col}">{text}</text>')

    ys = [0, 106, 212, 318, 424]
    step(ys[0], "Scientific research task", "retrieve the relevant literature", fill=NAVY, tc="#fff", sc="#c9d3e8", stroke=NAVY)
    step(ys[1], "Read source / OCR", "keep the original text")
    step(ys[2], "Extract scientific entities", "points to a line; never rewrites it")
    step(ys[3], "Verify evidence", "quote check + source provenance")
    step(ys[4], "Resolve entity identity", "historical name → modern database")
    for y in ys[:-1]:
        p.append(arrow(f"M{cx} {y + bh + 2} V{y + 106 - 6}"))
    p.append(robot(x0 + bw - 36, ys[2] + 8, 0.6))
    # measured on the test pages (left column)
    p.append(f'<text x="{x0 - 26}" y="26" text-anchor="end" font-size="24" font-style="italic" fill="{SOFT}">measured, 16 test pages</text>')
    note(ys[1] + 47, "F1 0.60 → 0.95 by OCR", RED)
    note(ys[2] + 47, "F1 0.93–0.98, four models")
    note(ys[3] + 47, "0 recall lost to quoting")
    note(ys[4] + 47, "14 of 34 names lost", RED)
    # decision
    dy, dh, dw = 572, 70, 210
    p.append(arrow(f"M{cx} {ys[4] + bh + 2} V{dy - dh - 6}"))
    p.append(f'<path d="M{cx} {dy - dh} L{cx + dw} {dy} L{cx} {dy + dh} L{cx - dw} {dy} Z" fill="#fff" stroke="{NAVY}" stroke-width="2.5" stroke-dasharray="9 7"/>')
    p.append(f'<text x="{cx}" y="{dy - 6}" text-anchor="middle" font-size="{FS}" font-weight="600" fill="{NAVY}">Sufficient</text>')
    p.append(f'<text x="{cx}" y="{dy + 28}" text-anchor="middle" font-size="{FS}" font-weight="600" fill="{NAVY}">evidence?</text>')
    note(dy - 4, "two models agreed, still wrong:", RED)
    note(dy + 28, "50 Butler · 75 Reeve", RED)
    # yes: the record
    ry = 676
    p.append(arrow(f"M{cx} {dy + dh} V{ry - 6}"))
    p.append(f'<text x="{cx + 16}" y="{dy + dh + 26}" font-size="24" fill="{SOFT}">yes</text>')
    p.append(f'<rect x="{x0}" y="{ry}" width="{bw}" height="62" rx="12" fill="{NAVY}"/>')
    p.append(f'<text x="{cx}" y="{ry + 41}" text-anchor="middle" font-size="{FS}" font-weight="600" fill="#fff">Auditable record</text>')
    # no: re-check, then back to reading
    lx, lw, ly, lh = 1050, 330, 246, 140
    lc = lx + lw / 2
    nx = lx + lw - 34  # the "no" line enters the box near its right edge, clear of the signals note
    p.append(f'<path d="M{cx + dw} {dy} H{nx} V{ly + lh + 6}" fill="none" stroke="{SOFT}" stroke-width="2.5" stroke-dasharray="8 6" marker-end="url(#ah)"/>')
    p.append(f'<text x="{cx + dw + 18}" y="{dy - 12}" font-size="24" fill="{SOFT}">no</text>')
    p.append(f'<rect x="{lx}" y="{ly}" width="{lw}" height="{lh}" rx="12" fill="#fff" stroke="{SOFT}" stroke-width="2" stroke-dasharray="9 7"/>')
    for i, (t, wt, col) in enumerate([("Re-check the scan", 600, NAVY), ("or ask a person", 400, SOFT), ("to review", 400, SOFT)]):
        p.append(f'<text x="{lc}" y="{ly + 44 + i * 34}" text-anchor="middle" font-size="{FS}" font-weight="{wt}" fill="{col}">{t}</text>')
    p.append(f'<path d="M{lc} {ly} V{ys[1] + bh / 2} H{x0 + bw + 8}" fill="none" stroke="{SOFT}" stroke-width="2.5" stroke-dasharray="8 6" marker-end="url(#ah)"/>')
    for i, t in enumerate(["Signals that helped:", "OCR junk, no exact", "database match.", "Not: model agreement."]):
        p.append(f'<text x="{nx - 18}" y="{ly + lh + 44 + i * 30}" text-anchor="end" font-size="24" fill="{SOFT}">{t}</text>')
    # legend
    for i, t in enumerate(["Solid: measured here.", "Dashed: proposed, not", "yet tested end to end."]):
        p.append(f'<text x="0" y="{H - 62 + i * 28}" font-size="24" fill="{SOFT}">{t}</text>')
    return (f'<svg viewBox="-3 -3 {W + 6} {H + 6}" width="100%" role="img" aria-label="An evidence-aware scientific '
            f'agent, proposed workflow. Research task; read source or OCR, keeping the original text (measured: F1 '
            f'0.60 to 0.95 by OCR); extract entities, the model (drawn as a robot) points to a line and never rewrites it (F1 0.93 '
            f'to 0.98); verify evidence by quote check and provenance (0 recall lost); resolve identity against a '
            f'modern database (14 of 34 names lost). Then a decision, sufficient evidence? Two models agreeing is '
            f'not enough: agreed but wrong, 50 in Butler and 75 in Reeve. Yes: auditable record. No: re-check the '
            f'scan or ask a person, then read again. Signals that helped: OCR junk and no exact database match, '
            f'not model agreement. Solid steps were measured; dashed ones are proposed and untested end to end.">'
            + "\n".join(p) + "</svg>")


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
    <p class="key"><b>BioEvidenceBench · Key finding:</b> most evidence was lost at reading (F1 0.60 on library OCR, 0.95 on modern OCR) and at linking (14 of 34 names); extraction lost little.</p>
    <p class="authors"><b>Dekun Sun</b> <span class="aff">· University of Pennsylvania, MAS-CS · volunteer, California Academy of Sciences, Scientific Computing</span></p>
  </div>
  <div class="brand">
    <img class="penn" src="fig/penn_logo_reverse.png" alt="University of Pennsylvania">
    <img class="cas" src="fig/cas_logo_reverse.png" alt="California Academy of Sciences">
    <div class="hqr"><img src="fig/qr_repo.svg" alt="QR code to the BioEvidenceBench repository"><span>github.com/dekunsun/BioEvidenceBench</span></div>
  </div>
</header>

<main>
<div class="row" id="r1">
<div class="box">
  <p class="act">01 · Motivation</p>
  <div class="in">
    <h2>Two real books, 1849 and 1907. An agent that quotes the OCR faithfully can still file the wrong species.</h2>
    <div class="plates">
      <figure><img src="fig/v5/reeve_plate17.jpg" alt="Reeve, Conchologia iconica 1849, plate XVII: Bulimus shells in colour"><figcaption>Reeve 1849, shells · plate XVII</figcaption></figure>
      <figure><img src="fig/v5/butler_jay.jpg" alt="Butler, Birds of Great Britain and Ireland 1907, plate 96: the Jay"><figcaption>Butler 1907, birds · plate 96, Jay</figcaption></figure>
    </div>
    <img class="line" src="fig/v5/bulimus_line.png" alt="The printed line BULIMUS CHILENSIS in Reeve 1849, BHL page 8966790">
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
        <p class="gate" style="white-space:normal">Agents: Claude Opus 5.5 and Gemini 4 Carbon. Design after Lei, Docherty &amp; Cooper (2024): label before seeing model output.</p>
      </div>
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
      <div><p class="lab">Shared errors</p><p class="num">99–100%</p><p class="what">model agreement; agreed but wrong on library OCR: 50 Butler, 75 Reeve</p></div>
    </div>
    <p class="punch">Two agents can agree on the same mistake: both read the same damaged OCR.</p>
    <div class="grid3">
      <div><p class="sub-h">A · Three texts: OCR decides F1</p>
        <figure><img src="fig/v5/f1_by_text.png" alt="Value F1 by text: library OCR 0.60 and 0.64, modern OCR 0.95 and 0.98, expert transcription 0.98 and 0.98, with 95% intervals"></figure></div>
      <div><p class="sub-h">B · Names intact predict F1</p>
        <figure><img src="fig/v5/names_vs_f1.png" alt="Value F1 against share of names intact after OCR, Spearman 0.95 Butler and 1.00 Reeve"></figure></div>
      <div><p class="sub-h">C · Linking 34 correctly read names</p>
        <figure><img src="fig/v5/link_recall.png" alt="Link recall: plain GBIF lookup 0.59, with context hint 0.62, LLM linker Haiku 0.76, Opus 0.91"></figure></div>
    </div>
    <div class="dq">
      <p class="sub-h" style="margin:0">D · Spot the fake: which is printed in 1849?</p>
      <div class="choices" style="margin:0"><div>A · Turritella brevisis</div><div>B · Turritella brevialis</div></div>
      <div class="flip" style="margin:0">B is printed; a modern OCR model wrote A. Nothing looks broken.</div>
    </div>
  </div>
</div>
<div class="box">
  <p class="act">04 · Protocol and Data</p>
  <div class="in">
    <p>Pre-registered · frozen before the test pages · deviations logged</p>
    <p>F1 per book, 95% page-bootstrap intervals; the two books are never pooled.</p>
    <p class="sub-h" style="margin-top:.25in">Data</p>
    <div class="dl">
      <div class="v">16</div><div class="d"><b>Test pages</b><span>Reeve 1849 shells · Butler 1907 birds</span></div>
      <div class="v">607</div><div class="d"><b>Hand-labelled mentions</b><span>before any model output</span></div>
      <div class="v">0.90</div><div class="d"><b>Labeller agreement</b><span>exact match, 5 pages</span></div>
    </div>
    <p class="sub-h" style="margin-top:auto;padding-top:.2in">Next: classical Chinese</p>
    <div class="bencao"><img src="fig/v2/bencao_chars.png" alt="陶弘景 as written in the manuscript, 弘 one stroke short"><span class="zh" style="font-size:40px;color:var(--accent)">→ 陶弘景</span></div>
    <p class="note" style="margin-top:.08in"><i>Bencao gangmu</i> 本草綱目 manuscript: the model writes the modern character, right for search, wrong for the edition.</p>
  </div>
</div>
</div>

<div class="row" id="r3">
<div class="box">
  <p class="act">05 · Proposed Framework</p>
  <div class="in">
    <h2>An evidence-aware scientific agent: a proposed workflow, informed by these results</h2>
    {framework_svg()}
  </div>
</div>
<div class="stack">
<div class="box">
  <p class="act">06 · Conclusion</p>
  <div class="in"><ul class="concl">
      <li><b>Finding.</b> Library OCR cost a third of the values; a plain database lookup lost 14 of 34 correctly read names. Extraction lost little on these pages (0.93–0.98).</li>
      <li><b>For agent builders.</b> Check that names survive OCR; let the model point and code write; test the database link on its own; agreement between models is not evidence.</li>
      <li><b>Next.</b> Reeve's names; the classical Chinese test pages. Materials papers are untested.</li>
    </ul></div>
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
