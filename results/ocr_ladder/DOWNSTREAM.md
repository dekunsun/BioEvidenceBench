# Does a cheap OCR measure predict downstream extraction? (exploratory, test pages)

Opus G1 value F1 (ALL_PRIMARY) on each OCR text, against the OCR's median page CER and the share of gold mentions preserved intact (`src/ocr_ladder.py`). 21 FineBooks OCR rows (Datalab rows not sent to the API: their outputs carry use restrictions), BHL legacy OCR and the expert text; 7 Butler and 9 Reeve test pages. Decided after unsealing: exploratory.

| book | Spearman F1 vs page CER | Spearman F1 vs preservation | Spearman recall vs preservation |
|---|---|---|---|
| Butler | -0.11 (p=0.609) | 0.95 (p=0.000) | 0.97 (p=0.000) |
| Reeve | -0.61 (p=0.001) | 1.00 (p=0.000) | 1.00 (p=0.000) |

Recall minus preservation, across OCR versions: median +0.014, range -0.007 to +0.044 (negative = the extractor gets fewer right than survive the OCR).

| book   | ocr                      |   median_page_cer |   preserved |   preserved_folded |   value_R |   value_F1 |   value_F1_lo |   value_F1_hi |
|:-------|:-------------------------|------------------:|------------:|-------------------:|----------:|-----------:|--------------:|--------------:|
| Butler | legacy (BHL)             |             0.047 |       0.613 |              0.613 |     0.584 |      0.597 |         0.445 |         0.736 |
| Butler | tesseract                |             0.013 |       0.701 |              0.701 |     0.686 |      0.681 |         0.581 |         0.795 |
| Butler | smoldocling              |             0.011 |       0.759 |              0.803 |     0.737 |      0.735 |         0.613 |         0.845 |
| Butler | deepseek-ocr2            |             0.042 |       0.803 |              0.861 |     0.774 |      0.771 |         0.659 |         0.868 |
| Butler | deepseek-ocr             |             0.038 |       0.825 |              0.825 |     0.803 |      0.803 |         0.703 |         0.893 |
| Butler | ovis-ocr2                |             0.005 |       0.854 |              0.927 |     0.825 |      0.825 |         0.708 |         0.937 |
| Butler | qianfan-ocr              |             0.004 |       0.869 |              0.891 |     0.825 |      0.825 |         0.675 |         0.953 |
| Butler | unlimited-ocr            |             0.004 |       0.861 |              0.905 |     0.825 |      0.825 |         0.707 |         0.941 |
| Butler | paddleocr-vl-16          |             0.005 |       0.854 |              0.854 |     0.839 |      0.836 |         0.733 |         0.934 |
| Butler | minicpm-ocr              |             0.02  |       0.876 |              0.964 |     0.839 |      0.846 |         0.74  |         0.939 |
| Butler | falcon-ocr               |             0.019 |       0.912 |              0.912 |     0.869 |      0.862 |         0.789 |         0.925 |
| Butler | nemotron-parse-35        |             0.006 |       0.898 |              0.898 |     0.869 |      0.865 |         0.761 |         0.968 |
| Butler | glm-ocr                  |             0.025 |       0.854 |              0.898 |     0.861 |      0.881 |         0.799 |         0.964 |
| Butler | unlimited-ocr2           |             0.004 |       0.92  |              0.92  |     0.883 |      0.893 |         0.823 |         0.966 |
| Butler | ovis-ocr3                |             0.005 |       0.927 |              0.927 |     0.905 |      0.899 |         0.817 |         0.964 |
| Butler | lighton-ocr2             |             0.009 |       0.942 |              0.942 |     0.927 |      0.93  |         0.862 |         0.986 |
| Butler | lighton-ocr3-0.8b        |             0.005 |       0.964 |              0.964 |     0.942 |      0.938 |         0.892 |         0.974 |
| Butler | dots-ocr                 |             0.023 |       0.942 |              0.942 |     0.934 |      0.945 |         0.904 |         0.98  |
| Butler | lighton-ocr3-4b          |             0.018 |       0.971 |              0.971 |     0.942 |      0.945 |         0.908 |         0.976 |
| Butler | kraken-ppocrv6           |             0.011 |       0.985 |              0.985 |     0.956 |      0.946 |         0.903 |         0.98  |
| Butler | dots-mocr                |             0.02  |       0.964 |              0.964 |     0.949 |      0.952 |         0.923 |         0.979 |
| Butler | olmocr2                  |             0.019 |       0.964 |              0.964 |     0.956 |      0.953 |         0.909 |         0.987 |
| Butler | mistral-ocr (OpenRouter) |             0.005 |       0.993 |              0.993 |     0.956 |      0.953 |         0.919 |         0.98  |
| Butler | qwen35-9b                |             0.013 |       0.978 |              0.978 |     0.964 |      0.96  |         0.915 |         0.994 |
| Butler | expert                   |             0     |       1     |              1     |     0.985 |      0.982 |         0.947 |         1     |
| Reeve  | smoldocling              |             0.052 |       0.596 |              0.648 |     0.587 |      0.625 |         0.469 |         0.707 |
| Reeve  | legacy (BHL)             |             0.086 |       0.657 |              0.662 |     0.638 |      0.638 |         0.521 |         0.719 |
| Reeve  | tesseract                |             0.036 |       0.681 |              0.681 |     0.671 |      0.667 |         0.59  |         0.706 |
| Reeve  | paddleocr-vl-16          |             0.026 |       0.784 |              0.854 |     0.775 |      0.773 |         0.69  |         0.843 |
| Reeve  | deepseek-ocr2            |             0.033 |       0.822 |              0.883 |     0.812 |      0.808 |         0.762 |         0.903 |
| Reeve  | deepseek-ocr             |             0.032 |       0.836 |              0.897 |     0.826 |      0.822 |         0.756 |         0.888 |
| Reeve  | lighton-ocr2             |             0.013 |       0.85  |              0.925 |     0.84  |      0.836 |         0.781 |         0.962 |
| Reeve  | nemotron-parse-35        |             0.015 |       0.873 |              0.948 |     0.864 |      0.862 |         0.839 |         0.928 |
| Reeve  | lighton-ocr3-4b          |             0.013 |       0.878 |              0.953 |     0.869 |      0.864 |         0.792 |         0.964 |
| Reeve  | qianfan-ocr              |             0.018 |       0.883 |              0.958 |     0.869 |      0.864 |         0.817 |         0.951 |
| Reeve  | olmocr2                  |             0.027 |       0.883 |              0.934 |     0.873 |      0.869 |         0.826 |         0.973 |
| Reeve  | qwen35-9b                |             0.024 |       0.911 |              0.934 |     0.901 |      0.897 |         0.831 |         0.972 |
| Reeve  | ovis-ocr3                |             0.016 |       0.915 |              0.991 |     0.901 |      0.901 |         0.86  |         0.984 |
| Reeve  | unlimited-ocr            |             0.012 |       0.915 |              0.958 |     0.906 |      0.902 |         0.848 |         0.957 |
| Reeve  | lighton-ocr3-0.8b        |             0.022 |       0.915 |              0.991 |     0.906 |      0.902 |         0.865 |         0.992 |
| Reeve  | ovis-ocr2                |             0.017 |       0.92  |              0.995 |     0.911 |      0.909 |         0.873 |         0.992 |
| Reeve  | mistral-ocr (OpenRouter) |             0.015 |       0.93  |              0.967 |     0.92  |      0.916 |         0.867 |         0.973 |
| Reeve  | falcon-ocr               |             0.019 |       0.939 |              0.944 |     0.944 |      0.918 |         0.848 |         0.948 |
| Reeve  | unlimited-ocr2           |             0.012 |       0.939 |              0.977 |     0.93  |      0.927 |         0.877 |         0.966 |
| Reeve  | kraken-ppocrv6           |             0.022 |       0.967 |              0.967 |     0.953 |      0.949 |         0.908 |         0.972 |
| Reeve  | glm-ocr                  |             0.022 |       0.981 |              0.981 |     0.967 |      0.967 |         0.944 |         0.987 |
| Reeve  | minicpm-ocr              |             0.022 |       0.986 |              0.986 |     0.977 |      0.972 |         0.957 |         1     |
| Reeve  | dots-mocr                |             0.013 |       0.991 |              0.991 |     0.981 |      0.977 |         0.954 |         0.997 |
| Reeve  | dots-ocr                 |             0.012 |       0.995 |              0.995 |     0.986 |      0.981 |         0.969 |         0.998 |
| Reeve  | expert                   |             0     |       1     |              1     |     0.981 |      0.981 |         0.974 |         1     |
