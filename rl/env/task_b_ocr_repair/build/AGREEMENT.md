# Task B step 4: alignment audit agreement (Gloria × Claude)

Gloria checked 30 round-2 pairs (`received/2026-11-21_audit_gloria.xlsx`, archived unchanged) without seeing the build's decision or Claude's verdict. B004 and B006 are left out: Claude had named its verdict on them in chat first. **28 independent pairs.**

| Measure | Value |
|---|---|
| Exact agreement, three labels | 22 / 28 (79%) |
| Cohen's kappa, three labels | 0.57 |
| Agreement on "same printed line?" (yes or partly vs no) | 27 / 28 (96%) |
| Cohen's kappa, same line | 0.90 |

Rows Claude, columns Gloria:

| claude_verdict   |   yes |   partly |   no |
|:-----------------|------:|---------:|-----:|
| yes              |    16 |        0 |    0 |
| partly           |     5 |        0 |    0 |
| no               |     1 |        0 |    6 |

## Disagreements

| Pair | Claude | Gloria | Usable now | Reason |
|---|---|---|---|---|
| B022 | partly | yes | no: coverage 0.62 | Reeve index; rejected by coverage |
| B045 | no | yes | no: coverage 0.46; span ratio 0.54; similarity 0.29 | below 0.3: wrong or garbage; rejection correct |
| B049 | partly | yes | no: coverage 0.68 | index line: OCR lacks leaders, column or page number; rejected by coverage (right decision for a target the OCR does not contain) |
| B064 | partly | yes | no: coverage 0.78 | Reeve index; rejected by coverage |
| B069 | partly | yes | no: coverage 0.82 | Reeve index; rejected by coverage |
| B075 | partly | yes | no: coverage 0.74 | Trudy list; right entry, leaders/marks not in OCR; rejected |

## Pairs the build uses

Of the 30 pairs, 13 are usable in the current build; Gloria marked 0 of them `no` and Claude 0.

## Reading the disagreements

- **Five are one definition** (B022, B049, B064, B069, B075): index and list lines whose OCR lost the leader dots or the page reference. Claude counted words missing from the OCR as `partly`; Gloria judged them the same printed line with OCR losses, which is what the question asked ("is the input the OCR of this line?"). The sheet's wording ("缺词" under partly) allowed both. From now on: `partly` means a pairing problem (words from another line or column, or only part of the line paired); losses inside the right line are `yes`. All five were already rejected by the build, and leader-dot lines are now set aside, so no usable line changes.
- **B045 is Claude's error.** Gloria checked the scan: `DeBariana SC re` is the OCR of `7. Pariana Cl.` (`ariana`), with no sign of another line. Claude had grouped it with the garbage lines below similarity 0.3 without looking at the scan. The pairing is right; the build still rejects it (similarity 0.29), which is acceptable for training since the input cannot yield the target, but it is a false negative of the similarity floor, not a wrong pair.
- Claude's verdicts in `audit_sample.csv` are left as written; this file is the adjudication.

