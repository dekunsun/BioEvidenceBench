"""Inter-annotator agreement on the 5 double-labelled test pages (ANNOTATION_GUIDE section 4).

    python src/agreement.py --name independent \
        --a gold/received/2026-11-19_test_8992379_gloria.csv ... \
        --b gold/received/<date>_test_friend.csv

    python src/agreement.py --name working --a gold/gold_mentions_gloria_test.csv --b <friend file>

Two comparisons are meant to be run:
  independent  Gloria's files AS DELIVERED (before any adjudication or AI discussion; for 8992643
               her reconstructed independent version) against the friend's file as delivered.
               This is the agreement number that is reported.
  working      Gloria's adjudicated test gold against the friend's file. Its disagreement list is
               what Gloria adjudicates. Never reported as agreement (the gold has been adjudicated).

Unit: a mention = (page, start, end, field) in the expert transcription. Matching, per page:
  1. exact     same start, end and field
  2. overlap   same field, spans overlap (one-to-one, largest overlap first)
Only same-field pairs agree. What is left is listed as a disagreement:
  field_differs   the spans overlap but the fields differ
  only_a / only_b one labeller has a mention the other has not
  (a same-field overlap that is not exact is listed as `boundary`, though it counts as overlap
  agreement)
Agreement per field = 2 * matched / (n_a + n_b) (the F1 of one labeller against the other; it
is symmetric). Reported per book, per field, and for ALL_PRIMARY (every field but vernacular,
as in scoring). Rows with field `none` or adjudication `excluded` are not mentions. Rows without
offsets get them when the text occurs exactly once on the page; otherwise they are listed as
`unplaced` and left out until offsets are filled in (src/check_gold.py shows the positions).

Read-only: never writes a gold file. Output in results/agreement_<name>/.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from common import DATA, ROOT

PRIMARY = ["taxon", "person", "locality", "institution", "date"]
FIELDS = PRIMARY + ["vernacular"]
KEEP = ["page_id", "start", "end", "field", "text", "notes", "adjudication"]


def load_labels(paths: list[Path], pages: set[int] | None = None) -> tuple[pd.DataFrame, pd.DataFrame]:
    """(placed mentions, unplaced rows). Offsets are filled only where the text is unique."""
    d = pd.concat([pd.read_csv(p, dtype=str, keep_default_na=False).assign(source=p.name) for p in paths],
                  ignore_index=True)
    for c in KEEP:
        if c not in d.columns:
            d[c] = ""
    d["page_id"] = d.page_id.astype(int)
    if pages is not None:
        d = d[d.page_id.isin(pages)]
    d = d[(d.field.str.strip() != "none") & (d.adjudication.str.strip() != "excluded")].copy()
    starts, ends = [], []
    for r in d.itertuples():
        if str(r.start).strip() and str(r.end).strip():
            starts.append(int(float(r.start))); ends.append(int(float(r.end)))
            continue
        src = (DATA / "sample" / "expert" / f"{r.page_id}.txt").read_text(encoding="utf-8")
        hits = [i for i in range(len(src)) if r.text and src.startswith(r.text, i)]
        starts.append(hits[0] if len(hits) == 1 else -1)
        ends.append(hits[0] + len(r.text) if len(hits) == 1 else -1)
    d["start"], d["end"] = starts, ends
    return d[d.start >= 0].reset_index(drop=True), d[d.start < 0].reset_index(drop=True)


def _ov(a, b) -> int:
    return max(0, min(a["end"], b["end"]) - max(a["start"], b["start"]))


def match_page(a: list[dict], b: list[dict]) -> list[dict]:
    """One row per pair or leftover: kind in exact, boundary, field_differs, only_a, only_b."""
    out, used_a, used_b = [], set(), set()
    # 1. exact
    for i, x in enumerate(a):
        for j, y in enumerate(b):
            if j not in used_b and (x["start"], x["end"], x["field"]) == (y["start"], y["end"], y["field"]):
                out.append({"kind": "exact", "a": x, "b": y}); used_a.add(i); used_b.add(j)
                break
    # 2. same field, overlapping, largest overlap first; then 3. overlapping, other field
    for same_field in (True, False):
        cands = sorted(((_ov(x, y), i, j) for i, x in enumerate(a) for j, y in enumerate(b)
                        if i not in used_a and j not in used_b and _ov(x, y) > 0
                        and (x["field"] == y["field"]) == same_field), reverse=True)
        for _, i, j in cands:
            if i in used_a or j in used_b:
                continue
            out.append({"kind": "boundary" if same_field else "field_differs", "a": a[i], "b": b[j]})
            used_a.add(i); used_b.add(j)
    out += [{"kind": "only_a", "a": x, "b": None} for i, x in enumerate(a) if i not in used_a]
    out += [{"kind": "only_b", "a": None, "b": y} for j, y in enumerate(b) if j not in used_b]
    return out


def compare(a: pd.DataFrame, b: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for pid in sorted(set(a.page_id) | set(b.page_id)):
        pa = a[a.page_id == pid].to_dict("records")
        pb = b[b.page_id == pid].to_dict("records")
        for m in match_page(pa, pb):
            x, y = m["a"] or {}, m["b"] or {}
            rows.append({"page_id": pid, "kind": m["kind"],
                         "a_start": x.get("start", ""), "a_end": x.get("end", ""), "a_field": x.get("field", ""),
                         "a_text": x.get("text", ""), "a_notes": x.get("notes", ""),
                         "b_start": y.get("start", ""), "b_end": y.get("end", ""), "b_field": y.get("field", ""),
                         "b_text": y.get("text", ""), "b_notes": y.get("notes", "")})
    return pd.DataFrame(rows)


def summarise(pairs: pd.DataFrame, book_of: dict[int, str]) -> pd.DataFrame:
    p = pairs.assign(book=pairs.page_id.map(book_of))
    out = []
    for book, d in list(p.groupby("book")) + [("ALL_BOOKS", p)]:
        for field in FIELDS + ["ALL_PRIMARY"]:
            fs = PRIMARY if field == "ALL_PRIMARY" else [field]
            in_a, in_b = d.a_field.isin(fs), d.b_field.isin(fs)
            n_a, n_b = int(in_a.sum()), int(in_b.sum())
            same = d.kind.isin(["exact", "boundary"]) & in_a      # same-field pairs: a_field == b_field
            exact = int((same & (d.kind == "exact")).sum())
            overlap = int(same.sum())
            out.append({"book": book, "field": field, "pages": d.page_id.nunique(), "n_a": n_a, "n_b": n_b,
                        "exact": exact, "overlap": overlap,
                        "agreement_exact": round(2 * exact / (n_a + n_b), 3) if n_a + n_b else None,
                        "agreement_overlap": round(2 * overlap / (n_a + n_b), 3) if n_a + n_b else None,
                        "field_differs": int((d.kind == "field_differs").where(in_a | in_b, False).sum()),
                        "only_a": int(((d.kind == "only_a") & in_a).sum()),
                        "only_b": int(((d.kind == "only_b") & in_b).sum())})
    return pd.DataFrame(out)


def main() -> None:
    from analysis import sha256_file
    ap = argparse.ArgumentParser()
    ap.add_argument("--name", required=True)
    ap.add_argument("--a", nargs="+", required=True, help="labeller A (Gloria) file(s)")
    ap.add_argument("--b", nargs="+", required=True, help="labeller B (second labeller) file(s)")
    a_args = ap.parse_args()
    b_lab, b_unplaced = load_labels([Path(x) for x in a_args.b])
    pages = set(b_lab.page_id) | set(b_unplaced.page_id)
    a_lab, a_unplaced = load_labels([Path(x) for x in a_args.a], pages)
    split = pd.read_csv(DATA / "sample_split.csv")
    book_of = dict(zip(split.PageID.astype(int), split.book))
    pairs = compare(a_lab, b_lab)
    summary = summarise(pairs, book_of)

    out = ROOT / "results" / f"agreement_{a_args.name}"
    out.mkdir(parents=True, exist_ok=True)
    summary.to_csv(out / "agreement.csv", index=False)
    dis = pairs[pairs.kind != "exact"].assign(decision="", decision_note="")
    dis.to_csv(out / "disagreements.csv", index=False)
    unplaced = pd.concat([a_unplaced.assign(labeller="a"), b_unplaced.assign(labeller="b")])
    unplaced.to_csv(out / "unplaced.csv", index=False)
    (out / "config.json").write_text(json.dumps({
        "written_at": datetime.now(timezone.utc).isoformat(timespec="seconds"), "pages": sorted(pages),
        "a": {p: sha256_file(p) for p in a_args.a}, "b": {p: sha256_file(p) for p in a_args.b},
        "unit": "mention (page, start, end, field) in the expert transcription",
        "agreement": "2 * matched / (n_a + n_b); exact = same span and field, overlap = same field, spans overlap",
        "left_out": "field none, adjudication excluded, rows without unique offsets (unplaced.csv)"},
        indent=2), encoding="utf-8")
    show = summary[summary.n_a + summary.n_b > 0]
    lines = [f"# Agreement: {a_args.name}", "",
             "A = Gloria, B = second labeller. Agreement = 2 × matched / (n_A + n_B).", "",
             show.to_markdown(index=False), "",
             f"Disagreements to look at: {len(dis)} (`disagreements.csv`; kinds: "
             + ", ".join(f"{k} {v}" for k, v in dis.kind.value_counts().items()) + ").",
             f"Rows left out for lack of unique offsets: {len(unplaced)} (`unplaced.csv`).", ""]
    (out / "REPORT.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
