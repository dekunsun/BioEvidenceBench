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
    c = match_page(gold, misread)["taxon"]
    assert c["lenient"][:3] == (1, 0, 0) and c["exact"][:3] == (1, 0, 0) and c["value"][:3] == (0, 1, 1)


def test_unaligned_prediction_is_false_positive():
    gold = pd.DataFrame([{"field": "locality", "start": 21, "end": 36, "text": "Central America"}])
    p = _pred([("locality", 0, 3, "xyz", None, None)])
    assert match_page(gold, p)["locality"]["lenient"][:3] == (0, 1, 1)


def test_norm_value_joins_line_end_hyphenation():
    assert norm_value("Ameri-\nca") == norm_value("america")


def test_prf():
    p, r, f = prf(8, 2, 2)
    assert round(p, 2) == 0.8 and round(r, 2) == 0.8 and round(f, 2) == 0.8


def test_norm_value_ignores_markdown_emphasis():
    assert norm_value("**BULIMUS CASTUS.**") == norm_value("BULIMUS CASTUS.")
    assert norm_value("*A. dulcivox*") == norm_value("A. dulcivox")


def test_ambiguous_gold_rows_are_optional():
    gold = pd.DataFrame([
        {"field": "taxon", "start": 0, "end": 14, "text": "BULIMUS CASTUS", "adjudication": "ambiguous"},
        {"field": "taxon", "start": 30, "end": 37, "text": "Bulimus", "adjudication": ""}])
    hit = _pred([("taxon", 0, 14, "BULIMUS CASTUS", 0, 14)])
    assert match_page(gold, hit)["taxon"]["lenient"] == (0, 0, 1, 1)      # no credit, no FP; counted as excluded
    assert match_page(gold, _pred([]))["taxon"]["lenient"] == (0, 0, 1, 0)  # the ambiguous row is not an FN


def test_prediction_takes_the_gold_span_it_overlaps_most():
    gold = pd.DataFrame([
        {"field": "locality", "start": 0, "end": 5, "text": "Dover", "adjudication": ""},
        {"field": "locality", "start": 10, "end": 16, "text": "Calais", "adjudication": ""}])
    p = _pred([("locality", 4, 16, "r and Calais", 4, 16), ("locality", 0, 5, "Dover", 0, 5)])
    assert match_page(gold, p)["locality"]["lenient"][:3] == (2, 0, 0)


def test_vernacular_is_scored_apart_from_taxon():
    gold = pd.DataFrame([{"field": "vernacular", "start": 0, "end": 8, "text": "Sky-Lark", "adjudication": ""}])
    p = _pred([("taxon", 0, 8, "Sky-Lark", 0, 8)])
    c = match_page(gold, p)
    assert c["taxon"]["lenient"][:3] == (0, 1, 0) and c["vernacular"]["lenient"][:3] == (0, 0, 1)


def test_two_predictions_on_one_gold_mention_give_one_tp_and_one_fp():
    gold = pd.DataFrame([{"field": "taxon", "start": 0, "end": 14, "text": "BULIMUS CASTUS", "adjudication": ""}])
    p = _pred([("taxon", 0, 7, "BULIMUS", 0, 7), ("taxon", 8, 14, "CASTUS", 8, 14),
               ("taxon", 0, 14, "BULIMUS CASTUS", 0, 14)])
    assert match_page(gold, p)["taxon"]["lenient"][:3] == (1, 2, 0)


def test_one_prediction_cannot_match_two_gold_mentions():
    gold = pd.DataFrame([
        {"field": "locality", "start": 0, "end": 8, "text": "Cornwall", "adjudication": ""},
        {"field": "locality", "start": 13, "end": 18, "text": "Devon", "adjudication": ""}])
    p = _pred([("locality", 0, 18, "Cornwall and Devon", 0, 18)])
    assert match_page(gold, p)["locality"]["lenient"][:3] == (1, 0, 1)


def test_assignment_is_optimal_not_greedy():
    # A greedy pass would give the wide prediction to the first gold span and strand the second one.
    gold = pd.DataFrame([
        {"field": "taxon", "start": 0, "end": 5, "text": "aaaaa", "adjudication": ""},
        {"field": "taxon", "start": 6, "end": 11, "text": "bbbbb", "adjudication": ""}])
    p = _pred([("taxon", 0, 11, "aaaaa bbbbb", 0, 11), ("taxon", 0, 5, "aaaaa", 0, 5)])
    assert match_page(gold, p)["taxon"]["lenient"][:3] == (2, 0, 0)


def test_strict_gold_is_preferred_over_ambiguous():
    gold = pd.DataFrame([
        {"field": "taxon", "start": 0, "end": 5, "text": "aaaaa", "adjudication": "ambiguous"},
        {"field": "taxon", "start": 4, "end": 9, "text": "abbbb", "adjudication": ""}])
    p = _pred([("taxon", 0, 9, "aaaaabbbb", 0, 9)])
    assert match_page(gold, p)["taxon"]["lenient"] == (1, 0, 0, 0)


def test_issue_regions_are_parsed_as_expert_offsets(tmp_path):
    from score import load_issues
    f = tmp_path / "issues.csv"
    f.write_text("page_id,issue_type,field,full_text,frag1_start,frag1_end,frag2_start,frag2_end,notes\n"
                 "8992612,non_contiguous,taxon,Alauda arvensis,10,16,40,48,caption between\n"
                 "8992612,other,locality,Dover,90,95,,,\n")
    assert load_issues(f) == {8992612: [(10, 16), (40, 48), (90, 95)]}
    assert load_issues(None) == {}


def test_norm_value_folds_typographic_hyphen_and_apostrophe_but_not_letters():
    from score import norm_value
    assert norm_value("WHITE‐ZONED ACHATINA") == norm_value("WHITE-ZONED ACHATINA")
    assert norm_value("PHILIPPI’S ACHATINA") == norm_value("PHILIPPI'S ACHATINA")
    assert norm_value("Achatinœ") != norm_value("Achatinæ")


def test_gold_rows_from_a_later_guide_version_can_be_made_optional(tmp_path):
    from score import load_gold
    p = tmp_path / "g.csv"
    p.write_text("page_id,start,end,field,text,qualifier,notes,adjudication,guide_version\n"
                 "1,0,4,vernacular,moss,,,adjudicated,v0.7\n"
                 "1,9,13,locality,Kent,,,,v0.6\n")
    assert list(load_gold(p).adjudication) == ["adjudicated", ""]
    assert list(load_gold(p, optional_after="v0.6").adjudication) == ["ambiguous", ""]
    assert list(load_gold(p, optional_after="v0.7").adjudication) == ["adjudicated", ""]


def test_excluded_rows_are_not_gold_but_optional_in_the_sensitivity_report(tmp_path):
    from score import load_gold
    p = tmp_path / "g.csv"
    p.write_text("page_id,start,end,field,text,qualifier,notes,adjudication,guide_version\n"
                 "1,0,7,vernacular,Finches,,in a cited title,excluded,v0.8\n"
                 "1,9,13,locality,Kent,,,,v0.6\n")
    assert list(load_gold(p).text) == ["Kent"]
    g = load_gold(p, optional_after="v0.6")
    assert list(g.text) == ["Finches", "Kent"] and list(g.adjudication) == ["ambiguous", ""]


def test_a_run_with_no_predictions_on_a_page_is_scored_not_crashed(tmp_path, monkeypatch):
    """An empty model answer on a page (and a page with no entities at all) must give
    zero predictions and the right false negatives, not an exception."""
    import pandas as pd
    import score
    pages = pd.read_csv(score.DATA / "sample_split.csv").query("split == 'dev'")
    pid = int(pages.PageID.iloc[0])
    text = score.page_text("expert", pid)
    word = text.split()[0]
    run = tmp_path / "empty_run"
    run.mkdir()
    # one prediction on another page only, so the first page has none in this arm
    other = int(pages.PageID.iloc[1])
    pd.DataFrame([{"page_id": other, "version": "expert", "condition": "G1", "i": 0, "field": "locality",
                   "line": 1, "model_text": "x", "had_line_label": False, "value": "",
                   "status": "invalid_evidence", "start": "", "end": "", "score": 0.0}]
                 ).to_csv(run / "dev_mentions.csv", index=False)
    gold = tmp_path / "gold.csv"
    rows = [f"{pid},0,{len(word)},locality,{word},,,,v0.8"] + [f"{int(q)},,,none,,,,,v0.8" for q in pages.PageID.iloc[1:]]
    gold.write_text("page_id,start,end,field,text,qualifier,notes,adjudication,guide_version\n" + "\n".join(rows) + "\n")
    monkeypatch.setattr(score, "RESULTS", tmp_path)
    d = score.score_run_detail("empty_run", gold, "dev")
    row = d["by_page"].query("page_id == @pid and field == 'locality'").iloc[0]
    assert row.n_pred == 0 and row.value_fn == 1 and row.value_tp == 0
