"""Fixed unit tests for task B's Reward v1.1 (rl/env/task_b_ocr_repair/REWARD_DESIGN.md).

    python -m pytest tests/test_rl_task_b.py -q

Each test is one rule from the design: no network, no model.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pytest  # noqa: E402

import rl_task_b as T  # noqa: E402

REF = "Muscicapa parva recorded in specimens"
OCR = "Muscicapa parua recorded in specirnens"
NAME = [False, True, False, False, False]          # "parva" is a scientific-name word (weight 3)


def u(target=REF, inp=OCR, flags=NAME):
    return T.make_unit(target, inp, flags)


def r(unit, out):
    return T.reward(unit, out)


# ---------------------------------------------------------------- basic
def test_perfect_repair_scores_one():
    assert r(u(), REF)["reward"] == 1.0


def test_returning_ocr_unchanged_scores_zero_on_damaged_line():
    d = r(u(), OCR)
    assert d["reward"] == 0.0 and d["repaired_words"] == 0 and d["extra_words"] == 0


def test_returning_a_clean_line_unchanged_scores_one():
    clean = "the dry and barren regions"
    assert r(u(clean, clean, [False] * 5), clean)["reward"] == 1.0


# ---------------------------------------------------------------- the worked example (name weight 3)
@pytest.mark.parametrize("out, expected", [
    ("Muscicapa parua recorded in specimens", 0.25),        # only the ordinary word repaired
    ("Muscicapa parva recorded in specirnens", 0.75),       # only the name repaired
    (REF, 1.0),                                             # both
    ("Muscicapa parva recordd in specimens", 0.5),          # both, one correct word broken: -0.5
])
def test_weighted_repair_and_fixed_penalty(out, expected):
    assert r(u(), out)["reward"] == pytest.approx(expected)


# ---------------------------------------------------------------- penalties are fixed per action
def test_breaking_a_correct_word_costs_the_same_on_any_line():
    clean = "the dry and barren regions"
    d_clean = r(u(clean, clean, [False] * 5), "the dry and barren regionz")
    assert d_clean["damaged_correct_words"] == 1 and d_clean["reward"] == 0.5


def test_inserted_word_costs_a_quarter():
    clean = "the dry and barren regions"
    d = r(u(clean, clean, [False] * 5), "the dry and barren regions xyz")
    assert d["extra_words"] == 1 and d["reward"] == 0.75


def test_duplicated_correct_word_is_not_rewarded_twice():
    clean = "the dry and barren regions"
    d = r(u(clean, clean, [False] * 5), "the dry dry and barren regions")
    assert d["extra_words"] == 1 and d["reward"] == 0.75


# ---------------------------------------------------------------- no double counting
def test_wrong_repair_is_a_substitution_not_an_insertion():
    unit = u("the dry and barren regions", "the dry and ban-en regions", [False] * 5)
    d = r(unit, "the dry and barrem regions")
    assert d["repaired_words"] == 0 and d["extra_words"] == 0 and d["reward"] == 0.0


def test_ocr_fragments_kept_are_not_penalised_again():
    unit = u("The examples of B. pythogaster selected", "The examples ofB.pi/iko//nster selected",
             [False, False, False, True, True, False])
    d = r(unit, unit["input"])
    assert d["reward"] == 0.0 and d["extra_words"] == 0


def test_writing_the_right_word_next_to_the_damaged_one_is_not_a_repair():
    unit = u("the dry and barren regions", "the dry and ban-en regions", [False] * 5)
    d = r(unit, "the dry and ban-en barren regions")
    assert d["repaired_words"] == 0 and d["reward"] <= 0.0


# ---------------------------------------------------------------- format gate
@pytest.mark.parametrize("out, reason", [
    ("", "empty"),
    ("   ", "empty"),
    (REF + "\n" + REF, "several lines"),
    ("Corrected line: " + REF, "commentary prefix"),
    ("Here is the repaired text: " + REF, "commentary prefix"),
    ("*" + REF + "*", "wrapped in *"),
    ("```" + REF + "```", "wrapped in ```"),
    ('"' + REF + '"', 'wrapped in "'),
])
def test_format_errors_score_zero_and_are_flagged(out, reason):
    d = r(u(), out)
    assert d["reward"] == 0.0 and not d["format_valid"] and d["format_reason"] == reason


def test_integrity_check_rejects_a_much_longer_answer():
    d = r(u(), REF + " " + REF)
    assert d["format_valid"] and not d["integrity_valid"] and d["reward"] == 0.0


# ---------------------------------------------------------------- characters
def test_typographic_ligatures_are_folded():
    assert T.nfc("ﬁnest diﬀerences") == "finest differences"


def test_spelling_ligature_letters_are_kept():
    clean = "named by Linnæus himself"
    d = r(u(clean, clean, [False] * 4), "named by Linnaeus himself")
    assert d["damaged_correct_words"] == 1 and d["reward"] == 0.5


@pytest.mark.parametrize("out, strict, reading", [
    ("ſpecies novæ", 1.0, 1.0),     # the transcription's own glyph
    ("species novæ", 0.0, 1.0),     # long s read as s: wrong for the main reward, right for reading
    ("fpecies novæ", 0.0, 0.0),     # the OCR's f for ſ: wrong for both
])
def test_long_s_main_reward_and_reading_metric(out, strict, reading):
    unit = u("ſpecies novæ", "fpecies novæ", [False, False])
    d = r(unit, out)
    assert d["reward"] == strict and d["reward_reading"] == reading


def test_reward_is_clipped_to_minus_one():
    clean = "one two three four five"
    d = r(u(clean, clean, [False] * 5), "oNe tWo tHree fOur fIve")
    assert d["reward"] == -1.0


def test_mufi_ligatures_are_folded_and_long_s_kept():
    assert T.nfc("e\ueada, fo\ueba7libus, Inſe\ueec5a") == "eſt, foſſilibus, Inſecta"


def test_reference_with_an_unreadable_character_is_marked():
    assert T._UNREADABLE.search("GOLDEN ORIOLE \ufffd") and T._UNREADABLE.search("Sturnid\uefa1")
    assert not T._UNREADABLE.search("Linnæus ſpecies")
