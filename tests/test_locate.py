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


LEGACY = "The bird of the valley of the \n Amoor is A. blak- \n istoni, and B. annu-\nlatus.\nHab. Ja- \n maica."


def test_g0_layout_variants_are_found_not_hallucinations():
    for v, want in [("valley of the Amoor", "valley of the \n Amoor"),
                    ("A. blak- istoni", "A. blak- \n istoni"),
                    ("A. blakistoni", "A. blak- \n istoni"),
                    ("B. annulatus", "B. annu-\nlatus"),
                    ("B. annu-\nlatus", "B. annu-\nlatus")]:
        r = locate_all(LEGACY, "G0", [{"field": "taxon", "value": v}])[0]
        assert r["status"] in ("exact", "layout_variant"), (v, r)
        assert r["value"] == want, (v, r["value"])


def test_line_labels_copied_by_the_model_are_removed_and_flagged():
    r = locate_all(LEGACY, "G0", [{"field": "locality", "value": "Ja- \nL074| \nL075|  maica"}])[0]
    assert r["had_line_label"] and r["status"] == "layout_variant" and r["value"] == "Ja- \n maica"


def test_g1_cross_line_quote():
    # cited line 2 is " Amoor is A. blak- "; the quote runs onto line 3
    r = locate_all(LEGACY, "G1", [{"field": "taxon", "line": 2, "quote": "A. blakistoni"}])[0]
    assert r["status"] == "cross_line" and r["value"] == "A. blak- \n istoni"


def test_flatten_does_not_create_matches_across_unrelated_text():
    assert locate_all(LEGACY, "G0", [{"field": "taxon", "value": "Amoor Hab."}])[0]["status"] != "exact"
