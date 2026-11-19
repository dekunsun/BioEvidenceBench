# Analysis report: dev_p4_rq4 (DEV pages)

Gold: `gold/gold_mentions_gloria.csv` (5a3e85b6dd32…), guide ['v0.5', 'v0.6'].
Code commit `6d0fb251a6` **with uncommitted changes**.
Runs: `20261119-0113_claude-opus-5-5_dev_p4_r1` (llm, claude-opus-5-5, prompt p4-guide-v0.6); `20261119-0221_gemini-4-carbon_dev_p4_r1` (llm2, gemini-4-carbon, prompt p4-guide-v0.6); `20261118-2102_rules-gnfinder-v1.4.0_all` (rule, rules + gnfinder v1.4.0, prompt None).

**Dev pages are not blind. These numbers are for tuning, not results.**

## Sample behind every number

| book   | field       |   pages |   gold |   gold_ambiguous_excluded | too_few_to_compare   |
|:-------|:------------|--------:|-------:|--------------------------:|:---------------------|
| Butler | ALL_PRIMARY |       3 |     63 |                         0 | False                |
| Butler | date        |       3 |      2 |                         0 | True                 |
| Butler | institution |       3 |      0 |                         0 | True                 |
| Butler | locality    |       3 |     37 |                         0 | False                |
| Butler | person      |       3 |     11 |                         0 | False                |
| Butler | taxon       |       3 |     13 |                         0 | False                |
| Butler | vernacular  |       3 |     41 |                         0 | False                |
| Reeve  | ALL_PRIMARY |       3 |     70 |                         0 | False                |
| Reeve  | date        |       3 |      0 |                         0 | True                 |
| Reeve  | institution |       3 |     11 |                         0 | False                |
| Reeve  | locality    |       3 |     12 |                         0 | False                |
| Reeve  | person      |       3 |     22 |                         0 | False                |
| Reeve  | taxon       |       3 |     25 |                         0 | False                |
| Reeve  | vernacular  |       3 |     12 |                         0 | False                |

## Scores, primary fields together (value level is the primary metric)

| run                                     | book   | version                | condition   |   gold |   pred |   value_P |   value_R |   value_F1 |   value_F1_lo |   value_F1_hi |   lenient_F1 |   exact_F1 |   unaligned |
|:----------------------------------------|:-------|:-----------------------|:------------|-------:|-------:|----------:|----------:|-----------:|--------------:|--------------:|-------------:|-----------:|------------:|
| 20261119-0113_claude-opus-5-5_dev_p4_r1 | Butler | expert                 | G0          |     63 |     63 |     1     |     1     |      1     |         1     |         1     |        1     |      1     |           0 |
| 20261119-0113_claude-opus-5-5_dev_p4_r1 | Butler | expert                 | G1          |     63 |     63 |     1     |     1     |      1     |         1     |         1     |        1     |      1     |           0 |
| 20261119-0113_claude-opus-5-5_dev_p4_r1 | Butler | legacy                 | G0          |     63 |     63 |     0.794 |     0.794 |      0.794 |         0.727 |         0.873 |        1     |      1     |           0 |
| 20261119-0113_claude-opus-5-5_dev_p4_r1 | Butler | legacy                 | G1          |     63 |     63 |     0.794 |     0.794 |      0.794 |         0.727 |         1     |        1     |      1     |           0 |
| 20261119-0113_claude-opus-5-5_dev_p4_r1 | Butler | modern_dots-mocr       | G0          |     63 |     63 |     0.968 |     0.968 |      0.968 |         0.957 |         1     |        1     |      0.984 |           0 |
| 20261119-0113_claude-opus-5-5_dev_p4_r1 | Butler | modern_dots-mocr       | G1          |     63 |     63 |     0.984 |     0.984 |      0.984 |         0.978 |         1     |        1     |      1     |           0 |
| 20261119-0113_claude-opus-5-5_dev_p4_r1 | Butler | modern_dots-mocr_plain | G0          |     63 |     63 |     0.984 |     0.984 |      0.984 |         0.978 |         1     |        1     |      1     |           0 |
| 20261119-0113_claude-opus-5-5_dev_p4_r1 | Butler | modern_dots-mocr_plain | G1          |     63 |     63 |     0.984 |     0.984 |      0.984 |         0.978 |         1     |        1     |      1     |           0 |
| 20261119-0113_claude-opus-5-5_dev_p4_r1 | Reeve  | expert                 | G0          |     70 |     70 |     1     |     1     |      1     |         1     |         1     |        1     |      1     |           0 |
| 20261119-0113_claude-opus-5-5_dev_p4_r1 | Reeve  | expert                 | G1          |     70 |     70 |     1     |     1     |      1     |         1     |         1     |        1     |      1     |           0 |
| 20261119-0113_claude-opus-5-5_dev_p4_r1 | Reeve  | legacy                 | G0          |     70 |     70 |     0.714 |     0.714 |      0.714 |         0.579 |         0.778 |        1     |      0.971 |           0 |
| 20261119-0113_claude-opus-5-5_dev_p4_r1 | Reeve  | legacy                 | G1          |     70 |     70 |     0.714 |     0.714 |      0.714 |         0.579 |         0.778 |        1     |      0.971 |           0 |
| 20261119-0113_claude-opus-5-5_dev_p4_r1 | Reeve  | modern_dots-mocr       | G0          |     70 |     70 |     0.971 |     0.971 |      0.971 |         0.933 |         1     |        1     |      0.986 |           0 |
| 20261119-0113_claude-opus-5-5_dev_p4_r1 | Reeve  | modern_dots-mocr       | G1          |     70 |     71 |     0.958 |     0.971 |      0.965 |         0.933 |         1     |        0.993 |      0.979 |           0 |
| 20261119-0113_claude-opus-5-5_dev_p4_r1 | Reeve  | modern_dots-mocr_plain | G0          |     70 |     70 |     0.986 |     0.986 |      0.986 |         0.933 |         1     |        1     |      1     |           0 |
| 20261119-0113_claude-opus-5-5_dev_p4_r1 | Reeve  | modern_dots-mocr_plain | G1          |     70 |     70 |     0.986 |     0.986 |      0.986 |         0.933 |         1     |        1     |      0.971 |           0 |
| 20261119-0221_gemini-4-carbon_dev_p4_r1 | Butler | expert                 | G0          |     63 |     63 |     1     |     1     |      1     |         1     |         1     |        1     |      1     |           0 |
| 20261119-0221_gemini-4-carbon_dev_p4_r1 | Butler | expert                 | G1          |     63 |     63 |     1     |     1     |      1     |         1     |         1     |        1     |      1     |           0 |
| 20261119-0221_gemini-4-carbon_dev_p4_r1 | Butler | legacy                 | G0          |     63 |     63 |     0.794 |     0.794 |      0.794 |         0.727 |         0.873 |        1     |      1     |           0 |
| 20261119-0221_gemini-4-carbon_dev_p4_r1 | Butler | legacy                 | G1          |     63 |     57 |     0.772 |     0.698 |      0.733 |         0.471 |         0.783 |        0.95  |      0.95  |           0 |
| 20261119-0221_gemini-4-carbon_dev_p4_r1 | Butler | modern_dots-mocr       | G0          |     63 |     63 |     0.984 |     0.984 |      0.984 |         0.978 |         1     |        1     |      1     |           0 |
| 20261119-0221_gemini-4-carbon_dev_p4_r1 | Butler | modern_dots-mocr       | G1          |     63 |     63 |     0.984 |     0.984 |      0.984 |         0.978 |         1     |        1     |      1     |           0 |
| 20261119-0221_gemini-4-carbon_dev_p4_r1 | Butler | modern_dots-mocr_plain | G0          |     63 |     63 |     0.984 |     0.984 |      0.984 |         0.978 |         1     |        1     |      1     |           0 |
| 20261119-0221_gemini-4-carbon_dev_p4_r1 | Butler | modern_dots-mocr_plain | G1          |     63 |     63 |     0.984 |     0.984 |      0.984 |         0.978 |         1     |        1     |      1     |           0 |
| 20261119-0221_gemini-4-carbon_dev_p4_r1 | Reeve  | expert                 | G0          |     70 |     70 |     1     |     1     |      1     |         1     |         1     |        1     |      1     |           0 |
| 20261119-0221_gemini-4-carbon_dev_p4_r1 | Reeve  | expert                 | G1          |     70 |     70 |     1     |     1     |      1     |         1     |         1     |        1     |      1     |           0 |
| 20261119-0221_gemini-4-carbon_dev_p4_r1 | Reeve  | legacy                 | G0          |     70 |     51 |     0.765 |     0.557 |      0.645 |         0.324 |         0.778 |        0.843 |      0.843 |           0 |
| 20261119-0221_gemini-4-carbon_dev_p4_r1 | Reeve  | legacy                 | G1          |     70 |     51 |     0.765 |     0.557 |      0.645 |         0.324 |         0.778 |        0.843 |      0.843 |           0 |
| 20261119-0221_gemini-4-carbon_dev_p4_r1 | Reeve  | modern_dots-mocr       | G0          |     70 |     70 |     0.971 |     0.971 |      0.971 |         0.933 |         1     |        1     |      0.986 |           0 |
| 20261119-0221_gemini-4-carbon_dev_p4_r1 | Reeve  | modern_dots-mocr       | G1          |     70 |     70 |     0.986 |     0.986 |      0.986 |         0.933 |         1     |        1     |      1     |           0 |
| 20261119-0221_gemini-4-carbon_dev_p4_r1 | Reeve  | modern_dots-mocr_plain | G0          |     70 |     34 |     0.971 |     0.471 |      0.635 |         0.275 |         1     |        0.654 |      0.654 |           0 |
| 20261119-0221_gemini-4-carbon_dev_p4_r1 | Reeve  | modern_dots-mocr_plain | G1          |     70 |     70 |     0.986 |     0.986 |      0.986 |         0.933 |         1     |        1     |      1     |           0 |
| 20261118-2102_rules-gnfinder-v1.4.0_all | Butler | expert                 | RULE        |     63 |     26 |     0.769 |     0.317 |      0.449 |         0.222 |         0.531 |        0.449 |      0.449 |           0 |
| 20261118-2102_rules-gnfinder-v1.4.0_all | Butler | legacy                 | RULE        |     63 |     20 |     0.7   |     0.222 |      0.337 |         0.235 |         0.373 |        0.361 |      0.337 |           0 |
| 20261118-2102_rules-gnfinder-v1.4.0_all | Butler | modern_dots-mocr       | RULE        |     63 |     25 |     0.76  |     0.302 |      0.432 |         0.222 |         0.508 |        0.432 |      0.432 |           0 |
| 20261118-2102_rules-gnfinder-v1.4.0_all | Butler | modern_dots-mocr_plain | RULE        |     63 |     25 |     0.76  |     0.302 |      0.432 |         0.222 |         0.508 |        0.432 |      0.432 |           0 |
| 20261118-2102_rules-gnfinder-v1.4.0_all | Reeve  | expert                 | RULE        |     70 |     75 |     0.413 |     0.443 |      0.428 |         0.385 |         0.471 |        0.648 |      0.4   |           0 |
| 20261118-2102_rules-gnfinder-v1.4.0_all | Reeve  | legacy                 | RULE        |     70 |     52 |     0.442 |     0.329 |      0.377 |         0.333 |         0.393 |        0.607 |      0.459 |           0 |
| 20261118-2102_rules-gnfinder-v1.4.0_all | Reeve  | modern_dots-mocr       | RULE        |     70 |     69 |     0.435 |     0.429 |      0.432 |         0.381 |         0.48  |        0.619 |      0.403 |           0 |
| 20261118-2102_rules-gnfinder-v1.4.0_all | Reeve  | modern_dots-mocr_plain | RULE        |     70 |     73 |     0.452 |     0.471 |      0.462 |         0.44  |         0.478 |        0.657 |      0.434 |           0 |

Per field (including `vernacular`, scored apart): `scores.csv`.

## Where gold mentions are lost (main LLM, with evidence)

| book   | version                |   gold |   lost_at_ocr |   of_which_still_found |   lost_at_extraction |   lost_at_value |   kept |   kept_share |
|:-------|:-----------------------|-------:|--------------:|-----------------------:|---------------------:|----------------:|-------:|-------------:|
| Butler | expert                 |     63 |             0 |                      0 |                    0 |               0 |     63 |        1     |
| Butler | legacy                 |     63 |            12 |                     12 |                    0 |               1 |     50 |        0.794 |
| Butler | modern_dots-mocr       |     63 |             1 |                      1 |                    0 |               0 |     62 |        0.984 |
| Butler | modern_dots-mocr_plain |     63 |             1 |                      1 |                    0 |               0 |     62 |        0.984 |
| Reeve  | expert                 |     70 |             0 |                      0 |                    0 |               0 |     70 |        1     |
| Reeve  | legacy                 |     70 |            20 |                     20 |                    0 |               0 |     50 |        0.714 |
| Reeve  | modern_dots-mocr       |     70 |             1 |                      1 |                    0 |               1 |     68 |        0.971 |
| Reeve  | modern_dots-mocr_plain |     70 |             1 |                      1 |                    0 |               0 |     69 |        0.986 |

## Pre-registered comparisons (paired page bootstrap)

Shown: RQ1, RQ3, and RQ2 on the expert text. A is the arm the hypothesis expects to be better;
`verdict` compares the 95% interval of A - B with the rule written in advance.

| rq   | comparison                                                        | book   | field       | metric    |   pages |       a |       b |    diff |      lo |      hi | rule               | verdict      |
|:-----|:------------------------------------------------------------------|:-------|:------------|:----------|--------:|--------:|--------:|--------:|--------:|--------:|:-------------------|:-------------|
| RQ1  | modern OCR vs legacy OCR                                          | Reeve  | ALL_PRIMARY | value F1  |       3 |   0.965 |   0.714 |   0.25  |   0.181 |   0.421 | at_least 0.1       | supports     |
| RQ1  | expert vs modern OCR                                              | Reeve  | ALL_PRIMARY | value F1  |       3 |   1     |   0.965 |   0.035 |   0     |   0.067 | less_than 0.05     | inconclusive |
| RQ3  | recall with evidence (G1) vs without (G0), expert                 | Butler | ALL_PRIMARY | lenient R |       3 |   1     |   1     |   0     |   0     |   0     | greater_than -0.05 | supports     |
| RQ3  | recall with evidence (G1) vs without (G0), expert                 | Reeve  | ALL_PRIMARY | lenient R |       3 |   1     |   1     |   0     |   0     |   0     | greater_than -0.05 | supports     |
| RQ2  | LLM (G1) vs rule baseline, recall, expert                         | Butler | taxon       | lenient R |       3 |   1     |   0.615 |   0.385 |   0.385 |   0.385 | greater_than 0.0   | supports     |
| RQ2  | LLM (G1) vs rule baseline, recall, expert                         | Butler | person      | lenient R |       3 |   1     |   0.182 |   0.818 |   0.714 |   1     | greater_than 0.0   | supports     |
| RQ2  | LLM (G1) vs rule baseline, recall, expert                         | Butler | locality    | lenient R |       3 |   1     |   0.243 |   0.757 |   0.733 |   1     | greater_than 0.0   | supports     |
| RQ2  | LLM (G1) vs rule baseline, recall, expert                         | Butler | institution | lenient R |       3 | nan     | nan     | nan     | nan     | nan     | greater_than 0.0   | no data      |
| RQ2  | LLM (G1) vs rule baseline, recall, expert                         | Butler | date        | lenient R |       3 |   1     |   0.5   |   0.5   |   0     |   1     | greater_than 0.0   | inconclusive |
| RQ2  | LLM (G1) vs rule baseline, recall, expert                         | Reeve  | taxon       | lenient R |       3 |   1     |   0.88  |   0.12  |   0     |   0.6   | greater_than 0.0   | inconclusive |
| RQ2  | LLM (G1) vs rule baseline, recall, expert                         | Reeve  | person      | lenient R |       3 |   1     |   0.091 |   0.909 |   0.333 |   1     | greater_than 0.0   | supports     |
| RQ2  | LLM (G1) vs rule baseline, recall, expert                         | Reeve  | locality    | lenient R |       3 |   1     |   1     |   0     |   0     |   0     | greater_than 0.0   | against      |
| RQ2  | LLM (G1) vs rule baseline, recall, expert                         | Reeve  | institution | lenient R |       3 |   1     |   1     |   0     |   0     |   0     | greater_than 0.0   | against      |
| RQ2  | LLM (G1) vs rule baseline, recall, expert                         | Reeve  | date        | lenient R |       3 | nan     | nan     | nan     | nan     | nan     | greater_than 0.0   | no data      |
| RQ2  | LLM (G1) vs rule baseline, value F1, expert                       | Butler | taxon       | value F1  |       3 |   1     |   0.696 |   0.304 |   0.273 |   0.333 | greater_than 0.0   | supports     |
| RQ2  | LLM (G1) vs rule baseline, value F1, expert                       | Reeve  | taxon       | value F1  |       3 |   1     |   0.286 |   0.714 |   0.486 |   0.956 | greater_than 0.0   | supports     |
| RQ3  | recall with evidence (G1) vs without (G0), legacy                 | Butler | ALL_PRIMARY | lenient R |       3 |   1     |   1     |   0     |   0     |   0     | greater_than -0.05 | supports     |
| RQ3  | recall with evidence (G1) vs without (G0), legacy                 | Reeve  | ALL_PRIMARY | lenient R |       3 |   1     |   1     |   0     |   0     |   0     | greater_than -0.05 | supports     |
| RQ3  | recall with evidence (G1) vs without (G0), modern_dots-mocr       | Butler | ALL_PRIMARY | lenient R |       3 |   1     |   1     |   0     |   0     |   0     | greater_than -0.05 | supports     |
| RQ3  | recall with evidence (G1) vs without (G0), modern_dots-mocr       | Reeve  | ALL_PRIMARY | lenient R |       3 |   1     |   1     |   0     |   0     |   0     | greater_than -0.05 | supports     |
| RQ3  | recall with evidence (G1) vs without (G0), modern_dots-mocr_plain | Butler | ALL_PRIMARY | lenient R |       3 |   1     |   1     |   0     |   0     |   0     | greater_than -0.05 | supports     |
| RQ3  | recall with evidence (G1) vs without (G0), modern_dots-mocr_plain | Reeve  | ALL_PRIMARY | lenient R |       3 |   1     |   1     |   0     |   0     |   0     | greater_than -0.05 | supports     |

RQ2 on the other text versions, descriptive comparisons and other fields: `comparisons.csv`.

## Evidence (RQ3)

| book   | version                | condition   |   outputs |   unsupported |   unsupported_rate |   wrong_line |   type_check_failed |   copied_line_label |
|:-------|:-----------------------|:------------|----------:|--------------:|-------------------:|-------------:|--------------------:|--------------------:|
| Butler | expert                 | G0          |       104 |             0 |             0      |            0 |                   0 |                   0 |
| Butler | expert                 | G1          |       103 |             0 |             0      |            0 |                   0 |                   0 |
| Butler | legacy                 | G0          |       103 |             0 |             0      |            0 |                   1 |                   0 |
| Butler | legacy                 | G1          |       103 |             0 |             0      |            0 |                   1 |                   0 |
| Butler | modern_dots-mocr       | G0          |       104 |             0 |             0      |            0 |                   0 |                   0 |
| Butler | modern_dots-mocr       | G1          |       103 |             0 |             0      |            0 |                   0 |                   0 |
| Butler | modern_dots-mocr_plain | G0          |       103 |             0 |             0      |            0 |                   0 |                   0 |
| Butler | modern_dots-mocr_plain | G1          |       104 |             0 |             0      |            0 |                   0 |                   0 |
| Reeve  | expert                 | G0          |        82 |             0 |             0      |            0 |                   0 |                   0 |
| Reeve  | expert                 | G1          |        82 |             0 |             0      |            0 |                   0 |                   0 |
| Reeve  | legacy                 | G0          |        82 |             0 |             0      |            0 |                   0 |                   0 |
| Reeve  | legacy                 | G1          |        82 |             0 |             0      |            0 |                   0 |                   0 |
| Reeve  | modern_dots-mocr       | G0          |        82 |             1 |             0.0122 |            0 |                   0 |                   0 |
| Reeve  | modern_dots-mocr       | G1          |        83 |             0 |             0      |            0 |                   0 |                   0 |
| Reeve  | modern_dots-mocr_plain | G0          |        82 |             0 |             0      |            0 |                   0 |                   0 |
| Reeve  | modern_dots-mocr_plain | G1          |        82 |             0 |             0      |            0 |                   0 |                   0 |

## Request outcomes

| run                                     | outcome     |   requests |
|:----------------------------------------|:------------|-----------:|
| 20261118-2102_rules-gnfinder-v1.4.0_all | ok          |         24 |
| 20261119-0113_claude-opus-5-5_dev_p4_r1 | ok          |         48 |
| 20261119-0221_gemini-4-carbon_dev_p4_r1 | empty       |          1 |
| 20261119-0221_gemini-4-carbon_dev_p4_r1 | ok          |         44 |
| 20261119-0221_gemini-4-carbon_dev_p4_r1 | parse_error |          3 |

## Shadow evaluation (RQ4): flagged = proposed auto-accept, nothing is skipped

| book   | version                |   predictions |   flagged |   flagged_share |   precision_flagged |   precision_unflagged |    diff |   diff_lo |   diff_hi | verdict      |   errors_in_flagged_set |   gold |   missed_by_model_a |   missed_by_both |
|:-------|:-----------------------|--------------:|----------:|----------------:|--------------------:|----------------------:|--------:|----------:|----------:|:-------------|------------------------:|-------:|--------------------:|-----------------:|
| Butler | expert                 |            63 |        63 |           1     |               1     |               nan     | nan     |   nan     |   nan     | no data      |                       0 |     63 |                   0 |                0 |
| Butler | legacy                 |            63 |        56 |           0.889 |               0.786 |                 0.857 |  -0.071 |    -0.273 |     0.8   | inconclusive |                      12 |     63 |                   0 |                0 |
| Butler | modern_dots-mocr       |            63 |        63 |           1     |               0.984 |               nan     | nan     |   nan     |   nan     | no data      |                       1 |     63 |                   0 |                0 |
| Butler | modern_dots-mocr_plain |            63 |        63 |           1     |               0.984 |               nan     | nan     |   nan     |   nan     | no data      |                       1 |     63 |                   0 |                0 |
| Reeve  | expert                 |            70 |        70 |           1     |               1     |               nan     | nan     |   nan     |   nan     | no data      |                       0 |     70 |                   0 |                0 |
| Reeve  | legacy                 |            70 |        51 |           0.729 |               0.765 |                 0.579 |   0.186 |     0.154 |     0.199 | supports     |                      12 |     70 |                   0 |                0 |
| Reeve  | modern_dots-mocr       |            71 |        70 |           0.986 |               0.971 |                 0     |   0.971 |     0.955 |     0.986 | supports     |                       2 |     70 |                   0 |                0 |
| Reeve  | modern_dots-mocr_plain |            70 |        70 |           1     |               0.986 |               nan     | nan     |   nan     |   nan     | no data      |                       1 |     70 |                   0 |                0 |

### Risk and coverage

| book   | version                |   accept_up_to_tier |   accepted |   coverage |   errors_accepted |   risk |   left_for_review |
|:-------|:-----------------------|--------------------:|-----------:|-----------:|------------------:|-------:|------------------:|
| Butler | expert                 |                   0 |         63 |      1     |                 0 |  0     |                 0 |
| Butler | legacy                 |                   0 |         56 |      0.889 |                12 |  0.214 |                 7 |
| Butler | legacy                 |                   1 |         57 |      0.905 |                13 |  0.228 |                 6 |
| Butler | legacy                 |                   2 |         63 |      1     |                13 |  0.206 |                 0 |
| Butler | modern_dots-mocr       |                   0 |         63 |      1     |                 1 |  0.016 |                 0 |
| Butler | modern_dots-mocr_plain |                   0 |         63 |      1     |                 1 |  0.016 |                 0 |
| Reeve  | expert                 |                   0 |         70 |      1     |                 0 |  0     |                 0 |
| Reeve  | legacy                 |                   0 |         51 |      0.729 |                12 |  0.235 |                19 |
| Reeve  | legacy                 |                   2 |         70 |      1     |                20 |  0.286 |                 0 |
| Reeve  | modern_dots-mocr       |                   0 |         70 |      0.986 |                 2 |  0.029 |                 1 |
| Reeve  | modern_dots-mocr       |                   2 |         71 |      1     |                 3 |  0.042 |                 0 |
| Reeve  | modern_dots-mocr_plain |                   0 |         70 |      1     |                 1 |  0.014 |                 0 |

False positives and negatives for the error analysis: `discrepancies.csv` (1178 rows).
