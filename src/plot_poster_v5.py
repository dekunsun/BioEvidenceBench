"""Charts for the A1 poster, version 5 (poster/poster.html, LiveLab layout): the three charts of
src/plot_poster_v3.py redrawn at the LiveLab poster's chart size and type (Liberation Sans, as Arial /
Helvetica in the poster's CSS), so every label prints at the poster's body size (26 px).
Each chart is shown about 700 px wide; at 6.4 in x 200 dpi that is a 0.55 scale, so 17 pt -> 26 px.

    python src/plot_poster_v5.py   -> poster/fig/v5/f1_by_text.png, names_vs_f1.png, link_recall.png
"""
from __future__ import annotations

import matplotlib.pyplot as plt

import plot_poster_v3 as v3

v3.OUT = v3.ROOT / "poster" / "fig" / "v5"
v3.FS = 17.0
v3.W, v3.H = 6.4, 2.8
v3.INK, v3.GREY = "#15201c", "#4d5a55"
plt.rcParams.update({"font.family": ["Liberation Sans", "DejaVu Sans"], "font.size": v3.FS,
                     "axes.edgecolor": v3.GREY, "axes.labelcolor": v3.INK, "xtick.color": v3.INK,
                     "ytick.color": v3.INK})

if __name__ == "__main__":
    v3.OUT.mkdir(parents=True, exist_ok=True)
    v3.f1_by_text()
    v3.names_vs_f1()
    v3.link_recall()
    print("written", v3.OUT)
