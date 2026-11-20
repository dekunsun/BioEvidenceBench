# Which cheap signal concentrates the errors? (exploratory, Opus G1, test pages)

Shadow comparison: flagged = sent to review, unflagged = would be proposed for auto-accept. `recall` = share of errors flagged; `precision` = share of flags that are errors. Decided after unsealing (DEVIATIONS.md). `not_agreed` exists only where Gemini read the same text version.

| versions         | signal        |   predictions |   errors |   flagged |   flagged_share |   errors_caught |   recall |   precision |   errors_left_unflagged |   error_rate_unflagged |
|:-----------------|:--------------|--------------:|---------:|----------:|----------------:|----------------:|---------:|------------:|------------------------:|-----------------------:|
| all OCR versions | ocr_junk      |          9443 |     1226 |       242 |           0.026 |              62 |    0.051 |       0.256 |                    1164 |                  0.127 |
| all OCR versions | gbif_no_exact |          9443 |     1226 |      1451 |           0.154 |             447 |    0.365 |       0.308 |                     779 |                  0.097 |
| all OCR versions | any_cheap     |          9443 |     1226 |      1659 |           0.176 |             478 |    0.39  |       0.288 |                     748 |                  0.096 |
| all OCR versions | not_agreed    |           816 |      156 |        13 |           0.016 |              12 |    0.077 |       0.923 |                     144 |                  0.179 |
| all OCR versions | legacy_text   |          9443 |     1226 |       403 |           0.043 |             143 |    0.117 |       0.355 |                    1083 |                  0.12  |
| expert           | ocr_junk      |           412 |        8 |         8 |           0.019 |               0 |    0     |       0     |                       8 |                  0.02  |
| expert           | gbif_no_exact |           412 |        8 |        56 |           0.136 |               0 |    0     |       0     |                       8 |                  0.022 |
| expert           | any_cheap     |           412 |        8 |        64 |           0.155 |               0 |    0     |       0     |                       8 |                  0.023 |
| expert           | not_agreed    |           412 |        8 |         5 |           0.012 |               3 |    0.375 |       0.6   |                       5 |                  0.012 |
| expert           | legacy_text   |           412 |        8 |         0 |           0     |               0 |    0     |     nan     |                       8 |                  0.019 |
| legacy           | ocr_junk      |           403 |      143 |        47 |           0.117 |              42 |    0.294 |       0.894 |                     101 |                  0.284 |
| legacy           | gbif_no_exact |           403 |      143 |        80 |           0.199 |              61 |    0.427 |       0.762 |                      82 |                  0.254 |
| legacy           | any_cheap     |           403 |      143 |       101 |           0.251 |              78 |    0.545 |       0.772 |                      65 |                  0.215 |
| legacy           | not_agreed    |           403 |      143 |        11 |           0.027 |              10 |    0.07  |       0.909 |                     133 |                  0.339 |
| legacy           | legacy_text   |           403 |      143 |       403 |           1     |             143 |    1     |       0.355 |                       0 |                nan     |
| modern_dots-mocr | ocr_junk      |           413 |       13 |         8 |           0.019 |               0 |    0     |       0     |                      13 |                  0.032 |
| modern_dots-mocr | gbif_no_exact |           413 |       13 |        55 |           0.133 |               3 |    0.231 |       0.055 |                      10 |                  0.028 |
| modern_dots-mocr | any_cheap     |           413 |       13 |        63 |           0.153 |               3 |    0.231 |       0.048 |                      10 |                  0.029 |
| modern_dots-mocr | not_agreed    |           413 |       13 |         2 |           0.005 |               2 |    0.154 |       1     |                      11 |                  0.027 |
| modern_dots-mocr | legacy_text   |           413 |       13 |         0 |           0     |               0 |    0     |     nan     |                      13 |                  0.031 |

Per book: `summary.csv`.