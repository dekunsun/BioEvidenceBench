"""Build the web and PDF versions of the preprint from its Markdown source.

    python src/build_preprint.py          # -> docs/preprint/preprint.html and preprint.pdf
    python src/build_preprint.py rl       # -> docs/rl_report/rl_report.html and rl_report.pdf

docs/preprint.md (and docs/rl_results.md for the RL technical report) is the only source: edit it,
never the HTML. The page uses the layout of the
LiveLab preprint (github.com/dekunsun/livelab/docs/preprint): Source Serif, a centred title block,
numbered figures with captions, booktabs-style tables, a reference list; docs/preprint/preprint.css
is that stylesheet. The PDF is printed from the HTML with headless Chromium (A4).
"""
from __future__ import annotations

import re
import subprocess

import markdown

from common import ROOT

SRC = ROOT / "docs" / "preprint.md"
OUT = ROOT / "docs" / "preprint"
REPO = "https://github.com/dekunsun/BioEvidenceBench"


def fix_links(html: str) -> str:
    """The Markdown sits in docs/, the HTML in docs/preprint/: relative links move one level down."""
    def rel(m):
        attr, url = m.group(1), m.group(2)
        if re.match(r"(https?:|mailto:|#|\.\./\.\./)", url):
            return m.group(0)
        return f'{attr}="../{url}"'
    return re.sub(r'(href|src)="([^"]+)"', rel, html)


def figures(html: str) -> str:
    """<p><img></p> followed by an italic caption paragraph becomes <figure> + <figcaption>."""
    pat = re.compile(r'<p><img alt="([^"]*)" src="([^"]+)" ?/?></p>\s*<p><em>(Figure \d+\.)(.*?)</em></p>', re.S)
    return pat.sub(lambda m: f'<figure class="wide"><img src="{m.group(2)}" alt="{m.group(1)}">'
                             f'<figcaption><b>{m.group(3)}</b>{m.group(4)}</figcaption></figure>', html)


def tables(html: str) -> str:
    html = html.replace("<table>", '<div class="tablewrap"><table>').replace("</table>", "</table></div>")
    # numbers right-aligned, as in the LiveLab tables
    return re.sub(r"<td>([−+\-]?[\d.,/ \[\]−–]+%?)</td>", r'<td class="n">\1</td>', html)


TARGETS = {
    "preprint": dict(src=SRC, out=OUT, name="preprint", start="## Abstract",
                     page_title="BioEvidenceBench: Where Is Trustworthy Data Lost?",
                     note="Results marked <b>[pre-registered]</b> come from a run frozen before the test pages "
                          "were processed; results marked <b>[exploratory]</b> were designed after the test "
                          "outputs were unsealed."),
    "rl": dict(src=ROOT / "docs" / "rl_results.md", out=ROOT / "docs" / "rl_report", name="rl_report",
               start="<p align", page_title="BioEvidenceBench RL: Repairing Historical OCR",
               title="Teaching a small model to repair historical OCR: supervised fine-tuning, GRPO and a reward audit",
               note="Technical report on the training study of BioEvidenceBench (module 7). The locked test "
                    "was pre-registered and run once; the pipeline test in section 14 is exploratory."),
}


def main(target: str = "preprint") -> None:
    cfg = TARGETS[target]
    src, out, name = cfg["src"], cfg["out"], cfg["name"]
    md = src.read_text(encoding="utf-8")
    # title block: first heading, author line, status line; the rest is the body
    title = cfg.get("title") or re.search(r"^# (.+)$", md, re.M).group(1)
    body = md[md.index(cfg["start"]):]
    html = markdown.markdown(body, extensions=["tables", "sane_lists"])
    html = figures(fix_links(html))
    html = tables(html)
    # references: the numbered list after the References heading
    html = re.sub(r'(<h2>References</h2>\s*)<ol>', r'\1<ol class="refs">', html)
    html = html.replace("<h2>Abstract</h2>\n<p>", '<h2>Abstract</h2>\n<p class="abstract">', 1)
    css = (OUT / "preprint.css").read_text(encoding="utf-8")         # one stylesheet for both
    css += "\n  .refs { list-style: decimal; padding-left: 1.6rem; }\n  .refs li { padding-left: 0; text-indent: 0; }\n  hr { display: none; }\n"
    page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{cfg["page_title"]}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Source+Serif+4:ital,opsz,wght@0,8..60,400;0,8..60,600;0,8..60,700;1,8..60,400&display=swap">
<style>{css}</style>
</head>
<body>

<header>
  <h1>{title}</h1>
  <p class="authors">Dekun Sun</p>
  <p class="affil">University of Pennsylvania · <a href="https://ai4s.fyi">ai4s.fyi</a></p>
  <p class="date">November 2026 · preprint draft, work in progress, not peer reviewed · <a href="{REPO}">github.com/dekunsun/BioEvidenceBench</a> · <a href="{name}.pdf">PDF</a></p>
  <p class="date">{cfg["note"]}</p>
</header>

{html}

</body>
</html>
"""
    out.mkdir(parents=True, exist_ok=True)
    (out / f"{name}.html").write_text(page, encoding="utf-8")
    subprocess.run(["node", "-e", """
const {chromium}=require('playwright');
(async()=>{const b=await chromium.launch();const p=await b.newPage();
await p.goto('file://'+process.argv[1]);await p.waitForTimeout(2500);
await p.pdf({path:process.argv[2],format:'A4',printBackground:false,preferCSSPageSize:true});
await b.close();})();""", str(out / f"{name}.html"), str(out / f"{name}.pdf")], check=True)
    print("wrote", out / f"{name}.html", f"and {name}.pdf")


if __name__ == "__main__":
    import sys
    main(sys.argv[1] if len(sys.argv) > 1 else "preprint")
