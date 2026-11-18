import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from baseline_rules import find_regex  # noqa: E402

TEXT = "PFEIFFER, Pro. Zool. Soc., 1846, p. 112.\n\nHab. Central America?\nshot by Mr. J. Smith on 3rd May, 1890 (Mus. Cuming.)"


def spans(field):
    return [TEXT[m["start"]:m["end"]] for m in find_regex(TEXT) if m["field"] == field]


def test_rules_find_each_field_once():
    assert sorted(spans("person")) == ["J. Smith", "PFEIFFER"]
    assert spans("locality") == ["Central America"]
    assert "3rd May, 1890" in spans("date") and "1846" in spans("date")
    assert spans("institution") == ["Mus. Cuming"]


def test_no_overlapping_duplicates_within_a_field():
    d = spans("date")
    assert "1890" not in d  # covered by the longer "3rd May, 1890"
