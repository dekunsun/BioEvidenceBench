"""Task B step 4: agreement between Gloria's and Claude's alignment verdicts on 30 round-2 pairs.

    python src/rl_task_b_audit_agreement.py

Reads Gloria's workbook as delivered (build/received/2026-11-21_audit_gloria.xlsx, never edited)
and Claude's verdicts (build/audit_sample.csv). B004 and B006 are left out of the agreement figure:
Claude named its verdict on them in chat before Gloria checked them. Writes build/AGREEMENT.md and
build/agreement.csv. No model is called.
"""
from __future__ import annotations

import pandas as pd

from common import ROOT

B = ROOT / "rl" / "env" / "task_b_ocr_repair" / "build"
GLORIA = B / "received" / "2026-11-21_audit_gloria.xlsx"
NOT_INDEPENDENT = {"B004", "B006"}
LABELS = ["yes", "partly", "no"]


def kappa(a: pd.Series, b: pd.Series) -> float:
    """Cohen's kappa for two labellers on the same items."""
    po = (a == b).mean()
    pe = sum((a == k).mean() * (b == k).mean() for k in set(a) | set(b))
    return (po - pe) / (1 - pe) if pe < 1 else 1.0


def main() -> None:
    g = pd.read_excel(GLORIA, sheet_name="pairs")
    c = pd.read_csv(B / "audit_sample.csv")
    m = g[["audit_id", "book", "aligned_correctly (yes/no/partly)", "failure_type", "note"]].rename(
        columns={"aligned_correctly (yes/no/partly)": "gloria", "failure_type": "gloria_type", "note": "gloria_note"}
    ).merge(c[["audit_id", "sim_bucket", "usable", "set_aside", "claude_verdict", "claude_failure_type", "claude_note",
               "input", "target"]], on="audit_id")
    m["gloria"] = m.gloria.str.strip().str.lower()
    m["independent"] = ~m.audit_id.isin(NOT_INDEPENDENT)
    m["agree"] = m.gloria == m.claude_verdict
    m.to_csv(B / "agreement.csv", index=False)

    i = m[m.independent]
    same_g, same_c = i.gloria != "no", i.claude_verdict != "no"         # "is it the same printed line?"
    acc = m[m.usable.astype(bool)]
    table = pd.crosstab(i.claude_verdict, i.gloria).reindex(index=LABELS, columns=LABELS, fill_value=0)
    dis = i[~i.agree]
    lines = [
        "# Task B step 4: alignment audit agreement (Gloria × Claude)", "",
        f"Gloria checked 30 round-2 pairs (`received/2026-11-21_audit_gloria.xlsx`, archived unchanged) without "
        f"seeing the build's decision or Claude's verdict. B004 and B006 are left out: Claude had named its "
        f"verdict on them in chat first. **{len(i)} independent pairs.**", "",
        "| Measure | Value |", "|---|---|",
        f"| Exact agreement, three labels | {i.agree.sum()} / {len(i)} ({i.agree.mean():.0%}) |",
        f"| Cohen's kappa, three labels | {kappa(i.gloria, i.claude_verdict):.2f} |",
        f"| Agreement on \"same printed line?\" (yes or partly vs no) | {(same_g == same_c).sum()} / {len(i)} "
        f"({(same_g == same_c).mean():.0%}) |",
        f"| Cohen's kappa, same line | {kappa(same_g, same_c):.2f} |", "",
        "Rows Claude, columns Gloria:", "", table.to_markdown(), "",
        "## Disagreements", "",
        "| Pair | Claude | Gloria | Usable now | Reason |", "|---|---|---|---|---|"]
    for r in dis.itertuples():
        lines.append(f"| {r.audit_id} | {r.claude_verdict} | {r.gloria} | {'yes' if r.usable else 'no: ' + str(r.set_aside)} "
                     f"| {r.claude_note if pd.notna(r.claude_note) else ''} |")
    lines += ["", "## Pairs the build uses", "",
              f"Of the 30 pairs, {len(acc)} are usable in the current build; Gloria marked "
              f"{(acc.gloria == 'no').sum()} of them `no` and Claude {(acc.claude_verdict == 'no').sum()}.", ""]
    lines += ["## Reading the disagreements", "",
              "- **Five are one definition** (B022, B049, B064, B069, B075): index and list lines whose OCR "
              "lost the leader dots or the page reference. Claude counted words missing from the OCR as "
              "`partly`; Gloria judged them the same printed line with OCR losses, which is what the question "
              "asked (\"is the input the OCR of this line?\"). The sheet's wording (\"缺词\" under partly) "
              "allowed both. From now on: `partly` means a pairing problem (words from another line or column, "
              "or only part of the line paired); losses inside the right line are `yes`. All five were already "
              "rejected by the build, and leader-dot lines are now set aside, so no usable line changes.",
              "- **B045 is Claude's error.** Gloria checked the scan: `DeBariana SC re` is the OCR of "
              "`7. Pariana Cl.` (`ariana`), with no sign of another line. Claude had grouped it with the "
              "garbage lines below similarity 0.3 without looking at the scan. The pairing is right; the build "
              "still rejects it (similarity 0.29), which is acceptable for training since the input cannot "
              "yield the target, but it is a false negative of the similarity floor, not a wrong pair.",
              "- Claude's verdicts in `audit_sample.csv` are left as written; this file is the adjudication.", ""]
    (B / "AGREEMENT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
