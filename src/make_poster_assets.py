"""Image crops for the A1 poster (poster/poster.html), cut from the real scans at full resolution so they
print sharp. Text on the poster is HTML; only the scans are images.

    python src/make_poster_assets.py   -> poster/fig/v2/*.png

Scans: Reeve 1849 and Butler 1907 pages from finebooks/bhl-impact-gt (CC BY 3.0); Reeve plate XVII from
Internet Archive (public domain); 本草綱目 half-leaf 036-1b from CADAL via Internet Archive (public domain).
"""
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
IMG = ROOT / "data" / "cache" / "images"
OUT = ROOT / "poster" / "fig" / "v2"
RED, TEAL = (178, 59, 59), (31, 134, 131)


def page(pid: str) -> Image.Image:
    return Image.open(IMG / f"{pid}.webp").convert("RGB")


def boxed(im: Image.Image, crop, box, colour=RED, width=6) -> Image.Image:
    """Crop with a rounded box drawn round `box` (page coordinates)."""
    c = im.crop(crop).copy()
    d = ImageDraw.Draw(c)
    x0, y0, x1, y1 = box[0] - crop[0], box[1] - crop[1], box[2] - crop[0], box[3] - crop[1]
    d.rounded_rectangle((x0 - 10, y0 - 8, x1 + 10, y1 + 8), radius=10, outline=colour, width=width)
    return c


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    # hook: BULIMUS CHILENSIS on Reeve 8966790, with the lines around it
    boxed(page("8966790"), (300, 520, 1270, 760), (388, 608, 760, 652)).save(OUT / "hook_scan.png")
    Image.open(ROOT / "docs/assets/overview/reeve_plate17_fig102.png").save(OUT / "hook_shell.png")
    # quiz: Turritella brevialis on Reeve 8967281 (cut without the box, so the answer is not given away)
    page("8967281").crop((1225, 600, 2160, 745)).save(OUT / "quiz_scan.png")
    # link: Sykes' Wagtail account on Butler 8992647, name boxed
    boxed(page("8992647"), (600, 1290, 1760, 1530), (900, 1455, 1262, 1512)).save(OUT / "link_page.png")
    # read station: legacy OCR damage, the same BULIMUS line, small
    page("8966790").crop((380, 600, 770, 660)).save(OUT / "read_name.png")
    # gallery: the pages the agent had to read
    for name, im in (("gallery_reeve.png", page("8967281")), ("gallery_butler.png", page("8992647")),
                     ("gallery_plate.png", Image.open(ROOT / "docs/assets/overview/reeve_plate17.jpg").convert("RGB"))):
        im.thumbnail((900, 1200)); im.save(OUT / name)
    # 本草綱目 036-1b: whole half-leaf with 陶𢎞景 boxed, and the three characters side by side
    bc = Image.open(ROOT / "results/bencao_pilot/pages/036-1b.jpg").convert("RGB")
    full = bc.copy(); d = ImageDraw.Draw(full)
    d.rounded_rectangle((1524, 1962, 1634, 2238), radius=10, outline=RED, width=10)
    full.thumbnail((900, 1300)); full.save(OUT / "bencao_page.png")
    chars = [(1538, 1972, 1620, 2058), (1538, 2056, 1620, 2142), (1538, 2140, 1620, 2228)]
    strip = Image.new("RGB", (sum(c[2] - c[0] for c in chars) + 40, max(c[3] - c[1] for c in chars)), "white")
    x = 0
    for c in chars:
        strip.paste(bc.crop(c), (x, 0)); x += c[2] - c[0] + 20
    strip.save(OUT / "bencao_chars.png")
    print(sorted(p.name for p in OUT.iterdir()))


if __name__ == "__main__":
    main()
