import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from common import legacy_ocr_url, markdown_drop_mask, markdown_to_plain, normalize_for_cer  # noqa: E402
from compute_cer import band, cer, word_miss  # noqa: E402
from load_gt import offset_view  # noqa: E402


def test_normalize_folds_ligatures_quotes_and_whitespace():
    assert normalize_for_cer("reﬂexa “X”\n  ſpecies") == 'reﬂexa "X" species'.replace("ﬂ", "fl")


def test_cer_basic():
    assert cer("Hob.", "Hab.") == 0.25
    assert cer("same", "same") == 0.0


def test_word_miss_ignores_order():
    assert word_miss("b a", "a b") == 0.0
    assert word_miss("a", "a b") == 0.5


def test_bands():
    assert [band(x) for x in (0.0, 0.019, 0.02, 0.099, 0.10, 2.0)] == ["low", "low", "medium", "medium", "high", "high"]


def test_offset_view_offsets_slice_back_to_the_text():
    text = "BULIMUS.\n\nHab. Central America?"
    view = offset_view(text).splitlines()
    start = int(view[2].split("|")[0])
    assert text[start:start + 4] == "Hab."


def test_legacy_url_padding():
    assert legacy_ocr_url(35904, 8967091, 381).endswith("item-035904/item-035904-08967091-0381.txt")


def test_markdown_ablation_only_deletes_marks_and_keeps_lines():
    md = "# BULIMUS.\n\n**BULIMUS CASTUS.** *Bul. testâ* thus * marked\n### Species 124. (*Mus. Cuming.*)"
    plain = markdown_to_plain(md)
    assert plain == "BULIMUS.\n\nBULIMUS CASTUS. Bul. testâ thus * marked\nSpecies 124. (Mus. Cuming.)"
    assert plain.count("\n") == md.count("\n")
    dropped = {c for c, d in zip(md, markdown_drop_mask(md)) if d}
    assert dropped <= {"*", "#", " "}


def test_markdown_pairs_never_span_a_line_break():
    md = "one * footnote mark\nand another * here"
    assert markdown_to_plain(md) == md
