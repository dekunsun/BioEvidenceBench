"""Patched copy of the scorer's value rules, for rl/ only. src/score.py (frozen) is NOT changed.

Two patches, from the 2A attack (rl/verifier_audit/adversarial/REPORT.md):

1. Fidelity gate. In G0 and G1 the value is sliced from the source wherever the locator finds the
   model's text. When it only finds it by fuzzy match (`fuzzy`, `silent_correction`) or by case
   (`case_variant`), the frozen pipeline still slices the CORRECT source text, so a model whose own
   quote or value was wrong gets full credit. As an RL reward that would never punish an
   unfaithful quote. Patched: for those statuses the model's own text is the value.
2. Edge quotation marks. norm_value maps curly quotes to straight ones but does not strip them at
   the edges, so a reading wrapped in quotes is not credited. Patched: strip " at the edges too.

Usage: `with patched(): ...` around calls into score / rl_attack_scorer; outside the block the
frozen behaviour is unchanged.
"""
from __future__ import annotations

import contextlib
import re
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
import score as S  # noqa: E402

GATED = {"fuzzy", "silent_correction", "case_variant"}


def norm_value_patched(s: str) -> str:
    s = unicodedata.normalize("NFKC", s or "").translate(S._TYPO)
    s = S._MD.sub("", s)
    s = S._HYPH.sub("", s)
    return re.sub(r"\s+", " ", s).strip(' .,;:()[]"').casefold()


@contextlib.contextmanager
def patched():
    old = S.norm_value
    S.norm_value = norm_value_patched
    try:
        yield
    finally:
        S.norm_value = old


def gate_value(condition: str, status: str, sliced: str | None, model_text: str | None) -> str | None:
    """The value the patched reward uses for one prediction."""
    if condition in ("G0", "G1") and status in GATED:
        return model_text
    return sliced
