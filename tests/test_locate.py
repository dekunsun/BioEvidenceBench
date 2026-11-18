import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from locate import locate_all, locate_g0, locate_g1  # noqa: E402
from prompts import number_lines  # noqa: E402

PAGE = "BULIMUS.\n\nSpecies 2S3. (Mus. Dennison.)\n\nBuLIMUS CASTDS. Bul. testa\n\nHob. Central America?"


def test_number_lines_matches_line_numbers():
    numbered = number_lines(PAGE).split("\n")
    assert numbered[4].startswith("L5| BuLIMUS CASTDS")


def test_g1_exact_and_value_sliced_from_source():
    r = locate_g1(PAGE, 5, "BuLIMUS CASTDS")
    assert r["status"] == "exact" and PAGE[r["start"]:r["end"]] == "BuLIMUS CASTDS"


def test_g1_silent_correction_keeps_source_text():
    # The model "fixed" the OCR in its quote; the value must still come from the source.
    out = locate_all(PAGE, "G1", [{"field": "taxon", "line": 5, "quote": "BULIMUS CASTUS"}])[0]
    assert out["status"] == "silent_correction"
    assert out["value"] == "BuLIMUS CASTDS"
    assert out["model_text"] == "BULIMUS CASTUS"


def test_g1_wrong_line_and_invalid():
    assert locate_g1(PAGE, 1, "Central America")["status"] == "wrong_line"
    assert locate_g1(PAGE, 99, "x")["status"] == "invalid_evidence"
    assert locate_g1(PAGE, 7, "Philippine Islands")["status"] == "invalid_evidence"


def test_g0_statuses():
    assert locate_g0(PAGE, "Central America")["status"] == "exact"
    assert locate_g0(PAGE, "bulimus castds")["status"] == "case_variant"
    assert locate_g0(PAGE, "BuLIMUS CASTUS")["status"] == "fuzzy"
    assert locate_g0(PAGE, "Philippine Islands")["status"] == "not_found"


def test_g0_repeated_values_map_to_successive_occurrences():
    page = "Hab. Cuba.\nHab. Cuba."
    out = locate_all(page, "G0", [{"field": "locality", "value": "Cuba"}] * 2)
    assert [o["start"] for o in out] == [5, 16]
