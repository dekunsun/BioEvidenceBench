# Exploratory conditions: LLM repair, vision only, vision + OCR (test pages)

Decided after unsealing (DEVIATIONS.md); Claude Opus 5.5, effort medium, frozen field definitions. `bag` = per page and field, multiset of normalised values against the gold texts (works without positions, so the image-only condition can be compared); ALL_PRIMARY.

| condition                              |   Butler |   Reeve |
|:---------------------------------------|---------:|--------:|
| G1 · expert                            |    0.982 |   0.981 |
| G1 · legacy                            |    0.597 |   0.69  |
| G1 · modern_deepseek-ocr2              |    0.771 |   0.808 |
| G1 · modern_dots-mocr                  |    0.952 |   0.977 |
| G1 · modern_tesseract                  |    0.681 |   0.671 |
| G2 [fable-5-2] · legacy                |    0.949 |   0.962 |
| G2 [fable-5-2] · modern_deepseek-ocr2  |    0.872 |   0.956 |
| G2 [fable-5-2] · probe_swap            |    0.869 |   0.907 |
| G2 [fable-5-2] · probe_typo            |    0.964 |   0.981 |
| G2 [haiku-5-5] · legacy                |    0.873 |   0.82  |
| G2 [haiku-5-5] · modern_deepseek-ocr2  |    0.788 |   0.817 |
| G2 [haiku-5-5] · probe_swap            |    0.876 |   0.854 |
| G2 [haiku-5-5] · probe_typo            |    0.945 |   0.885 |
| G2 [sonnet-5-5] · legacy               |    0.822 |   0.649 |
| G2 [sonnet-5-5] · modern_deepseek-ocr2 |    0.769 |   0.837 |
| G2 · expert                            |    0.975 |   0.981 |
| G2 · legacy                            |    0.956 |   0.967 |
| G2 · modern_deepseek-ocr2              |    0.807 |   0.867 |
| G2 · modern_dots-mocr                  |    0.964 |   0.981 |
| G2 · modern_tesseract                  |    0.96  |   0.949 |
| G2 · probe_swap                        |    0.88  |   0.913 |
| G2 · probe_typo                        |    0.967 |   0.97  |
| V1 [fable-5-2] · image                 |    0.956 |   0.991 |
| V1 [haiku-5-5] · image                 |    0.91  |   0.845 |
| V1 [sonnet-5-5] · image                |    0.946 |   0.949 |
| V1 · image                             |    0.96  |   0.981 |
| V2 · legacy                            |    0.949 |   0.97  |
| V2 · modern_dots-mocr                  |    0.964 |   0.977 |
| V3 · image                             |    0.96  |   0.981 |

Scored with positions by score.py (value F1, reading as value) for the conditions that quote the text:

| condition                              | book   |   value_F1 |   value_F1_lo |   value_F1_hi |   repaired_share |
|:---------------------------------------|:-------|-----------:|--------------:|--------------:|-----------------:|
| G2 · expert                            | Butler |      0.975 |         0.944 |         1     |            0.01  |
| G2 · expert                            | Reeve  |      0.981 |         0.965 |         1     |            0.01  |
| G2 · legacy                            | Butler |      0.956 |         0.924 |         0.982 |            0.305 |
| G2 · legacy                            | Reeve  |      0.906 |         0.788 |         0.954 |            0.305 |
| G2 · modern_deepseek-ocr2              | Butler |      0.807 |         0.709 |         0.893 |            0.066 |
| G2 · modern_deepseek-ocr2              | Reeve  |      0.867 |         0.824 |         0.961 |            0.066 |
| G2 · modern_dots-mocr                  | Butler |      0.964 |         0.929 |         0.991 |            0.005 |
| G2 · modern_dots-mocr                  | Reeve  |      0.981 |         0.967 |         1     |            0.005 |
| G2 · modern_tesseract                  | Butler |      0.96  |         0.928 |         0.984 |            0.284 |
| G2 · modern_tesseract                  | Reeve  |      0.939 |         0.911 |         0.976 |            0.284 |
| V2 · legacy                            | Butler |      0.949 |         0.919 |         0.977 |            0.312 |
| V2 · legacy                            | Reeve  |      0.909 |         0.789 |         0.972 |            0.312 |
| V2 · modern_dots-mocr                  | Butler |      0.964 |         0.93  |         0.991 |            0.002 |
| V2 · modern_dots-mocr                  | Reeve  |      0.977 |         0.962 |         1     |            0.002 |
| G2 [haiku-5-5] · legacy                | Butler |      0.873 |         0.77  |         0.945 |            0.291 |
| G2 [haiku-5-5] · legacy                | Reeve  |      0.767 |         0.694 |         0.874 |            0.291 |
| G2 [haiku-5-5] · modern_deepseek-ocr2  | Butler |      0.788 |         0.707 |         0.859 |            0.042 |
| G2 [haiku-5-5] · modern_deepseek-ocr2  | Reeve  |      0.817 |         0.744 |         0.964 |            0.042 |
| G2 [fable-5-2] · legacy                | Butler |      0.949 |         0.897 |         0.987 |            0.32  |
| G2 [fable-5-2] · legacy                | Reeve  |      0.901 |         0.786 |         0.96  |            0.32  |
| G2 [fable-5-2] · modern_deepseek-ocr2  | Butler |      0.872 |         0.784 |         0.941 |            0.137 |
| G2 [fable-5-2] · modern_deepseek-ocr2  | Reeve  |      0.956 |         0.936 |         1     |            0.137 |
| G2 [sonnet-5-5] · legacy               | Butler |      0.822 |         0.754 |         0.895 |            0.306 |
| G2 [sonnet-5-5] · legacy               | Reeve  |      0.577 |         0.424 |         0.84  |            0.306 |
| G2 [sonnet-5-5] · modern_deepseek-ocr2 | Butler |      0.769 |         0.625 |         0.897 |            0.059 |
| G2 [sonnet-5-5] · modern_deepseek-ocr2 | Reeve  |      0.837 |         0.784 |         0.933 |            0.059 |
| G2 · probe_swap                        | Butler |      0.88  |         0.823 |         0.929 |            0.01  |
| G2 · probe_swap                        | Reeve  |      0.913 |         0.89  |         0.962 |            0.01  |
| G2 · probe_typo                        | Butler |      0.967 |         0.931 |         0.995 |            0.171 |
| G2 · probe_typo                        | Reeve  |      0.97  |         0.947 |         0.986 |            0.171 |
| G2 [fable-5-2] · probe_swap            | Butler |      0.869 |         0.807 |         0.924 |            0.012 |
| G2 [fable-5-2] · probe_swap            | Reeve  |      0.907 |         0.881 |         0.962 |            0.012 |
| G2 [fable-5-2] · probe_typo            | Butler |      0.964 |         0.933 |         0.986 |            0.179 |
| G2 [fable-5-2] · probe_typo            | Reeve  |      0.981 |         0.971 |         1     |            0.179 |
| G2 [haiku-5-5] · probe_swap            | Butler |      0.869 |         0.826 |         0.922 |            0.005 |
| G2 [haiku-5-5] · probe_swap            | Reeve  |      0.844 |         0.794 |         0.947 |            0.005 |
| G2 [haiku-5-5] · probe_typo            | Butler |      0.945 |         0.913 |         0.974 |            0.161 |
| G2 [haiku-5-5] · probe_typo            | Reeve  |      0.88  |         0.836 |         0.9   |            0.161 |
