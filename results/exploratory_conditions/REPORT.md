# Exploratory conditions: LLM repair, vision only, vision + OCR (test pages)

Decided after unsealing (DEVIATIONS.md); Claude Opus 5.5, effort medium, frozen field definitions. `bag` = per page and field, multiset of normalised values against the gold texts (works without positions, so the image-only condition can be compared); ALL_PRIMARY.

| condition                 |   Butler |   Reeve |
|:--------------------------|---------:|--------:|
| G1 · expert               |    0.982 |   0.981 |
| G1 · legacy               |    0.597 |   0.69  |
| G1 · modern_deepseek-ocr2 |    0.771 |   0.808 |
| G1 · modern_dots-mocr     |    0.952 |   0.977 |
| G1 · modern_tesseract     |    0.681 |   0.671 |
| G2 · expert               |    0.975 |   0.981 |
| G2 · legacy               |    0.956 |   0.967 |
| G2 · modern_deepseek-ocr2 |    0.807 |   0.867 |
| G2 · modern_dots-mocr     |    0.964 |   0.981 |
| G2 · modern_tesseract     |    0.96  |   0.949 |
| V1 · image                |    0.96  |   0.981 |
| V2 · legacy               |    0.949 |   0.97  |
| V2 · modern_dots-mocr     |    0.964 |   0.977 |

Scored with positions by score.py (value F1, reading as value) for the conditions that quote the text:

| condition                 | book   |   value_F1 |   value_F1_lo |   value_F1_hi |   repaired_share |
|:--------------------------|:-------|-----------:|--------------:|--------------:|-----------------:|
| G2 · expert               | Butler |      0.975 |         0.944 |         1     |            0.01  |
| G2 · expert               | Reeve  |      0.981 |         0.965 |         1     |            0.01  |
| G2 · legacy               | Butler |      0.956 |         0.924 |         0.982 |            0.305 |
| G2 · legacy               | Reeve  |      0.906 |         0.788 |         0.954 |            0.305 |
| G2 · modern_deepseek-ocr2 | Butler |      0.807 |         0.709 |         0.893 |            0.066 |
| G2 · modern_deepseek-ocr2 | Reeve  |      0.867 |         0.824 |         0.961 |            0.066 |
| G2 · modern_dots-mocr     | Butler |      0.964 |         0.929 |         0.991 |            0.005 |
| G2 · modern_dots-mocr     | Reeve  |      0.981 |         0.967 |         1     |            0.005 |
| G2 · modern_tesseract     | Butler |      0.96  |         0.928 |         0.984 |            0.284 |
| G2 · modern_tesseract     | Reeve  |      0.939 |         0.911 |         0.976 |            0.284 |
| V2 · legacy               | Butler |      0.949 |         0.919 |         0.977 |            0.312 |
| V2 · legacy               | Reeve  |      0.909 |         0.789 |         0.972 |            0.312 |
| V2 · modern_dots-mocr     | Butler |      0.964 |         0.93  |         0.991 |            0.002 |
| V2 · modern_dots-mocr     | Reeve  |      0.977 |         0.962 |         1     |            0.002 |
