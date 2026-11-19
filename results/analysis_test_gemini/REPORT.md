# Analysis report: test_gemini (TEST pages)

Gold: `gold/gold_mentions_gloria_test.csv` (c24a9bac66ee…), guide ['v0.10', 'v0.6', 'v0.7', 'v0.8', 'v0.9'].
Code commit `dba7ab497d` **with uncommitted changes**.
Runs: `20261119-2052_gemini-4-carbon_test_sync` (llm, gemini-4-carbon, prompt p4-guide-v0.6); `20261119-2052_claude-opus-5-5_test_batch` (llm2, claude-opus-5-5, prompt p4-guide-v0.6); `20261118-2102_rules-gnfinder-v1.4.0_all` (rule, rules + gnfinder v1.4.0, prompt None).


## Sample behind every number

| book   | field       |   pages |   gold |   gold_ambiguous_excluded | too_few_to_compare   |
|:-------|:------------|--------:|-------:|--------------------------:|:---------------------|
| Butler | ALL_PRIMARY |       7 |    137 |                         0 | False                |
| Butler | date        |       7 |     26 |                         0 | False                |
| Butler | institution |       7 |      0 |                         0 | True                 |
| Butler | locality    |       7 |     49 |                         0 | False                |
| Butler | person      |       7 |     19 |                         0 | False                |
| Butler | taxon       |       7 |     43 |                         0 | False                |
| Butler | vernacular  |       7 |     52 |                         0 | False                |
| Reeve  | ALL_PRIMARY |       9 |    213 |                         0 | False                |
| Reeve  | date        |       9 |      0 |                         0 | True                 |
| Reeve  | institution |       9 |     23 |                         0 | False                |
| Reeve  | locality    |       9 |     31 |                         0 | False                |
| Reeve  | person      |       9 |     85 |                         0 | False                |
| Reeve  | taxon       |       9 |     74 |                         0 | False                |
| Reeve  | vernacular  |       9 |     19 |                         0 | False                |

## Scores, primary fields together (value level is the primary metric)

| run                                      | book   | version                | condition   |   gold |   pred |   value_P |   value_R |   value_F1 |   value_F1_lo |   value_F1_hi |   lenient_F1 |   exact_F1 |   unaligned |
|:-----------------------------------------|:-------|:-----------------------|:------------|-------:|-------:|----------:|----------:|-----------:|--------------:|--------------:|-------------:|-----------:|------------:|
| 20261119-2052_gemini-4-carbon_test_sync  | Butler | expert                 | G0          |    137 |    139 |     0.971 |     0.985 |      0.978 |         0.944 |         1     |        0.993 |      0.978 |           0 |
| 20261119-2052_gemini-4-carbon_test_sync  | Butler | expert                 | G1          |    137 |    138 |     0.971 |     0.978 |      0.975 |         0.939 |         1     |        0.996 |      0.975 |           0 |
| 20261119-2052_gemini-4-carbon_test_sync  | Butler | legacy                 | G0          |    137 |    139 |     0.597 |     0.606 |      0.601 |         0.456 |         0.747 |        0.993 |      0.92  |           0 |
| 20261119-2052_gemini-4-carbon_test_sync  | Butler | legacy                 | G1          |    137 |    138 |     0.601 |     0.606 |      0.604 |         0.452 |         0.749 |        0.996 |      0.924 |           0 |
| 20261119-2052_gemini-4-carbon_test_sync  | Butler | modern_dots-mocr       | G0          |    137 |    136 |     0.963 |     0.956 |      0.96  |         0.925 |         0.987 |        0.989 |      0.952 |           0 |
| 20261119-2052_gemini-4-carbon_test_sync  | Butler | modern_dots-mocr       | G1          |    137 |    137 |     0.964 |     0.964 |      0.964 |         0.93  |         0.991 |        0.985 |      0.956 |           0 |
| 20261119-2052_gemini-4-carbon_test_sync  | Butler | modern_dots-mocr_plain | G0          |    137 |    137 |     0.949 |     0.949 |      0.949 |         0.917 |         0.978 |        0.985 |      0.942 |           0 |
| 20261119-2052_gemini-4-carbon_test_sync  | Butler | modern_dots-mocr_plain | G1          |    137 |    138 |     0.957 |     0.964 |      0.96  |         0.927 |         0.983 |        0.982 |      0.953 |           0 |
| 20261119-2052_gemini-4-carbon_test_sync  | Reeve  | expert                 | G0          |    213 |    215 |     0.972 |     0.981 |      0.977 |         0.957 |         1     |        0.981 |      0.977 |           0 |
| 20261119-2052_gemini-4-carbon_test_sync  | Reeve  | expert                 | G1          |    213 |    214 |     0.986 |     0.991 |      0.988 |         0.977 |         1     |        0.993 |      0.988 |           0 |
| 20261119-2052_gemini-4-carbon_test_sync  | Reeve  | legacy                 | G0          |    213 |    215 |     0.637 |     0.643 |      0.64  |         0.517 |         0.721 |        0.935 |      0.897 |           5 |
| 20261119-2052_gemini-4-carbon_test_sync  | Reeve  | legacy                 | G1          |    213 |    214 |     0.64  |     0.643 |      0.642 |         0.523 |         0.723 |        0.937 |      0.899 |           5 |
| 20261119-2052_gemini-4-carbon_test_sync  | Reeve  | modern_dots-mocr       | G0          |    213 |    215 |     0.958 |     0.967 |      0.963 |         0.93  |         1     |        0.991 |      0.972 |           0 |
| 20261119-2052_gemini-4-carbon_test_sync  | Reeve  | modern_dots-mocr       | G1          |    213 |    214 |     0.977 |     0.981 |      0.979 |         0.957 |         0.997 |        0.993 |      0.988 |           0 |
| 20261119-2052_gemini-4-carbon_test_sync  | Reeve  | modern_dots-mocr_plain | G0          |    213 |    214 |     0.977 |     0.981 |      0.979 |         0.959 |         1     |        0.993 |      0.988 |           0 |
| 20261119-2052_gemini-4-carbon_test_sync  | Reeve  | modern_dots-mocr_plain | G1          |    213 |    214 |     0.963 |     0.967 |      0.965 |         0.934 |         0.996 |        0.993 |      0.974 |           0 |
| 20261119-2052_claude-opus-5-5_test_batch | Butler | expert                 | G0          |    137 |    137 |     0.971 |     0.971 |      0.971 |         0.935 |         1     |        0.993 |      0.971 |           0 |
| 20261119-2052_claude-opus-5-5_test_batch | Butler | expert                 | G1          |    137 |    138 |     0.978 |     0.985 |      0.982 |         0.947 |         1     |        0.996 |      0.982 |           0 |
| 20261119-2052_claude-opus-5-5_test_batch | Butler | legacy                 | G0          |    137 |    134 |     0.612 |     0.599 |      0.605 |         0.459 |         0.748 |        0.974 |      0.9   |           0 |
| 20261119-2052_claude-opus-5-5_test_batch | Butler | legacy                 | G1          |    137 |    131 |     0.611 |     0.584 |      0.597 |         0.445 |         0.736 |        0.97  |      0.881 |           0 |
| 20261119-2052_claude-opus-5-5_test_batch | Butler | modern_dots-mocr       | G0          |    137 |    136 |     0.971 |     0.964 |      0.967 |         0.929 |         0.994 |        0.989 |      0.96  |           0 |
| 20261119-2052_claude-opus-5-5_test_batch | Butler | modern_dots-mocr       | G1          |    137 |    136 |     0.956 |     0.949 |      0.952 |         0.923 |         0.979 |        0.982 |      0.945 |           0 |
| 20261119-2052_claude-opus-5-5_test_batch | Butler | modern_dots-mocr_plain | G0          |    137 |    136 |     0.978 |     0.971 |      0.974 |         0.949 |         0.994 |        0.989 |      0.967 |           0 |
| 20261119-2052_claude-opus-5-5_test_batch | Butler | modern_dots-mocr_plain | G1          |    137 |    136 |     0.971 |     0.964 |      0.967 |         0.929 |         0.994 |        0.989 |      0.96  |           0 |
| 20261119-2052_claude-opus-5-5_test_batch | Reeve  | expert                 | G0          |    213 |    214 |     0.977 |     0.981 |      0.979 |         0.961 |         1     |        0.984 |      0.979 |           0 |
| 20261119-2052_claude-opus-5-5_test_batch | Reeve  | expert                 | G1          |    213 |    213 |     0.981 |     0.981 |      0.981 |         0.974 |         1     |        0.991 |      0.977 |           0 |
| 20261119-2052_claude-opus-5-5_test_batch | Reeve  | legacy                 | G0          |    213 |    209 |     0.651 |     0.638 |      0.645 |         0.53  |         0.722 |        0.934 |      0.9   |           5 |
| 20261119-2052_claude-opus-5-5_test_batch | Reeve  | legacy                 | G1          |    213 |    213 |     0.638 |     0.638 |      0.638 |         0.521 |         0.719 |        0.93  |      0.892 |           5 |
| 20261119-2052_claude-opus-5-5_test_batch | Reeve  | modern_dots-mocr       | G0          |    213 |    214 |     0.977 |     0.981 |      0.979 |         0.956 |         1     |        0.993 |      0.988 |           0 |
| 20261119-2052_claude-opus-5-5_test_batch | Reeve  | modern_dots-mocr       | G1          |    213 |    215 |     0.972 |     0.981 |      0.977 |         0.954 |         0.997 |        0.991 |      0.986 |           0 |
| 20261119-2052_claude-opus-5-5_test_batch | Reeve  | modern_dots-mocr_plain | G0          |    213 |    215 |     0.972 |     0.981 |      0.977 |         0.956 |         1     |        0.991 |      0.986 |           0 |
| 20261119-2052_claude-opus-5-5_test_batch | Reeve  | modern_dots-mocr_plain | G1          |    213 |    215 |     0.972 |     0.981 |      0.977 |         0.955 |         0.996 |        0.991 |      0.986 |           0 |
| 20261118-2102_rules-gnfinder-v1.4.0_all  | Butler | expert                 | RULE        |    137 |     77 |     0.844 |     0.474 |      0.607 |         0.476 |         0.729 |        0.673 |      0.551 |           0 |
| 20261118-2102_rules-gnfinder-v1.4.0_all  | Butler | legacy                 | RULE        |    137 |     68 |     0.662 |     0.328 |      0.439 |         0.318 |         0.576 |        0.615 |      0.468 |           0 |
| 20261118-2102_rules-gnfinder-v1.4.0_all  | Butler | modern_dots-mocr       | RULE        |    137 |     80 |     0.862 |     0.504 |      0.636 |         0.5   |         0.765 |        0.691 |      0.571 |           0 |
| 20261118-2102_rules-gnfinder-v1.4.0_all  | Butler | modern_dots-mocr_plain | RULE        |    137 |     80 |     0.85  |     0.496 |      0.627 |         0.496 |         0.739 |        0.691 |      0.562 |           0 |
| 20261118-2102_rules-gnfinder-v1.4.0_all  | Reeve  | expert                 | RULE        |    213 |    173 |     0.555 |     0.451 |      0.497 |         0.435 |         0.551 |        0.622 |      0.497 |           0 |
| 20261118-2102_rules-gnfinder-v1.4.0_all  | Reeve  | legacy                 | RULE        |    213 |    128 |     0.477 |     0.286 |      0.358 |         0.293 |         0.411 |        0.499 |      0.434 |           1 |
| 20261118-2102_rules-gnfinder-v1.4.0_all  | Reeve  | modern_dots-mocr       | RULE        |    213 |    158 |     0.57  |     0.423 |      0.485 |         0.406 |         0.554 |        0.588 |      0.485 |           0 |
| 20261118-2102_rules-gnfinder-v1.4.0_all  | Reeve  | modern_dots-mocr_plain | RULE        |    213 |    170 |     0.565 |     0.451 |      0.501 |         0.441 |         0.553 |        0.627 |      0.501 |           0 |

Per field (including `vernacular`, scored apart): `scores.csv`.

## Where gold mentions are lost (main LLM, with evidence)

| book   | version                |   gold |   lost_at_ocr |   of_which_still_found |   lost_at_extraction |   lost_at_value |   kept |   kept_share |
|:-------|:-----------------------|-------:|--------------:|-----------------------:|---------------------:|----------------:|-------:|-------------:|
| Butler | expert                 |    137 |             0 |                      0 |                    0 |               3 |    134 |        0.978 |
| Butler | legacy                 |    137 |            53 |                     53 |                    0 |               1 |     83 |        0.606 |
| Butler | modern_dots-mocr       |    137 |             5 |                      3 |                    0 |               2 |    130 |        0.949 |
| Butler | modern_dots-mocr_plain |    137 |             5 |                      3 |                    0 |               2 |    130 |        0.949 |
| Reeve  | expert                 |    213 |             0 |                      0 |                    1 |               1 |    211 |        0.991 |
| Reeve  | legacy                 |    213 |            73 |                     61 |                    1 |               2 |    137 |        0.643 |
| Reeve  | modern_dots-mocr       |    213 |             2 |                      2 |                    1 |               1 |    209 |        0.981 |
| Reeve  | modern_dots-mocr_plain |    213 |             2 |                      2 |                    1 |               4 |    206 |        0.967 |

## Pre-registered comparisons (paired page bootstrap)

Shown: RQ1, RQ3, and RQ2 on the expert text. A is the arm the hypothesis expects to be better;
`verdict` compares the 95% interval of A - B with the rule written in advance.

| rq   | comparison                                                        | book   | field       | metric    |   pages |       a |       b |    diff |      lo |      hi | rule               | verdict      |
|:-----|:------------------------------------------------------------------|:-------|:------------|:----------|--------:|--------:|--------:|--------:|--------:|--------:|:-------------------|:-------------|
| RQ1  | modern OCR vs legacy OCR                                          | Reeve  | ALL_PRIMARY | value F1  |       9 |   0.979 |   0.642 |   0.337 |   0.25  |   0.457 | at_least 0.1       | supports     |
| RQ1  | expert vs modern OCR                                              | Reeve  | ALL_PRIMARY | value F1  |       9 |   0.988 |   0.979 |   0.009 |   0     |   0.028 | less_than 0.05     | supports     |
| RQ3  | recall with evidence (G1) vs without (G0), expert                 | Butler | ALL_PRIMARY | lenient R |       7 |   1     |   1     |   0     |   0     |   0     | greater_than -0.05 | supports     |
| RQ3  | recall with evidence (G1) vs without (G0), expert                 | Reeve  | ALL_PRIMARY | lenient R |       9 |   0.995 |   0.986 |   0.009 |   0     |   0.021 | greater_than -0.05 | supports     |
| RQ2  | LLM (G1) vs rule baseline, recall, expert                         | Butler | taxon       | lenient R |       7 |   1     |   0.512 |   0.488 |   0.244 |   0.648 | greater_than 0.0   | supports     |
| RQ2  | LLM (G1) vs rule baseline, recall, expert                         | Butler | person      | lenient R |       7 |   1     |   0.263 |   0.737 |   0.625 |   0.882 | greater_than 0.0   | supports     |
| RQ2  | LLM (G1) vs rule baseline, recall, expert                         | Butler | locality    | lenient R |       7 |   1     |   0.449 |   0.551 |   0.25  |   0.704 | greater_than 0.0   | supports     |
| RQ2  | LLM (G1) vs rule baseline, recall, expert                         | Butler | institution | lenient R |       7 | nan     | nan     | nan     | nan     | nan     | greater_than 0.0   | no data      |
| RQ2  | LLM (G1) vs rule baseline, recall, expert                         | Butler | date        | lenient R |       7 |   1     |   0.885 |   0.115 |   0     |   0.312 | greater_than 0.0   | inconclusive |
| RQ2  | LLM (G1) vs rule baseline, recall, expert                         | Reeve  | taxon       | lenient R |       9 |   1     |   0.892 |   0.108 |   0.025 |   0.148 | greater_than 0.0   | supports     |
| RQ2  | LLM (G1) vs rule baseline, recall, expert                         | Reeve  | person      | lenient R |       9 |   1     |   0.224 |   0.776 |   0.671 |   0.861 | greater_than 0.0   | supports     |
| RQ2  | LLM (G1) vs rule baseline, recall, expert                         | Reeve  | locality    | lenient R |       9 |   0.968 |   0.581 |   0.387 |   0     |   0.611 | greater_than 0.0   | inconclusive |
| RQ2  | LLM (G1) vs rule baseline, recall, expert                         | Reeve  | institution | lenient R |       9 |   1     |   0.739 |   0.261 |   0     |   0.556 | greater_than 0.0   | inconclusive |
| RQ2  | LLM (G1) vs rule baseline, recall, expert                         | Reeve  | date        | lenient R |       9 | nan     | nan     | nan     | nan     | nan     | greater_than 0.0   | no data      |
| RQ2  | LLM (G1) vs rule baseline, value F1, expert                       | Butler | taxon       | value F1  |       7 |   1     |   0.636 |   0.364 |   0.207 |   0.493 | greater_than 0.0   | supports     |
| RQ2  | LLM (G1) vs rule baseline, value F1, expert                       | Reeve  | taxon       | value F1  |       9 |   0.987 |   0.536 |   0.45  |   0.295 |   0.678 | greater_than 0.0   | supports     |
| RQ3  | recall with evidence (G1) vs without (G0), legacy                 | Butler | ALL_PRIMARY | lenient R |       7 |   1     |   1     |   0     |   0     |   0     | greater_than -0.05 | supports     |
| RQ3  | recall with evidence (G1) vs without (G0), legacy                 | Reeve  | ALL_PRIMARY | lenient R |       9 |   0.939 |   0.939 |   0     |   0     |   0     | greater_than -0.05 | supports     |
| RQ3  | recall with evidence (G1) vs without (G0), modern_dots-mocr       | Butler | ALL_PRIMARY | lenient R |       7 |   0.985 |   0.985 |   0     |   0     |   0     | greater_than -0.05 | supports     |
| RQ3  | recall with evidence (G1) vs without (G0), modern_dots-mocr       | Reeve  | ALL_PRIMARY | lenient R |       9 |   0.995 |   0.995 |   0     |   0     |   0     | greater_than -0.05 | supports     |
| RQ3  | recall with evidence (G1) vs without (G0), modern_dots-mocr_plain | Butler | ALL_PRIMARY | lenient R |       7 |   0.985 |   0.985 |   0     |   0     |   0     | greater_than -0.05 | supports     |
| RQ3  | recall with evidence (G1) vs without (G0), modern_dots-mocr_plain | Reeve  | ALL_PRIMARY | lenient R |       9 |   0.995 |   0.995 |   0     |   0     |   0     | greater_than -0.05 | supports     |

RQ2 on the other text versions, descriptive comparisons and other fields: `comparisons.csv`.

## Evidence (RQ3)

| book   | version                | condition   |   outputs |   unsupported |   unsupported_rate |   wrong_line |   type_check_failed |   copied_line_label |
|:-------|:-----------------------|:------------|----------:|--------------:|-------------------:|-------------:|--------------------:|--------------------:|
| Butler | expert                 | G0          |       188 |             0 |                  0 |            0 |                   0 |                   0 |
| Butler | expert                 | G1          |       187 |             0 |                  0 |            0 |                   0 |                   0 |
| Butler | legacy                 | G0          |       189 |             0 |                  0 |            0 |                   3 |                   0 |
| Butler | legacy                 | G1          |       184 |             0 |                  0 |            0 |                   3 |                   0 |
| Butler | modern_dots-mocr       | G0          |       185 |             0 |                  0 |            0 |                   0 |                   0 |
| Butler | modern_dots-mocr       | G1          |       186 |             0 |                  0 |            0 |                   0 |                   0 |
| Butler | modern_dots-mocr_plain | G0          |       185 |             0 |                  0 |            0 |                   0 |                   0 |
| Butler | modern_dots-mocr_plain | G1          |       188 |             0 |                  0 |            0 |                   0 |                   0 |
| Reeve  | expert                 | G0          |       232 |             0 |                  0 |            0 |                   1 |                   0 |
| Reeve  | expert                 | G1          |       231 |             0 |                  0 |            0 |                   1 |                   0 |
| Reeve  | legacy                 | G0          |       232 |             0 |                  0 |            0 |                   2 |                   0 |
| Reeve  | legacy                 | G1          |       231 |             0 |                  0 |            0 |                   2 |                   0 |
| Reeve  | modern_dots-mocr       | G0          |       232 |             0 |                  0 |            0 |                   1 |                   0 |
| Reeve  | modern_dots-mocr       | G1          |       231 |             0 |                  0 |            0 |                   1 |                   0 |
| Reeve  | modern_dots-mocr_plain | G0          |       232 |             0 |                  0 |            0 |                   1 |                   0 |
| Reeve  | modern_dots-mocr_plain | G1          |       231 |             0 |                  0 |            0 |                   1 |                   0 |

## Request outcomes

| run                                      | outcome   |   requests |
|:-----------------------------------------|:----------|-----------:|
| 20261118-2102_rules-gnfinder-v1.4.0_all  | empty     |          3 |
| 20261118-2102_rules-gnfinder-v1.4.0_all  | ok        |         61 |
| 20261119-2052_claude-opus-5-5_test_batch | ok        |        128 |
| 20261119-2052_gemini-4-carbon_test_sync  | ok        |        128 |

## Shadow evaluation (RQ4): flagged = proposed auto-accept, nothing is skipped

| book   | version                |   predictions |   flagged |   flagged_share |   precision_flagged |   precision_unflagged |    diff |   diff_lo |   diff_hi |   unflagged | verdict            |   excluded_no_answer_from_b |   errors_in_flagged_set |   gold |   missed_by_model_a |   missed_by_both |
|:-------|:-----------------------|--------------:|----------:|----------------:|--------------------:|----------------------:|--------:|----------:|----------:|------------:|:-------------------|----------------------------:|------------------------:|-------:|--------------------:|-----------------:|
| Butler | expert                 |           138 |       138 |           1     |               0.971 |               nan     | nan     |   nan     |   nan     |           0 | too few to compare |                           0 |                       4 |    137 |                   0 |                0 |
| Butler | legacy                 |           138 |       130 |           0.942 |               0.631 |                 0.125 |   0.506 |     0.267 |     0.743 |           8 | too few to compare |                           0 |                      48 |    137 |                   0 |                0 |
| Butler | modern_dots-mocr       |           137 |       136 |           0.993 |               0.963 |                 1     |  -0.037 |    -0.07  |    -0.006 |           1 | too few to compare |                           0 |                       5 |    137 |                   2 |                2 |
| Butler | modern_dots-mocr_plain |           138 |       136 |           0.986 |               0.971 |                 0     |   0.971 |     0.932 |     1     |           2 | too few to compare |                           0 |                       4 |    137 |                   2 |                2 |
| Reeve  | expert                 |           214 |       212 |           0.991 |               0.986 |                 1     |  -0.014 |    -0.03  |     0     |           2 | too few to compare |                           0 |                       3 |    213 |                   1 |                1 |
| Reeve  | legacy                 |           214 |       211 |           0.986 |               0.645 |                 0.333 |   0.311 |     0.078 |     0.699 |           3 | too few to compare |                           0 |                      75 |    213 |                  13 |               13 |
| Reeve  | modern_dots-mocr       |           214 |       213 |           0.995 |               0.977 |                 1     |  -0.023 |    -0.038 |     0     |           1 | too few to compare |                           0 |                       5 |    213 |                   1 |                1 |
| Reeve  | modern_dots-mocr_plain |           214 |       213 |           0.995 |               0.962 |                 1     |  -0.038 |    -0.054 |     0     |           1 | too few to compare |                           0 |                       8 |    213 |                   1 |                1 |

### Risk and coverage

| book   | version                |   accept_up_to_tier |   accepted |   coverage |   errors_accepted |   risk |   left_for_review |
|:-------|:-----------------------|--------------------:|-----------:|-----------:|------------------:|-------:|------------------:|
| Butler | expert                 |                   0 |        138 |      1     |                 4 |  0.029 |                 0 |
| Butler | legacy                 |                   0 |        130 |      0.942 |                48 |  0.369 |                 8 |
| Butler | legacy                 |                   1 |        131 |      0.949 |                49 |  0.374 |                 7 |
| Butler | legacy                 |                   2 |        136 |      0.986 |                53 |  0.39  |                 2 |
| Butler | legacy                 |                   3 |        138 |      1     |                55 |  0.399 |                 0 |
| Butler | modern_dots-mocr       |                   0 |        136 |      0.993 |                 5 |  0.037 |                 1 |
| Butler | modern_dots-mocr       |                   2 |        137 |      1     |                 5 |  0.036 |                 0 |
| Butler | modern_dots-mocr_plain |                   0 |        136 |      0.986 |                 4 |  0.029 |                 2 |
| Butler | modern_dots-mocr_plain |                   2 |        138 |      1     |                 6 |  0.043 |                 0 |
| Reeve  | expert                 |                   0 |        212 |      0.991 |                 3 |  0.014 |                 2 |
| Reeve  | expert                 |                   1 |        213 |      0.995 |                 3 |  0.014 |                 1 |
| Reeve  | expert                 |                   2 |        214 |      1     |                 3 |  0.014 |                 0 |
| Reeve  | legacy                 |                   0 |        211 |      0.986 |                75 |  0.355 |                 3 |
| Reeve  | legacy                 |                   1 |        212 |      0.991 |                76 |  0.358 |                 2 |
| Reeve  | legacy                 |                   2 |        213 |      0.995 |                77 |  0.362 |                 1 |
| Reeve  | legacy                 |                   3 |        214 |      1     |                77 |  0.36  |                 0 |
| Reeve  | modern_dots-mocr       |                   0 |        213 |      0.995 |                 5 |  0.023 |                 1 |
| Reeve  | modern_dots-mocr       |                   1 |        214 |      1     |                 5 |  0.023 |                 0 |
| Reeve  | modern_dots-mocr_plain |                   0 |        213 |      0.995 |                 8 |  0.038 |                 1 |
| Reeve  | modern_dots-mocr_plain |                   1 |        214 |      1     |                 8 |  0.037 |                 0 |

False positives and negatives for the error analysis: `discrepancies.csv` (2988 rows).
