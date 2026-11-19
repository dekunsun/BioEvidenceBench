"""Tests for the pre-registered analyses, on small made-up tables (not gold labels)."""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import analysis as an  # noqa: E402


def _pages(tp, fp, fn, level="value"):
    return pd.DataFrame({"page_id": range(len(tp)), f"{level}_tp": tp, f"{level}_fp": fp, f"{level}_fn": fn})


def test_paired_bootstrap_identical_arms_have_zero_difference():
    a = _pages([5, 3, 8], [1, 0, 2], [1, 2, 0])
    r = an.paired_bootstrap(a, a.copy(), "value", "F1")
    assert r["diff"] == 0 and r["lo"] == 0 and r["hi"] == 0


def test_paired_bootstrap_detects_a_consistent_gain():
    a = _pages([9, 9, 9, 9, 9, 9], [1] * 6, [1] * 6)
    b = _pages([5, 5, 5, 5, 5, 5], [5] * 6, [5] * 6)
    r = an.paired_bootstrap(a, b, "value", "F1")
    assert r["diff"] == 0.4 and r["lo"] > 0.3
    assert an.verdict(r["lo"], r["hi"], "at_least", 0.10) == "supports"


def test_verdict_rules():
    assert an.verdict(0.12, 0.30, "at_least", 0.10) == "supports"
    assert an.verdict(-0.05, 0.08, "at_least", 0.10) == "against"
    assert an.verdict(0.02, 0.20, "at_least", 0.10) == "inconclusive"
    assert an.verdict(-0.02, 0.03, "less_than", 0.05) == "supports"
    assert an.verdict(0.06, 0.20, "less_than", 0.05) == "against"
    assert an.verdict(-0.03, 0.01, "greater_than", -0.05) == "supports"
    assert an.verdict(0.0, 0.1, None, None) == "descriptive"


def test_type_check():
    assert an.type_check("date", "3rd May, 1890")[0] and an.type_check("date", "April")[0]
    assert not an.type_check("date", "p. 112")[0]
    assert an.type_check("taxon", "Bulimus castus")[0] and not an.type_check("taxon", "castus 12")[0]
    assert not an.type_check("person", "the author")[0]
    assert not an.type_check("locality", "")[0]
    assert an.type_check("vernacular", "pheasants")[0]


def _gold(rows):
    return pd.DataFrame(rows, columns=["run", "book", "version", "condition", "page_id", "field", "start",
                                       "adjudication", "lenient", "value_ok"])


def test_stage_loss_puts_each_mention_in_exactly_one_stage():
    g = _gold([
        ("r", "Reeve", "legacy", "G1", 1, "taxon", 0, "", True, False),    # misread by OCR, still found
        ("r", "Reeve", "legacy", "G1", 1, "taxon", 10, "", False, False),  # survived OCR, not extracted
        ("r", "Reeve", "legacy", "G1", 1, "taxon", 20, "", True, False),   # survived, extracted, boundary wrong
        ("r", "Reeve", "legacy", "G1", 1, "taxon", 30, "", True, True),    # kept
        ("r", "Reeve", "legacy", "G1", 1, "taxon", 40, "ambiguous", False, False),  # not counted
    ])
    cer = pd.DataFrame({"page_id": [1] * 4, "field": ["taxon"] * 4, "version": ["legacy"] * 4,
                        "gold_start": [0, 10, 20, 30], "preserved": [False, True, True, True]})
    t = an.stage_loss(g, cer)
    row = t[t.field == "taxon"].iloc[0]
    assert (row.lost_at_ocr, row.lost_at_extraction, row.lost_at_value, row.kept, row.gold) == (1, 1, 1, 1, 4)
    assert row.of_which_still_found == 1


def test_expert_version_never_loses_mentions_at_ocr():
    g = _gold([("r", "Reeve", "expert", "G1", 1, "taxon", 0, "", False, False)])
    cer = pd.DataFrame({"page_id": [], "field": [], "version": [], "gold_start": [], "preserved": []})
    t = an.stage_loss(g, cer)
    assert t[t.field == "taxon"].iloc[0].lost_at_extraction == 1


def _pred(rows):
    return pd.DataFrame(rows, columns=["page_id", "book", "version", "field", "src_start", "src_end", "value",
                                       "status", "outcome", "value_ok"])


def test_flag_needs_agreement_clean_evidence_and_type():
    a = _pred([
        (1, "Reeve", "expert", "taxon", 0, 14, "Bulimus castus", "exact", "tp_value", True),
        (1, "Reeve", "expert", "taxon", 30, 44, "Bulimus obesus", "exact", "tp_value", True),      # B did not find it
        (1, "Reeve", "expert", "taxon", 60, 74, "Bulimus rubens", "silent_correction", "tp_value", True),
        (1, "Reeve", "expert", "locality", 90, 96, "Brazil", "exact", "fp_no_gold", False),
    ])
    b = _pred([
        (1, "Reeve", "expert", "taxon", 0, 14, "Bulimus castus", "exact", "tp_value", True),
        (1, "Reeve", "expert", "taxon", 58, 74, "s Bulimus rubens", "exact", "fp_value_wrong", False),
        (1, "Reeve", "expert", "locality", 90, 96, "Brazil", "exact", "fp_no_gold", False),
    ])
    f = an.flag_auto_accept(a, b)
    assert f.flagged.tolist() == [True, False, False, True]
    assert f.tier.tolist() == [0, 2, 1, 0]
    cov = an.risk_coverage(f)
    first = cov[cov.accept_up_to_tier == 0].iloc[0]
    assert first.accepted == 2 and first.errors_accepted == 1 and first.risk == 0.5   # a shared error


def test_one_prediction_of_b_cannot_confirm_two_predictions_of_a():
    a = _pred([(1, "Reeve", "expert", "locality", 0, 8, "Cornwall", "exact", "tp_value", True),
               (1, "Reeve", "expert", "locality", 13, 18, "Devon", "exact", "tp_value", True)])
    b = _pred([(1, "Reeve", "expert", "locality", 0, 18, "Cornwall and Devon", "exact", "fp_value_wrong", False)])
    assert an.flag_auto_accept(a, b).agree.sum() == 1


def test_evidence_counters_use_the_preregistered_definitions():
    m = pd.DataFrame({"page_id": ["1"] * 5, "version": ["legacy"] * 5,
                      "condition": ["G0", "G0", "G1", "G1", "G1"],
                      "field": ["taxon"] * 5, "value": ["Bulimus", "", "Bulimus", "Bulimus", ""],
                      "status": ["fuzzy", "not_found", "silent_correction", "wrong_line", "invalid_evidence"],
                      "had_line_label": ["False"] * 5})
    t = an.evidence_counters(m, pd.DataFrame({"PageID": [1], "book": ["Reeve"]}))
    g0, g1 = t[t.condition == "G0"].iloc[0], t[t.condition == "G1"].iloc[0]
    assert g0.unsupported == 2 and g1.unsupported == 2 and g1.wrong_line == 1


def test_rq4_leaves_out_pages_model_b_did_not_answer_and_needs_enough_unflagged():
    a = _pred([(1, "Reeve", "expert", "taxon", 0, 14, "Bulimus castus", "exact", "tp_value", True),
               (2, "Reeve", "expert", "taxon", 0, 14, "Bulimus obesus", "exact", "tp_value", True)])
    b = _pred([(1, "Reeve", "expert", "taxon", 0, 14, "Bulimus castus", "exact", "tp_value", True)])
    f = an.flag_auto_accept(a, b, b_answered={(1, "expert")})
    assert f.b_answered.tolist() == [True, False]
    gold = pd.DataFrame({"page_id": [1, 2], "book": ["Reeve"] * 2, "version": ["expert"] * 2,
                         "field": ["taxon"] * 2, "start": [0, 0], "end": [14, 14],
                         "adjudication": [""] * 2, "lenient": [True, True]})
    s = an.rq4_summary(f, gold, gold).iloc[0]
    assert s.predictions == 1 and s.excluded_no_answer_from_b == 1 and s.gold == 1
    assert s.verdict == "too few to compare"          # 0 unflagged predictions, not "against"
    cov = an.risk_coverage(f)
    assert cov.accepted.max() == 1


def test_answered_pairs_counts_ok_and_empty_only():
    o = pd.DataFrame({"run": ["r"] * 3, "page_id": [1, 2, 3], "version": ["expert"] * 3,
                      "condition": ["G1"] * 3, "outcome": ["ok", "empty", "parse_error"]})
    assert an.answered_pairs(o, "r") == {(1, "expert"), (2, "expert")}
