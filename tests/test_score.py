"""Scoring tests use made-up page text and made-up spans (not gold labels)."""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from score import char_map, map_span, match_page, norm_value, prf  # noqa: E402

EXPERT = "BULIMUS CASTUS. Hab. Central America?\nMus. Cuming."
LEGACY = "BuLIMUS CASTDS. Hob. Central Ameri-\nca? Mus. Cuming."


def _pred(rows):
    return pd.DataFrame(rows, columns=["field", "start", "end", "value", "m_start", "m_end"])


def test_alignment_maps_ocr_span_to_expert_span():
    cmap = char_map(LEGACY, EXPERT)
    s = LEGACY.index("Central")
    e = LEGACY.index("ca?") + 2
    assert map_span(cmap, s, e) == (EXPERT.index("Central"), EXPERT.index("Central") + len("Central America"))


def test_value_level_separates_misread_from_correct():
    gold = pd.DataFrame([{"field": "taxon", "start": 0, "end": 14, "text": "BULIMUS CASTUS"}])
    misread = _pred([("taxon", 0, 14, "BuLIMUS CASTDS", 0, 14)])
    c = match_page(gold, misread)
    assert c["lenient"] == (1, 0, 0) and c["exact"] == (1, 0, 0) and c["value"] == (0, 1, 1)


def test_unaligned_prediction_is_false_positive():
    gold = pd.DataFrame([{"field": "locality", "start": 21, "end": 36, "text": "Central America"}])
    p = _pred([("locality", 0, 3, "xyz", None, None)])
    assert match_page(gold, p)["lenient"] == (0, 1, 1)


def test_norm_value_joins_line_end_hyphenation():
    assert norm_value("Ameri-\nca") == norm_value("america")


def test_prf():
    p, r, f = prf(8, 2, 2)
    assert round(p, 2) == 0.8 and round(r, 2) == 0.8 and round(f, 2) == 0.8


def test_norm_value_ignores_markdown_emphasis():
    assert norm_value("**BULIMUS CASTUS.**") == norm_value("BULIMUS CASTUS.")
    assert norm_value("*A. dulcivox*") == norm_value("A. dulcivox")
