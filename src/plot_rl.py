"""Figure for docs/rl_results.md: locked-test repair rate by condition, and what GRPO did in training.

    python src/plot_rl.py            # -> docs/figures/rl_results.png

Left: damaged-word repair rate on the 500 locked in-book test lines (pass@1 over 4 answers), one dot
per seed, bar = mean of seeds (`rl/training/results_test/metrics.csv`). Right: share of GRPO training
answers that return the OCR unchanged, per 25-step bin (every completion was logged). Colours are
the conditions in both panels; the same numbers are in the tables of docs/rl_results.md.
"""
from __future__ import annotations

import gzip
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
RUNS = ROOT / "rl" / "training" / "runs"
SURFACE, INK, MUTED, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e4e3df"
COL = {"Base": "#8a8985", "SFT": "#2a78d6", "GRPO": "#eb6834", "SFT→GRPO": "#1baf7a", "GRPO, 1 − CER": "#eda100"}


def main() -> None:
    m = pd.read_csv(ROOT / "rl" / "training" / "results_test" / "metrics.csv")
    m = m[m.set == "p0_test_inbook"].set_index("model").repair_rate
    groups = [("Copy", ["copy"]), ("Base", ["base"]), ("SFT", ["sft_s1", "sft_s2"]),
              ("GRPO", ["grpo_s1", "grpo_s2"]), ("SFT→GRPO", ["sft_grpo_s1", "sft_grpo_s2"]),
              ("GRPO, 1 − CER", ["grpo_cer_s1"])]

    runs = {"GRPO": ["20261121-1832_p0s1/grpo_s1", "20261121-1832_p0s2/grpo_s2"],
            "SFT→GRPO": ["20261121-2007_sft600s1/sft_grpo_s1", "20261121-2008_sft600s2/sft_grpo_s2"],
            "GRPO, 1 − CER": ["20261121-2022_p1cer/grpo_cer_s1"]}

    fig, (a, b) = plt.subplots(1, 2, figsize=(12, 4.6), dpi=200, facecolor=SURFACE,
                               gridspec_kw={"width_ratios": [1.05, 1]})
    for ax in (a, b):
        ax.set_facecolor(SURFACE)
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
        for s in ("left", "bottom"):
            ax.spines[s].set_color(GRID)
        ax.tick_params(colors=MUTED, labelsize=9.5)
        ax.grid(axis="y", color=GRID, lw=0.8)
        ax.set_axisbelow(True)

    for i, (name, labels) in enumerate(groups):
        vals = [m[x] for x in labels]
        mean = sum(vals) / len(vals)
        c = COL.get(name, MUTED)
        a.bar(i, mean, width=0.6, color=c, alpha=0.9 if name != "Copy" else 0.0, edgecolor=c, linewidth=1.5)
        a.scatter([i] * len(vals), vals, s=36, color=INK, zorder=3, edgecolors=SURFACE, linewidths=1.5)
        a.text(i, max(vals) + 0.015, f"{mean:.2f}" if name != "Copy" else "0", ha="center", va="bottom",
               fontsize=10, color=INK)
    a.set_xticks(range(len(groups)), [g[0].replace("GRPO, 1 − CER", "GRPO\n1 − CER").replace("SFT→GRPO", "SFT\n→ GRPO")
                                      for g in groups], fontsize=9.5, color=INK)
    a.set_ylim(0, 0.5)
    a.set_ylabel("damaged words repaired", fontsize=10, color=MUTED)
    a.set_title("Locked in-book test: SFT repairs, GRPO does not\n(500 lines; dots = seeds, bar = mean)",
                loc="left", fontsize=12, color=INK, pad=10)

    for cond, paths in runs.items():
        for k, p in enumerate(paths):
            r = pd.read_json(gzip.open(RUNS / f"{p}_completions.jsonl.gz"), lines=True)
            s = r.groupby(r.step // 25 * 25)["copy"].mean()
            b.plot(s.index + 12.5, s.values, color=COL[cond], lw=2, ls="-" if k == 0 else (0, (4, 2)),
                   label=f"{cond}, seed {k + 1}" if len(paths) > 1 else f"{cond}, seed 1")
        b.text(s.index[-1] + 18, s.values[-1], cond, fontsize=9.5, color=INK, va="center")
    b.set_xlim(0, 345)
    b.set_ylim(0, 1)
    b.set_xlabel("GRPO step", fontsize=10, color=MUTED)
    b.set_ylabel("answers that copy the OCR unchanged", fontsize=10, color=MUTED)
    b.set_title("In training, GRPO from the base model learns to copy\n(share per 25 steps; SFT→GRPO stays near 17%)",
                loc="left", fontsize=12, color=INK, pad=10)
    b.legend(loc="center right", bbox_to_anchor=(1.0, 0.42), frameon=False, fontsize=8.5, labelcolor=INK)
    fig.tight_layout()
    out = ROOT / "docs" / "figures" / "rl_results.png"
    fig.savefig(out, facecolor=SURFACE)
    print(out)


if __name__ == "__main__":
    main()
