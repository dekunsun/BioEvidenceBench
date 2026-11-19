"""Tests for the linking scorer. All names and GBIF responses here are made up or public
textbook examples typed in by hand; no gold label and no network call is involved."""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import link_taxa as lt  # noqa: E402

SPECIES = {"matchType": "EXACT", "rank": "SPECIES", "status": "ACCEPTED", "usageKey": 100}
SYNONYM = {"matchType": "EXACT", "rank": "SPECIES", "status": "SYNONYM", "usageKey": 200,
           "acceptedUsageKey": 100}
GENUS = {"matchType": "HIGHERRANK", "rank": "GENUS", "status": "ACCEPTED", "usageKey": 9}
NONE = {"matchType": "NONE"}


def pred(resp):
    return lt.summarise_response(resp)


def test_clean_name_layout_only():
    assert lt.clean_name("*Alauda arvensis*") == "Alauda arvensis"
    assert lt.clean_name("A. blak-\nistoni") == "A. blakistoni"
    assert lt.clean_name("A. blak- istoni") == "A. blakistoni"
    assert lt.clean_name("ALAUDIDÆ.") == "Alaudidae"
    assert lt.clean_name("ACCENTOR MODULARIS") == "Accentor modularis"
    # an OCR misreading is left alone: the linker never corrects spelling
    assert lt.clean_name("A. giilgiila") == "A. giilgiila"


def test_name_form():
    assert lt.name_form("A. gulgula") == "abbreviated"
    assert lt.name_form("Alauda") == "uninomial"
    assert lt.name_form("ALAUDA ARVENSIS") == "binomial"
    assert lt.name_form("Passer domesticus domesticus") == "trinomial_or_longer"


def test_expand_abbreviation_uses_nearest_earlier_genus():
    earlier = ["Alaudidæ", "Alauda arvensis", "Anthus pratensis", "A. sala"]
    assert lt.expand_abbreviation("A. gulgula", earlier) == ("Anthus gulgula", True)
    assert lt.expand_abbreviation("A. gulgula", earlier[:2]) == ("Alauda gulgula", True)
    # a family name starting with the same letter is not a genus to expand from
    assert lt.expand_abbreviation("A. gulgula", ["Alaudidæ"]) == ("A. gulgula", False)
    assert lt.expand_abbreviation("P. major", earlier) == ("P. major", False)
    assert lt.expand_abbreviation("Alauda arvensis", earlier) == ("Alauda arvensis", False)


def test_outcome_resolved_rows():
    assert lt.outcome("resolved", "species", "100", pred(SPECIES)) == "correct"
    # a synonym counts when its accepted taxon is the gold one
    assert lt.outcome("resolved", "species", "100.0", pred(SYNONYM)) == "correct"
    assert lt.outcome("resolved", "species", "555", pred(SPECIES)) == "wrong_taxon"
    assert lt.outcome("resolved", "species", "100", pred(NONE)) == "no_link"
    assert lt.outcome("resolved", "species", "100", None) == "not_extracted"


def test_genus_match_for_a_species_name_is_never_correct():
    # even when the genus key happens to equal the gold key
    assert lt.outcome("resolved", "species", "9", pred(GENUS)) == "partial_only"
    # but a name printed as a genus and matched as a genus is correct
    assert lt.outcome("resolved", "genus", "9", pred(GENUS)) == "correct"


def test_outcome_rows_without_a_trustworthy_record():
    assert lt.outcome("unresolved", "species", "", pred(SPECIES)) == "overclaim"
    assert lt.outcome("partial", "species", "9", pred(SPECIES)) == "overclaim"
    assert lt.outcome("partial", "species", "9", pred(GENUS)) == "correct_abstain"
    assert lt.outcome("unresolved", "species", "", pred(NONE)) == "correct_abstain"
    assert lt.outcome("unresolved", "species", "", None) == "correct_abstain"
    assert lt.outcome("ambiguous", "species", "", pred(SPECIES)) == "ambiguous_gold"


def _rows():
    base = {"printed_rank": "species", "evidence_source": "Avibase", "run": "r", "version": "expert",
            "condition": "GOLD", "extracted": True}
    return pd.DataFrame([
        base | {"page_id": 1, "start": 0, "end": 15, "text": "Alauda arvensis", "name": "Alauda arvensis",
                "earlier": [], "resolution_status": "resolved", "accepted_usage_key": "100"},
        base | {"page_id": 1, "start": 30, "end": 40, "text": "A. gulgula", "name": "A. gulgula",
                "earlier": ["Alauda arvensis"], "resolution_status": "resolved", "accepted_usage_key": "300"},
        base | {"page_id": 2, "start": 5, "end": 20, "text": "Alauda nonesuch", "name": "Alauda nonesuch",
                "earlier": [], "resolution_status": "partial", "accepted_usage_key": "9"},
        base | {"page_id": 2, "start": 50, "end": 60, "text": "Alauda sp.", "name": "", "earlier": [],
                "resolution_status": "resolved", "accepted_usage_key": "100", "extracted": False},
    ])


def _cache(tmp_path, calls):
    table = {"Alauda arvensis": SPECIES, "Alauda gulgula": SPECIES | {"usageKey": 300},
             "A. gulgula": NONE, "Alauda nonesuch": GENUS}

    def fetch(name):
        calls.append(name)
        return table[name]
    return lt.GbifCache(tmp_path / "gbif.jsonl", fetch=fetch)


def test_link_rows_and_summary(tmp_path):
    calls = []
    scored = lt.link_rows(_rows(), _cache(tmp_path, calls))
    got = {(r.text, r.linker): r.outcome for r in scored.itertuples()}
    assert got[("Alauda arvensis", "printed")] == "correct"
    assert got[("A. gulgula", "printed")] == "no_link"          # GBIF cannot read "A."
    assert got[("A. gulgula", "expanded")] == "correct"         # expanded from the page
    assert got[("Alauda nonesuch", "printed")] == "correct_abstain"
    assert got[("Alauda sp.", "expanded")] == "not_extracted"
    assert "" not in calls                                      # nothing is looked up for a missed mention

    s = lt.summarise(scored, ["linker"]).set_index("linker")
    assert s.loc["printed", "gold_resolved"] == 3 and s.loc["printed", "correct"] == 1
    assert s.loc["printed", "link_recall"] == round(1 / 3, 3)
    assert s.loc["expanded", "link_recall"] == round(2 / 3, 3)
    assert s.loc["expanded", "link_precision"] == 1.0
    assert s.loc["expanded", "gold_partial"] == 1 and s.loc["expanded", "correct_abstain"] == 1


def test_cache_is_reused_from_disk(tmp_path):
    calls = []
    lt.link_rows(_rows(), _cache(tmp_path, calls))
    n = len(calls)
    assert n == len(set(calls))                                  # one request per distinct name
    lt.link_rows(_rows(), _cache(tmp_path, calls))               # second run reads the file
    assert len(calls) == n


def test_load_links_rejects_resolved_without_key(tmp_path):
    p = tmp_path / "links.csv"
    cols = "page_id,start,end,text,printed_rank,resolution_status,match_method,matched_rank," \
           "taxonomic_status,matched_usage_key,accepted_usage_key,evidence_source,notes\n"
    p.write_text(cols + "1,0,5,Aaaaa,species,resolved,exact,species,accepted,,,GBIF,\n")
    try:
        lt.load_links(p)
    except SystemExit as e:
        assert "accepted_usage_key" in str(e)
    else:
        raise AssertionError("expected SystemExit")


def test_loss_at_linking_versus_before_it(tmp_path):
    scored = lt.link_rows(_rows(), _cache(tmp_path, []))
    s = lt.summarise(scored, ["linker"]).set_index("linker")
    # printed: 3 resolved names; "A. gulgula" is lost at linking, "Alauda sp." before it
    assert s.loc["printed", "lost_at_linking"] == 1 and s.loc["printed", "lost_before_linking"] == 1
    assert s.loc["printed", "linking_minus_earlier_loss"] == 0.0
    # expanded: nothing is lost at linking any more, one name is still lost before it
    assert s.loc["expanded", "lost_at_linking"] == 0
    assert s.loc["expanded", "linking_minus_earlier_loss"] == round(-1 / 3, 3)
    assert s.loc["expanded", "loss_diff_verdict"] in ("against", "inconclusive")


def test_expand_links_turns_accepted_names_into_keys_and_copies_to_every_mention(tmp_path):
    import pandas as pd
    import expand_links as ex
    table = {"Turdidae": {"matchType": "EXACT", "canonicalName": "Turdidae", "rank": "FAMILY",
                          "status": "ACCEPTED", "usageKey": 5290},
             "Alauda": {"matchType": "EXACT", "canonicalName": "Alauda", "rank": "GENUS",
                        "status": "ACCEPTED", "usageKey": 2490696},
             "Accentor modularis": {"matchType": "EXACT", "canonicalName": "Accentor modularis",
                                    "rank": "SPECIES", "status": "SYNONYM", "usageKey": 7604351,
                                    "acceptedUsageKey": 5231763}}
    names = pd.DataFrame([
        {"name": "TURDIDÆ", "printed_rank": "family", "resolution_status": "resolved", "accepted_name": "Turdidae"},
        {"name": "A. blakistoni", "printed_rank": "species", "resolution_status": "partial", "accepted_name": "Alauda"},
        {"name": "A. modularis", "printed_rank": "species", "resolution_status": "resolved",
         "accepted_name": "Accentor modularis"},
    ]).set_index("name")
    links = tmp_path / "links.csv"
    links.write_text("page_id,start,end,text\n1,0,7,TURDIDÆ\n2,0,7,TURDIDÆ\n2,9,24,\"A. blak-\nistoni\"\n"
                     "3,0,12,A. modularis\n")
    out = ex.expand(names, links, tmp_path / "lookup.csv", fetch=lambda n: table[n])
    assert out.accepted_usage_key.tolist() == ["5290", "5290", "2490696", ""]   # a synonym is not filled in
    assert out.resolution_status.tolist() == ["resolved", "resolved", "partial", "resolved"]
    assert "SYNONYM" in (tmp_path / "lookup.csv").read_text()


def test_expand_links_takes_the_single_accepted_bird_record_of_a_homonym():
    import expand_links as ex
    passer = {"matchType": "HIGHERRANK", "canonicalName": "Chordata", "rank": "PHYLUM", "usageKey": 44,
              "alternatives": [
                  {"matchType": "EXACT", "canonicalName": "Passer", "rank": "GENUS", "status": "ACCEPTED",
                   "usageKey": 2492321, "class": "Aves"},
                  {"matchType": "EXACT", "canonicalName": "Passer", "rank": "GENUS", "status": "SYNONYM",
                   "usageKey": 7864359}]}
    assert ex.key_for("Passer", "genus", fetch=lambda n: passer) == ("2492321", "")
    two = passer | {"alternatives": passer["alternatives"] + [passer["alternatives"][0] | {"usageKey": 1}]}
    assert ex.key_for("Passer", "genus", fetch=lambda n: two)[0] == ""          # two candidates: not filled
    assert ex.key_for("Passer", "species", fetch=lambda n: passer)[0] == ""     # wrong rank: not filled
    fringilla = {"matchType": "HIGHERRANK", "canonicalName": "Fringilla", "rank": "GENUS", "status": "ACCEPTED",
                 "usageKey": 2494421, "class": "Aves",
                 "alternatives": [{"matchType": "EXACT", "canonicalName": "Fringilla", "rank": "SPECIES",
                                   "status": "ACCEPTED", "usageKey": 11969741, "class": "Aves"}]}
    assert ex.key_for("Fringilla", "genus", fetch=lambda n: fringilla) == ("2494421", "")


def test_subfamily_rows_are_left_out_of_link_scoring(tmp_path):
    p = tmp_path / "links.csv"
    cols = "page_id,start,end,text,printed_rank,resolution_status,accepted_usage_key,evidence_source\n"
    p.write_text(cols + "1,0,8,SYLVIINÆ,subfamily,resolved,,GBIF\n1,9,15,Passer,genus,resolved,2492321,GBIF\n")
    d = lt.load_links(p)          # a resolved subfamily row without a key is not an error
    assert d.text.tolist() == ["Passer"]
    assert d.attrs["not_in_backbone"].text.tolist() == ["SYLVIINÆ"]
