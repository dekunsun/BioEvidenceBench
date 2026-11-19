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


def test_rule_condition_uses_given_offsets():
    out = locate_all(PAGE, "RULE", [{"field": "locality", "start": 74, "end": 89}])[0]
    assert out["status"] == "exact" and out["value"] == PAGE[74:89]


def test_g1_repeated_quotes_in_one_line_map_to_successive_occurrences():
    # modern OCR text has one paragraph per line, so a word often repeats in a line
    page = "Title\nThe Jackdaw nests here; the Jackdaw also robs the Barn Owl."
    ms = [{"field": "vernacular", "line": 2, "quote": "Jackdaw"}] * 2
    out = locate_all(page, "G1", ms)
    assert [o["start"] for o in out] == [10, 34] and all(o["status"] == "exact" for o in out)
    # a third quote has no third occurrence: it stays on the last one
    assert locate_all(page, "G1", ms * 2)[2]["start"] == 34


def test_g1_same_quote_on_different_lines_is_counted_per_line():
    page = "Hab. Cuba.\nHab. Cuba."
    out = locate_all(page, "G1", [{"field": "locality", "line": 1, "quote": "Cuba"},
                                  {"field": "locality", "line": 2, "quote": "Cuba"}])
    assert [o["start"] for o in out] == [5, 16]


def test_g0_extra_repeat_uses_a_line_broken_occurrence():
    page = "Hab. Jamaica.\nfrom Ja-\nmaica."
    out = locate_all(page, "G0", [{"field": "locality", "value": "Jamaica"}] * 2)
    assert out[0]["status"] == "exact" and out[0]["start"] == 5
    assert out[1]["status"] == "layout_variant" and out[1]["value"] == "Ja-\nmaica"


def test_g0_value_is_not_placed_inside_a_longer_word():
    text = "The Jackdaws left.\nA Jackdaw stayed; the Daw called."
    out = locate_all(text, "G0", [{"field": "vernacular", "value": "Jackdaw"},
                                  {"field": "vernacular", "value": "Jackdaws"},
                                  {"field": "vernacular", "value": "Daw"}])
    assert [text[o["start"]:o["end"]] for o in out] == ["Jackdaw", "Jackdaws", "Daw"]
    assert out[0]["start"] == text.index("Jackdaw stayed")       # not inside "Jackdaws"
    assert out[2]["start"] == text.index("Daw called")           # not inside "Jackdaw"


def test_g0_short_value_avoids_a_span_taken_by_a_longer_mention():
    text = "The Hooded Crow breeds here. Mus. Benson has one.\nThe Crow was shot by Benson."
    out = locate_all(text, "G0", [{"field": "vernacular", "value": "Hooded Crow"},
                                  {"field": "institution", "value": "Mus. Benson"},
                                  {"field": "vernacular", "value": "Crow"},
                                  {"field": "person", "value": "Benson"}])
    assert out[2]["start"] == text.index("Crow was")
    assert out[3]["start"] == text.index("Benson.")


def test_g0_same_string_in_two_fields_gets_two_occurrences():
    text = "Lord Lilford wrote of the park of Lilford."
    out = locate_all(text, "G0", [{"field": "person", "value": "Lilford"},
                                  {"field": "locality", "value": "Lilford"}])
    assert out[0]["start"] != out[1]["start"]
    assert out[0]["start"] == text.index("Lilford wrote")
