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
#r2{grid-template-columns:0.70fr 0.30fr}
#r3{grid-template-columns:0.60fr 0.40fr}
main{gap:0.25in !important}
main>.row{flex:1 1 auto}  /* share any spare page height between the rows */
.box>.in{padding:0.34in 0.34in 0.30in}
h1{font-size:72px}
.brand{gap:.3in}
.brand .penn,.brand .cas{width:2.75in !important;height:auto;display:block}  /* same width, so the two logos share left and right edges */
.brand{justify-items:center}
h1{font-size:80px}
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
    W, H = 1419, 722
    p = [DEFS]
    # left: the model writes the record
    p.append(f'<rect x="0" y="0" width="690" height="{H - 6}" rx="18" fill="#f5f6f7" stroke="#c4cbd0" stroke-width="2"/>')
    p.append(f'<text x="25" y="46" font-size="{FS}" font-weight="700" fill="{SOFT}">Model writes the record</text>')
    L = [(76, 60, [("Scanned page", 600, INK)]),
         (196, 114, [("Model", 600, INK), ("reads the OCR,", 400, SOFT), ("writes the value", 400, SOFT)]),
         (370, 114, [("Record", 600, INK), ("<tspan font-style='italic'>Turritella</tspan>", 400, SOFT),
                     ("<tspan font-style='italic'>brevisis</tspan>", 400, SOFT)]),
         (550, 60, [("Researcher trusts it", 600, INK)])]
    prev = None
    for y, h, lines in L:
        p.append(box(25, y, 316, h, lines))
        if prev:
            p.append(arrow(f"M183 {prev} V{y - 5}"))
        prev = y + h
    for i, t in enumerate(["1 in 12 repairs", "is wrong; fluent", "OCR errors pass", "and look right"]):
        p.append(f'<text x="366" y="{232 + i * 32}" font-size="{FS}" font-weight="400" fill="{SOFT}">{t}</text>')
    # right: code owns the text
    x0 = 723
    p.append(f'<rect x="{x0}" y="0" width="690" height="{H - 6}" rx="18" fill="#eef1f7" stroke="{NAVY}" stroke-width="2"/>')
    p.append(f'<text x="{x0 + 25}" y="46" font-size="{FS}" font-weight="700" fill="{NAVY}">Code owns the text</text>')
    bx, bw = 748, 330
    R = [(76, 60, [("Scanned page", 600, INK)]),
         (166, 92, [("OCR text", 600, INK), ("F1 0.60 → 0.95", 400, RED)]),
         (290, 124, [("Code checks quote,", 600, NAVY), ("slices the value", 600, NAVY), ("0 recall lost", 400, SOFT)]),
         (446, 92, [("Database lookup", 600, INK), ("14 of 34 lost", 400, RED)]),
         (570, 124, [("Person reviews", 600, INK), ("50 of 75 errors made", 400, RED), ("by both models", 400, RED)])]
    prev = None
    for y, h, lines in R:
        p.append(box(bx, y, bw, h, lines, stroke=RULE))
        if prev:
            p.append(arrow(f"M{bx + bw / 2} {prev} V{y - 5}"))
        prev = y + h
    # the model on the side, with a robot
    mx, my, mw, mh = 1110, 104, 286, 256
    p.append(f'<rect x="{mx}" y="{my}" width="{mw}" height="{mh}" rx="12" fill="#fff" stroke="{SOFT}" stroke-width="2" stroke-dasharray="9 7"/>')
    p.append(robot(mx + mw / 2, my + 16, 0.95))
    for i, (t, wt, col) in enumerate([("Model", 600, INK), ("finds mentions,", 400, SOFT),
                                      ("quotes the line", 400, SOFT), ("F1 0.93–0.98", 400, NAVY)]):
        p.append(f'<text x="{mx + mw / 2}" y="{my + 136 + i * 32}" text-anchor="middle" font-size="{FS}" font-weight="{wt}" fill="{col}">{t}</text>')
    p.append(arrow(f"M{bx + bw} 212 H{mx - 5}", dash=True))
    p.append(arrow(f"M{mx + 60} {my + mh} V384 H{bx + bw + 5}", dash=True))
    for i, t in enumerate(["never rewrites", "the source text"]):
        p.append(f'<text x="{mx + mw / 2 + 20}" y="{456 + i * 32}" text-anchor="middle" font-size="{FS}" font-weight="600" fill="{NAVY}">{t}</text>')
    return (f'<svg viewBox="-3 -3 {W} {H}" width="100%" role="img" aria-label="Two designs. Model writes the '
            f'record: scanned page, model reads the OCR and writes the value, record, researcher trusts it; 1 in '
            f'12 repairs is wrong, and fluent OCR errors pass and look right. Code owns the text: scanned page, OCR text '
            f'(F1 0.60 to 0.95 by OCR), code checks the quote and slices the value (0 recall lost), database '
            f'lookup (14 of 34 names lost), person reviews (50 of 75 errors made by both models); the model, '
            f'drawn as a robot, finds mentions and quotes the line, F1 0.93 to 0.98, and never rewrites the '
            f'source text.">' + "\n".join(p) + "</svg>")


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
    <div class="grid2">
      <div><p class="sub-h">A · Same pages, three texts: OCR decides F1</p>
        <figure><img src="fig/v5/f1_by_text.png" alt="Value F1 by text: library OCR 0.60 and 0.64, modern OCR 0.95 and 0.98, expert transcription 0.98 and 0.98, with 95% intervals"></figure></div>
      <div><p class="sub-h">B · 24 OCR versions: names intact predict F1</p>
        <figure><img src="fig/v5/names_vs_f1.png" alt="Value F1 against share of names intact after OCR, Spearman 0.95 Butler and 1.00 Reeve"></figure></div>
      <div><p class="sub-h">C · Linking 34 correctly read names</p>
        <figure><img src="fig/v5/link_recall.png" alt="Link recall: plain GBIF lookup 0.59, with context hint 0.62, LLM linker Haiku 0.76, Opus 0.91"></figure></div>
      <div><p class="sub-h">D · Spot the fake: which is printed in 1849?</p>
        <div class="choices"><div>A · Turritella brevisis</div><div>B · Turritella brevialis</div></div>
        <div class="flip">B is printed; a modern OCR model wrote A. Nothing looks broken.</div>
        <p style="margin:0">Read right, linked wrong: <i>Motacilla beema</i> (1907) finds only the genus; today it is <i>Motacilla flava</i>.</p></div>
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
    <h2>Code owns the text; the model points and quotes</h2>
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
