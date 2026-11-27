"""Tests for src/anchor_boxes.py: local quote anchors on line boxes."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from anchor_boxes import Item, locate  # noqa: E402

LINES = [
    Item("Species 102. (Mus. Cuming.)", 100, 100, 270, 20),
    Item("BuLlMLS CiilLE.NSls. Bul. testa oblongo-ovata,", 100, 130, 460, 20),
    Item("tenui, subtiliter creberrime granulata;", 100, 160, 390, 20),
]
TEXT = "Species 102. (Mus. Cuming.)\nBULIMUS CHILENSIS. Bul. testa oblongo-ovata, tenui, subtiliter"


def span(s, sub):
    i = s.index(sub)
    return i, i + len(sub)


def test_exact_line_and_interpolated_box():
    s, e = span(TEXT, "Mus. Cuming")
    r = locate(TEXT, s, e, LINES)
    assert r["status"] == "boxed" and r["granularity"] == "line_interp"
    x0, y0, x1, y1 = r["box"]
    assert y0 == 100 and 100 < x0 < x1 < 370
    assert x1 - x0 < 0.6 * 270          # the value, not the whole line


def test_damaged_ocr_still_anchors_through_context():
    s, e = span(TEXT, "BULIMUS CHILENSIS")
    r = locate(TEXT, s, e, LINES, threshold=55)
    assert r["status"] == "boxed"
    assert r["box"][1] == 130            # the second line, despite the misread name


def test_below_threshold_is_missing_not_nearest():
    other = "Turritella brevialis, Lamarck. Hab. Senegal."
    r = locate(other, 0, 20, LINES, threshold=80)
    assert r["status"] == "text_verified_box_missing" and r["box"] is None


def test_reading_order_does_not_matter():
    swapped = [LINES[2], LINES[0], LINES[1]]   # the OCR read the page in a different order
    s, e = span(TEXT, "Mus. Cuming")
    r = locate(TEXT, s, e, swapped)
    assert r["status"] == "boxed" and r["box"][1] == 100


def test_repeated_name_disambiguated_by_context():
    lines = [Item("TURRITELLA brevialis, Lam. from Senegal", 0, 0, 400, 20),
             Item("TURRITELLA duplicata, Linn. from Ceylon", 0, 50, 400, 20)]
    text = "TURRITELLA duplicata, Linn. from Ceylon"
    r = locate(text, 0, 10, lines)
    assert r["status"] == "boxed" and r["box"][1] == 50


def test_identical_places_are_ambiguous():
    lines = [Item("TURRITELLA", 0, 0, 100, 20), Item("TURRITELLA", 0, 300, 100, 20)]
    r = locate("TURRITELLA", 0, 10, lines)
    assert r["status"] == "box_ambiguous" and r["box"] is None


def test_value_broken_across_lines():
    lines = [Item("the Sky-Lark (Alauda", 0, 0, 200, 20), Item("arvensis) breeds here", 0, 30, 220, 20)]
    text = "the Sky-Lark (Alauda arvensis) breeds here"
    s, e = span(text, "Alauda arvensis")
    r = locate(text, s, e, lines)
    assert r["status"] == "boxed"
    assert r["box"][1] == 0 and r["box"][3] == 50   # spans both lines
