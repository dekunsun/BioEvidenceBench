"""本草綱目 case: turn inline labels into gold rows (a typing aid; the labeller decides every label).

The labeller copies each reference line and wraps every mention in brackets with a field code:

    [宻甘]ta[别録]w[𢎞景]p{弘景}[沈香]t?

    t taxon · p person · l locality · w cited_work · s substance
    a after the code = qualifier alias (ta)
    {…} after the code = restored_form (normalization_type filled from data/bencao/variant_table.csv
        when every changed character is in the table; otherwise left empty for the labeller)
    ? after the code (or after {…}) = UNCLEAR (goes to notes)

Nothing is guessed: if the line with the brackets removed is not exactly the reference line, the script
stops and names the line, so a slip while typing can never change the source text.

    python src/bencao_inline_labels.py <workbook.xlsx> <half_leaf> <out.csv>
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "bencao"
FIELDS = {"t": "taxon", "p": "person", "l": "locality", "w": "cited_work", "s": "substance"}
TOKEN = re.compile(r"\[([^\[\]]+)\]([tplws])(a?)(\{[^{}]*\})?(\??)")


def parse_line(marked: str) -> tuple[str, list[dict]]:
    plain, rows, pos = [], [], 0
    for m in TOKEN.finditer(marked):
        plain.append(marked[pos:m.start()])
        rows.append({"text": m.group(1), "field": FIELDS[m.group(2)], "qualifier": "alias" if m.group(3) else "",
                     "restored_form": (m.group(4) or "")[1:-1], "unclear": bool(m.group(5))})
        plain.append(m.group(1))
        pos = m.end()
    plain.append(marked[pos:])
    text = "".join(plain)
    if "[" in text or "]" in text:
        raise ValueError(f"unmatched bracket or unknown field code in: {marked}")
    return text, rows


def norm_type(form: str, restored: str) -> str:
    if not restored or len(form) != len(restored):
        return ""
    table = pd.read_csv(DATA / "variant_table.csv")
    kinds = set()
    for a, b in zip(form, restored):
        if a == b:
            continue
        hit = table[(table.form == a) & (table.standard == b)]
        if hit.empty:
            return ""
        kinds.add(hit.type.iloc[0])
    return kinds.pop() if len(kinds) == 1 else ""


def convert(marked_lines: dict[int, str], half_leaf: str) -> pd.DataFrame:
    ref = (DATA / "verified_plain" / f"{half_leaf}.txt").read_text(encoding="utf-8").splitlines()
    out, offset = [], 0
    starts = [sum(len(x) + 1 for x in ref[:k]) for k in range(len(ref))]   # offsets in the file, newline = 1
    for line, marked in sorted(marked_lines.items()):
        text, rows = parse_line(marked)
        if text != ref[line - 1]:
            raise ValueError(f"line {line}: text with the brackets removed differs from the reference line")
        cursor = 0
        for r in rows:
            k = text.index(r["text"], cursor)            # reading order: next occurrence after the previous mention
            cursor = k + len(r["text"])
            out.append({"page_id": half_leaf, "line": line, "start": starts[line - 1] + k,
                        "end": starts[line - 1] + k + len(r["text"]), "field": r["field"], "text": r["text"],
                        "scan_text": "", "restored_form": r["restored_form"],
                        "normalization_type": norm_type(r["text"], r["restored_form"]),
                        "restoration_evidence": "", "qualifier": r["qualifier"],
                        "notes": "UNCLEAR: (inline ?)" if r["unclear"] else ""})
    return pd.DataFrame(out)


if __name__ == "__main__":
    wb, pb, dest = sys.argv[1:4]
    sh = pd.read_excel(wb, sheet_name="行内标注")
    sh = sh.rename(columns={sh.columns[2]: "marked"})
    sh = sh[pd.to_numeric(sh.line, errors="coerce").notna()]          # the worked example rows have no line number
    marked = {int(r.line): str(r.marked) for r in sh.itertuples() if isinstance(r.marked, str) and "[" in r.marked}
    convert(marked, pb).to_csv(dest, index=False)
    print(dest)
