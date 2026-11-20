"""docs/eval_settings.md: one row per model run, generated from the run records; never edited by hand.

    python src/make_eval_settings.py

Reads results/<run>/config.json and cost.json (whichever exist) for every run folder, plus the
LLM-linker spend in results/linking_variants*/config.json. A field missing from a record is shown
as "—" rather than filled from a default. The role column says how a run may be used:
pre-registered (frozen test run), dev (tuning; not blind), superseded (an earlier prompt),
exploratory (decided after unsealing, DEVIATIONS.md).
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from common import ROOT

RES = ROOT / "results"
OUT = ROOT / "docs" / "eval_settings.md"
PRE = {"20261119-2052_claude-opus-5-5_test_batch", "20261119-2052_gemini-4-carbon_test_sync",
       "20261118-2102_rules-gnfinder-v1.4.0_all"}


def role(run: str, cfg: dict) -> str:
    if run in PRE:
        return "pre-registered"
    if run.startswith("20261118-08"):
        return "superseded (p1/p2)"
    if "_dev" in run:
        return "dev"
    return "exploratory"


def short(xs) -> str:
    if xs in (None, "", []):
        return "—"
    if isinstance(xs, list):
        xs = [str(x).replace("modern_", "") for x in xs]
        return ", ".join(xs) if len(xs) <= 4 else f"{len(xs)} versions"
    return str(xs)


def main() -> None:
    rows = []
    for d in sorted(RES.glob("2026*")):
        cfg, cost = {}, {}
        if (d / "config.json").exists():
            cfg = json.loads((d / "config.json").read_text())
        if (d / "cost.json").exists():
            cost = json.loads((d / "cost.json").read_text())
        rec = {**cfg, **cost}
        model = rec.get("model") or ("gnfinder v1.4.0 + regex" if "rules" in d.name else "—")
        mode = rec.get("mode") or ("batch" if rec.get("batch") is True else "sync" if rec.get("batch") is False
                                   else "sync" if "explore" in d.name else "—")
        conds = rec.get("conditions") or rec.get("condition")
        vers = rec.get("versions") or rec.get("version")
        tok = rec.get("tokens") or {}
        stops = rec.get("stop_reasons") or {}
        rows.append({
            "Run": d.name, "Role": role(d.name, rec), "Model": model,
            "Provider": rec.get("provider") or ("anthropic" if str(model).startswith("claude") else
                                               "gemini" if "gemini" in str(model) else "local"),
            "Mode": mode, "Effort": rec.get("effort", "—"),
            "Prompt": rec.get("prompt_version") or rec.get("base_prompt_version") or "—",
            "Condition": short(conds), "Text versions": short(vers),
            "Pages": rec.get("pages") if isinstance(rec.get("pages"), (str, int)) else "—",
            "Requests": rec.get("requests") or rec.get("n_requests") or "—",
            "Stop reasons": ", ".join(f"{k} {v}" for k, v in stops.items()) or "—",
            "Errors": rec.get("errors", rec.get("unparsed", "—")),
            "Input tokens": f"{tok['input_tokens']:,}" if tok.get("input_tokens") else "—",
            "Output tokens": f"{tok['output_tokens']:,}" if tok.get("output_tokens") else "—",
            "Spend (US$)": round(rec["usd_total"], 2) if "usd_total" in rec else 0.0 if "rules" in d.name else "—",
        })
    for d in sorted(RES.glob("linking_variants*")):
        cfg = json.loads((d / "config.json").read_text())
        rows.append({"Run": d.name, "Role": "exploratory", "Model": cfg.get("llm_model", "—"),
                     "Provider": "anthropic", "Mode": "sync", "Effort": "—", "Prompt": "LLM linker",
                     "Condition": "linking", "Text versions": "expert, dots-mocr, legacy", "Pages": "test (Butler)",
                     "Requests": "—", "Stop reasons": "—", "Errors": "—", "Input tokens": "—",
                     "Output tokens": "—", "Spend (US$)": round(cfg.get("new_llm_usd", 0.0), 2)})
    t = pd.DataFrame(rows)
    spend = pd.to_numeric(t["Spend (US$)"], errors="coerce").fillna(0)
    by_role = t.assign(s=spend).groupby("Role").s.sum().round(2)
    by_prov = t.assign(s=spend).groupby("Provider").s.sum().round(2)
    lines = [
        "# BioEvidenceBench: evaluation settings", "",
        "One row per run folder, generated from the run records by `src/make_eval_settings.py`; never edited "
        "by hand. A dash means the record does not hold that field. Results: [results](results.md). Plan: "
        "[`PREREGISTRATION.md`](../PREREGISTRATION.md); later changes: [`DEVIATIONS.md`](../DEVIATIONS.md).", "",
        "**Common to every LLM run.** The model never rewrites source text: lines are numbered, the model returns "
        "values (G0) or a line plus a verbatim quote (G1, G2), and code slices or checks against the source. "
        "Temperature is never set, so each provider's default applies; Claude runs use adaptive thinking with the "
        "`effort` shown; Gemini runs use the model's default thinking. Every request and raw response is saved in "
        "the run folder, with the prompt, the input text's SHA-256 and the timestamp. Test-page outputs of the "
        "pre-registered runs were sealed until the freeze. Batch requests cost half the list price.", "",
        "**Conditions.** G0 values only; G1 line + verbatim quote (the frozen condition); G1F the frozen G1 prompt "
        "word for word on new pages; G2 verbatim quote + a repaired reading; V1 page image only; V2 image + OCR text; "
        "V3 image only, with a box per mention.", "",
        "**Spend by role (US$):** " + "; ".join(f"{k} {v:.2f}" for k, v in by_role.items()) +
        f". **By provider:** " + "; ".join(f"{k} {v:.2f}" for k, v in by_prov.items()) +
        f". **Total:** {spend.sum():.2f}. Estimated from saved token counts at list prices; dropped connections that "
        "may have been billed (about $0.15 on one Gemini run) are not included.", "",
        t.to_markdown(index=False), ""]
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"{len(t)} rows -> {OUT}; total ${spend.sum():.2f}")
    print(by_role.to_string()); print(by_prov.to_string())


if __name__ == "__main__":
    main()
