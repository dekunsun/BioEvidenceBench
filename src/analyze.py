"""Run every pre-registered analysis and write one report folder.

    python src/analyze.py --name dev_p3 --split dev \
        --llm <opus run> [--llm2 <second model's run>] --rule <rule baseline run> \
        --gold gold/gold_mentions_gloria.csv [--issues gold/annotation_issues_gloria.csv]

For --split test the runs must have been unsealed first (src/unseal.py); this script reads
only <split>_mentions.csv and <split>_outputs.jsonl and never a sealed file.

Writes results/analysis_<name>/:
  scores.csv                per run x book x version x condition x field (+ ALL_PRIMARY)
  comparisons.csv           paired page-bootstrap differences with the pre-registered verdicts
  stage_loss.csv            where gold mentions are lost: OCR, extraction, value
  entity_span_cer.csv       each gold mention as it appears in each OCR version
  evidence.csv              RQ3 counters (unsupported outputs, wrong line, type check)
  outcomes.csv              one status per request
  rq4_flags.csv, rq4_summary.csv, risk_coverage.csv   (only with --llm2)
  discrepancies.csv         every false positive and false negative, for the error analysis
  evaluation_settings.json  hashes of the gold file and every input, code commit, rules
  REPORT.md
"""
from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime, timezone

import pandas as pd

import analysis as an
from common import DATA, ROOT
from locate import FUZZY_MIN
from score import LEVELS, PRIMARY_FIELDS, RESULTS, SEPARATE_FIELDS, entity_span_cer, score_run_detail


def git_state() -> dict:
    def run(*args):
        return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    return {"commit": run("rev-parse", "HEAD"), "uncommitted_changes": bool(run("status", "--porcelain"))}


def md(df: pd.DataFrame) -> str:
    return df.to_markdown(index=False) if len(df) else "_(no rows)_"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--name", required=True)
    ap.add_argument("--split", choices=["dev", "test"], required=True)
    ap.add_argument("--llm", required=True, help="run id of the main LLM")
    ap.add_argument("--llm2", help="run id of the second LLM (RQ4)")
    ap.add_argument("--rule", help="run id of the rule baseline")
    ap.add_argument("--gold", required=True)
    ap.add_argument("--issues")
    a = ap.parse_args()

    out = RESULTS / f"analysis_{a.name}"
    out.mkdir(exist_ok=True)
    runs = [r for r in (a.llm, a.llm2, a.rule) if r]
    detail = {r: score_run_detail(r, a.gold, a.split, a.issues) for r in runs}
    scores = pd.concat([d["summary"] for d in detail.values()], ignore_index=True)
    by_page = pd.concat([d["by_page"] for d in detail.values()], ignore_index=True)
    gold_out = pd.concat([d["gold_outcomes"] for d in detail.values()], ignore_index=True)
    pred_out = pd.concat([d["pred_outcomes"] for d in detail.values()], ignore_index=True)
    pages = pd.read_csv(DATA / "sample_split.csv").query("split == @a.split")

    span_cer = entity_span_cer(a.gold, a.split)
    comparisons = an.planned_comparisons(by_page, a.llm, a.rule)
    stages = an.stage_loss(gold_out, span_cer)
    evidence = pd.concat([an.evidence_counters(an.read_mentions(r, a.split), pages).assign(run=r)
                          for r in runs], ignore_index=True)
    outcomes = pd.concat([an.outcome_table(r, a.split) for r in runs], ignore_index=True)

    # Every false positive and false negative, as input for the error analysis (section 5).
    fn = gold_out[(~gold_out.value_ok) & (gold_out.adjudication != "ambiguous")].assign(kind="false_negative")
    fp = pred_out[pred_out.outcome.str.startswith("fp_")].assign(kind="false_positive")
    disc = pd.concat([
        fn.rename(columns={"text": "gold_text"})[["kind", "run", "page_id", "book", "version", "condition",
                                                  "field", "gold_text", "pred_value", "pred_status", "lenient"]],
        fp.rename(columns={"value": "pred_value", "status": "pred_status"})[
            ["kind", "run", "page_id", "book", "version", "condition", "field", "gold_text", "pred_value",
             "pred_status", "outcome"]]], ignore_index=True)
    disc["error_group"] = ""     # for Gloria: OCR-sensitive / extraction / ambiguous (one or more)
    disc["error_note"] = ""

    for name, df in (("scores", scores), ("comparisons", comparisons), ("stage_loss", stages),
                     ("entity_span_cer", span_cer), ("evidence", evidence), ("outcomes", outcomes),
                     ("discrepancies", disc)):
        df.to_csv(out / f"{name}.csv", index=False)

    rq4 = cov = None
    if a.llm2:
        pa = pred_out[(pred_out.run == a.llm) & (pred_out.condition == "G1")]
        pb = pred_out[(pred_out.run == a.llm2) & (pred_out.condition == "G1")]
        flags = an.flag_auto_accept(pa, pb)
        ga = gold_out[(gold_out.run == a.llm) & (gold_out.condition == "G1")]
        gb = gold_out[(gold_out.run == a.llm2) & (gold_out.condition == "G1")]
        rq4, cov = an.rq4_summary(flags, ga, gb), an.risk_coverage(flags)
        flags.to_csv(out / "rq4_flags.csv", index=False)
        rq4.to_csv(out / "rq4_summary.csv", index=False)
        cov.to_csv(out / "risk_coverage.csv", index=False)

    cfgs = {r: json.loads((RESULTS / r / "config.json").read_text()) for r in runs}
    gold_df = pd.read_csv(a.gold, dtype=str, keep_default_na=False)
    settings = {
        "written_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "split": a.split, "code": git_state(),
        "gold": {"file": a.gold, "sha256": an.sha256_file(a.gold), "rows": len(gold_df),
                 "guide_versions": sorted(set(gold_df.get("guide_version", [])))},
        "issues": {"file": a.issues, "sha256": an.sha256_file(a.issues)} if a.issues else None,
        "runs": {r: {"role": "llm" if r == a.llm else "llm2" if r == a.llm2 else "rule",
                     "model": cfgs[r].get("model"), "prompt_version": cfgs[r].get("prompt_version"),
                     "effort": cfgs[r].get("effort"),
                     "mentions_sha256": an.sha256_file(RESULTS / r / f"{a.split}_mentions.csv")} for r in runs},
        "matching": {"levels": list(LEVELS), "assignment": "optimal one-to-one per field (linear_sum_assignment)",
                     "primary_fields": PRIMARY_FIELDS, "separate_fields": SEPARATE_FIELDS,
                     "primary_level": "value", "locate_fuzzy_threshold": FUZZY_MIN,
                     "ambiguous_gold": "optional: no credit, no penalty",
                     "issue_regions": "predictions touching them are set aside"},
        "bootstrap": {"resamples": an.N_BOOT, "seed": an.SEED, "unit": "page", "interval": "percentile 95%",
                      "paired_for_differences": True},
        "rq3_unsupported": {k: sorted(v) for k, v in an.UNSUPPORTED.items()},
        "rq4_flag": "second model extracts the same span (lenient) AND status in exact/cross_line AND type_check",
    }
    (out / "evaluation_settings.json").write_text(json.dumps(settings, indent=2), encoding="utf-8")

    prim = scores[scores.field == "ALL_PRIMARY"]
    counts = scores[(scores.run == a.llm) & (scores.version == "expert") & (scores.condition == "G1")][
        ["book", "field", "pages", "gold", "gold_ambiguous_excluded", "too_few_to_compare"]]
    lines = [
        f"# Analysis report: {a.name} ({a.split.upper()} pages)", "",
        f"Gold: `{a.gold}` ({settings['gold']['sha256'][:12]}…), guide {settings['gold']['guide_versions']}.",
        f"Code commit `{settings['code']['commit'][:10]}`"
        + (" **with uncommitted changes**" if settings["code"]["uncommitted_changes"] else "") + ".",
        "Runs: " + "; ".join(f"`{r}` ({v['role']}, {v['model']}, prompt {v['prompt_version']})"
                             for r, v in settings["runs"].items()) + ".",
        "" if a.split == "test" else "\n**Dev pages are not blind. These numbers are for tuning, not results.**", "",
        "## Sample behind every number", "", md(counts), "",
        "## Scores, primary fields together (value level is the primary metric)", "",
        md(prim[["run", "book", "version", "condition", "gold", "pred", "value_P", "value_R", "value_F1",
                 "value_F1_lo", "value_F1_hi", "lenient_F1", "exact_F1", "unaligned"]]), "",
        "Per field (including `vernacular`, scored apart): `scores.csv`.", "",
        "## Where gold mentions are lost (main LLM, with evidence)", "",
        md(stages[(stages.run == a.llm) & (stages.condition == "G1") & (stages.field == "ALL_PRIMARY")][
            ["book", "version", "gold", "lost_at_ocr", "of_which_still_found", "lost_at_extraction",
             "lost_at_value", "kept", "kept_share"]]), "",
        "## Pre-registered comparisons (paired page bootstrap)", "",
        "Shown: RQ1, RQ3, and RQ2 on the expert text. A is the arm the hypothesis expects to be better;",
        "`verdict` compares the 95% interval of A - B with the rule written in advance.", "",
        md(comparisons[comparisons.preregistered
                       & (comparisons.rq.isin(["RQ1", "RQ3"]) | comparisons.comparison.str.endswith("expert"))][
            ["rq", "comparison", "book", "field", "metric", "pages", "a", "b", "diff", "lo", "hi", "rule",
             "verdict"]]), "",
        "RQ2 on the other text versions, descriptive comparisons and other fields: `comparisons.csv`.", "",
        "## Evidence (RQ3)", "",
        md(evidence[evidence.run == a.llm][["book", "version", "condition", "outputs", "unsupported",
                                            "unsupported_rate", "wrong_line", "type_check_failed",
                                            "copied_line_label"]]), "",
        "## Request outcomes", "",
        md(outcomes.groupby(["run", "outcome"]).size().reset_index(name="requests")), "",
    ]
    if rq4 is not None:
        lines += ["## Shadow evaluation (RQ4): flagged = proposed auto-accept, nothing is skipped", "",
                  md(rq4), "", "### Risk and coverage", "", md(cov), ""]
    lines += [f"False positives and negatives for the error analysis: `discrepancies.csv` ({len(disc)} rows).", ""]
    (out / "REPORT.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
