"""Check a gold mention file. Read-only: it never edits the gold file.

For every row it checks that the field name is valid and that
text == expert_text[start:end]. For rows where only `text` is filled, it
looks the text up on the page. If it occurs once, it suggests the offsets.
If it occurs more than once, it lists every position so the labeller can
choose one.

Results go to a separate file next to the input:
gold/<name>.checked.csv, with columns status, suggested_start and
suggested_end added. Copy the suggested offsets into your own file if they
are right.

Run:  python src/check_gold.py gold/gold_mentions_gloria.csv
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

from common import DATA, TEXT

FIELDS = {"taxon", "vernacular", "person", "locality", "institution", "date", "none"}
ADJUDICATION = {"", "adjudicated", "ambiguous", "excluded"}


def check(path: Path) -> pd.DataFrame:
    g = pd.read_csv(path, dtype={"text": str, "notes": str}, keep_default_na=False)
    out = []
    for r in g.to_dict("records"):
        status, s_start, s_end = "ok", "", ""
        page = DATA / "sample" / "expert" / f"{r['page_id']}.txt"   # committed sample pages
        if not page.exists():
            page = TEXT / "expert" / f"{r['page_id']}.txt"           # any page, after load_gt.py
        if r["field"] not in FIELDS:
            status = f"bad field '{r['field']}'"
        elif str(r.get("adjudication", "")).strip() not in ADJUDICATION:
            status = f"bad adjudication '{r['adjudication']}' (use adjudicated, ambiguous or excluded)"
        elif "UNCLEAR" in str(r.get("notes", "")) and not str(r.get("adjudication", "")).strip():
            status = "ok (UNCLEAR: needs adjudication before scoring)"
        elif r["field"] == "none":
            status = "ok (page has no target entities)"
        elif not page.exists():
            status = "expert text missing: run src/load_gt.py"
        else:
            src = page.read_text(encoding="utf-8")
            if str(r["start"]).strip() and str(r["end"]).strip():
                a, b = int(r["start"]), int(r["end"])
                if not (0 <= a < b <= len(src)):
                    status = f"offsets out of range (page has {len(src)} chars)"
                elif src[a:b] != r["text"]:
                    status = f"MISMATCH: page[{a}:{b}] is {src[a:b]!r}"
            else:
                hits, i = [], src.find(r["text"])
                while i != -1 and r["text"]:
                    hits.append(i)
                    i = src.find(r["text"], i + 1)
                if len(hits) == 1:
                    status, s_start, s_end = "offsets suggested", hits[0], hits[0] + len(r["text"])
                elif not hits:
                    status = "text not found on page (check spelling, ligatures, line breaks)"
                else:
                    status = f"text occurs {len(hits)} times at starts {hits}: pick one"
        out.append(r | {"status": status, "suggested_start": s_start, "suggested_end": s_end})
    return pd.DataFrame(out)


if __name__ == "__main__":
    for arg in sys.argv[1:]:
        p = Path(arg)
        res = check(p)
        dest = p.with_name(p.stem + ".checked.csv")
        res.to_csv(dest, index=False)
        bad = res[~res.status.str.startswith("ok")]
        print(f"{p}: {len(res)} rows, {len(bad)} need attention -> {dest}")
        if len(bad):
            print(bad[["page_id", "field", "text", "status"]].to_string(index=False))
