"""Tests for the agreement script. Made-up spans only; no gold file is read."""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import agreement as ag  # noqa: E402


def m(start, end, field, text="x", page=1):
    return {"page_id": page, "start": start, "end": end, "field": field, "text": text, "notes": ""}


def test_match_page_kinds():
    a = [m(0, 5, "taxon"), m(10, 20, "locality"), m(30, 35, "person"), m(50, 55, "date")]
    b = [m(0, 5, "taxon"), m(10, 15, "locality"), m(30, 35, "institution"), m(70, 75, "taxon")]
    kinds = sorted(x["kind"] for x in ag.match_page(a, b))
    assert kinds == ["boundary", "exact", "field_differs", "only_a", "only_b"]


def test_same_field_overlap_is_preferred_over_another_field():
    a = [m(0, 10, "locality")]
    b = [m(0, 10, "person"), m(2, 8, "locality")]
    got = {x["kind"] for x in ag.match_page(a, b)}
    assert got == {"boundary", "only_b"}


def test_summary_counts_and_agreement():
    a = pd.DataFrame([m(0, 5, "taxon"), m(10, 20, "locality"), m(30, 35, "person", page=2)])
    b = pd.DataFrame([m(0, 5, "taxon"), m(10, 15, "locality"), m(30, 35, "person", page=2),
                      m(40, 45, "vernacular", page=2)])
    s = ag.summarise(ag.compare(a, b), {1: "Butler", 2: "Reeve"}).set_index(["book", "field"])
    allp = s.loc[("ALL_BOOKS", "ALL_PRIMARY")]
    assert (allp.n_a, allp.n_b, allp.exact, allp.overlap) == (3, 3, 2, 3)
    assert allp.agreement_exact == round(4 / 6, 3) and allp.agreement_overlap == 1.0
    assert s.loc[("Reeve", "vernacular")].only_b == 1          # vernacular is kept out of ALL_PRIMARY
    assert s.loc[("Butler", "locality")].agreement_exact == 0.0


def test_load_labels_drops_none_and_excluded_and_fills_unique_offsets(tmp_path):
    # a dev page; the string is just some text that occurs once, not a label
    src = (ag.DATA / "sample" / "expert" / "8992582.txt").read_text(encoding="utf-8")
    word = next(w for w in src.split() if len(w) > 6 and src.count(w) == 1)
    twice = next(w for w in src.split() if len(w) > 3 and src.count(w) == 2)
    p = tmp_path / "a.csv"
    pd.DataFrame([{"page_id": 8992582, "start": "", "end": "", "field": "taxon", "text": word},
                  {"page_id": 8992582, "start": "", "end": "", "field": "taxon", "text": twice},
                  {"page_id": 8992582, "start": "", "end": "", "field": "none", "text": ""},
                  {"page_id": 8992582, "start": "0", "end": "3", "field": "taxon", "text": "xyz",
                   "adjudication": "excluded"}]).to_csv(p, index=False)
    placed, unplaced = ag.load_labels([p])
    assert placed.text.tolist() == [word] and src[placed.start[0]:placed.end[0]] == word
    assert unplaced.text.tolist() == [twice]
