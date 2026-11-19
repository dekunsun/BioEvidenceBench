"""Merge Gloria's error-analysis tags into the case sheet and count them (PREREGISTRATION section 5).

    python src/summarise_error_tags.py

Reads the case sheets written by make_error_sheet.py and her tag files, archived unchanged in
results/error_analysis_test/received/ (one TSV per sheet, rows in sheet order, four columns:
OCR相关, 抽取或推理, 模糊或混合, 备注). Writes *_tagged.csv and SUMMARY.md. A case may carry
several tags, so tag counts can add up to more than the number of cases.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

from common import ROOT

DIR = ROOT / "results" / "error_analysis_test"
TAGS = ["OCR相关", "抽取或推理", "模糊或混合"]
SHEETS = {"gold_mentions": "2026-11-20_tags_gold_mentions_gloria.tsv",
          "extra_outputs": "2026-11-20_tags_extra_outputs_gloria.tsv"}


def read_tags(path: Path) -> pd.DataFrame:
    rows = [(line.rstrip("\n").split("\t") + [""] * 4)[:4]
            for line in path.read_text(encoding="utf-8").splitlines()]
    return pd.DataFrame(rows, columns=TAGS + ["备注"])


def merge(sheet: str) -> pd.DataFrame | None:
    tag_file = DIR / "received" / SHEETS[sheet]
    if not tag_file.exists():
        return None
    cases = pd.read_csv(DIR / f"{sheet}.csv", keep_default_na=False)
    tags = read_tags(tag_file)
    if len(tags) != len(cases):
        sys.exit(f"{tag_file.name}: {len(tags)} rows, the sheet has {len(cases)}")
    cases = cases.drop(columns=[c for c in TAGS + ["备注"] if c in cases.columns])
    out = pd.concat([cases, tags], axis=1)
    for t in TAGS:
        out[t] = out[t].str.strip().eq("是")
    untagged = out[~out[TAGS].any(axis=1)]
    if len(untagged):
        print(f"WARNING {sheet}: {len(untagged)} rows carry no tag")
    out.to_csv(DIR / f"{sheet}_tagged.csv", index=False)
    return out


def table(d: pd.DataFrame, by: list[str]) -> pd.DataFrame:
    g = d.groupby(by)
    t = pd.concat([g.size().rename("cases")] + [g[c].sum().rename(c) for c in TAGS], axis=1)
    combo = d[TAGS].apply(lambda r: "+".join(t for t, v in zip(TAGS, r) if v) or "(none)", axis=1)
    t["只有OCR相关"] = d.assign(c=combo).groupby(by).c.apply(lambda s: (s == "OCR相关").sum())
    return t.reset_index()


def main() -> None:
    lines = ["# Error analysis: Opus G1, test pages", "",
             "Tags by Gloria (2026-11-20); group A's OCR相关 was preset by its definition and spot-checked "
             "(DEVIATIONS.md). A case may carry several tags.", ""]
    for sheet in SHEETS:
        d = merge(sheet)
        if d is None:
            lines += [f"## {sheet}", "", f"Tags not received yet (`received/{SHEETS[sheet]}`).", ""]
            continue
        lines += [f"## {sheet} ({len(d)} cases)", "", "By book:", "",
                  table(d, ["book"]).to_markdown(index=False), "", "By book and field:", "",
                  table(d, ["book", "字段"]).to_markdown(index=False), "", "By group:", "",
                  table(d, ["分组"]).to_markdown(index=False), ""]
    (DIR / "SUMMARY.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
