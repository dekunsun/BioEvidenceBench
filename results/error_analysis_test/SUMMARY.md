# Error analysis: Opus G1, test pages

Tags by Gloria (2026-11-20); group A's OCR相关 was preset by its definition and spot-checked (DEVIATIONS.md). A case may carry several tags.

## gold_mentions (163 cases)

By book:

| book   |   cases |   OCR相关 |   抽取或推理 |   模糊或混合 |   只有OCR相关 |
|:-------|--------:|--------:|--------:|--------:|----------:|
| Butler |      74 |      66 |      11 |      17 |        56 |
| Reeve  |      89 |      85 |       6 |      15 |        74 |

By book and field:

| book   | 字段          |   cases |   OCR相关 |   抽取或推理 |   模糊或混合 |   只有OCR相关 |
|:-------|:------------|--------:|--------:|--------:|--------:|----------:|
| Butler | date        |       9 |       8 |       1 |       6 |         3 |
| Butler | locality    |       5 |       5 |       1 |       1 |         4 |
| Butler | person      |       8 |       8 |       0 |       0 |         8 |
| Butler | taxon       |      35 |      35 |       0 |       2 |        33 |
| Butler | vernacular  |      17 |      10 |       9 |       8 |         8 |
| Reeve  | institution |       6 |       6 |       0 |       1 |         5 |
| Reeve  | locality    |      10 |       8 |       4 |       4 |         6 |
| Reeve  | person      |      27 |      27 |       0 |       0 |        27 |
| Reeve  | taxon       |      36 |      36 |       0 |       6 |        30 |
| Reeve  | vernacular  |      10 |       8 |       2 |       4 |         6 |

By group:

| 分组               |   cases |   OCR相关 |   抽取或推理 |   模糊或混合 |   只有OCR相关 |
|:-----------------|--------:|--------:|--------:|--------:|----------:|
| A 只在旧OCR上错       |     137 |     137 |       0 |      10 |       127 |
| B 专家转录对，现代OCR也错  |       9 |       9 |       0 |       6 |         3 |
| C 所有版本都错（包括专家转录） |      13 |       1 |      13 |      12 |         0 |
| D 专家转录错，部分版本对    |       4 |       4 |       4 |       4 |         0 |

## extra_outputs (20 cases)

By book:

| book   |   cases |   OCR相关 |   抽取或推理 |   模糊或混合 |   只有OCR相关 |
|:-------|--------:|--------:|--------:|--------:|----------:|
| Butler |       4 |       4 |       2 |       3 |         0 |
| Reeve  |      16 |      15 |       2 |      16 |         0 |

By book and field:

| book   | 字段          |   cases |   OCR相关 |   抽取或推理 |   模糊或混合 |   只有OCR相关 |
|:-------|:------------|--------:|--------:|--------:|--------:|----------:|
| Butler | date        |       1 |       1 |       0 |       1 |         0 |
| Butler | locality    |       1 |       1 |       1 |       0 |         0 |
| Butler | vernacular  |       2 |       2 |       1 |       2 |         0 |
| Reeve  | institution |       1 |       1 |       0 |       1 |         0 |
| Reeve  | locality    |       3 |       3 |       0 |       3 |         0 |
| Reeve  | person      |       4 |       4 |       0 |       4 |         0 |
| Reeve  | taxon       |       7 |       6 |       2 |       7 |         0 |
| Reeve  | vernacular  |       1 |       1 |       0 |       1 |         0 |

By group:

| 分组          |   cases |   OCR相关 |   抽取或推理 |   模糊或混合 |   只有OCR相关 |
|:------------|--------:|--------:|--------:|--------:|----------:|
| E 四个版本都输出了  |       3 |       2 |       3 |       2 |         0 |
| F 只在部分版本输出  |      12 |      12 |       1 |      12 |         0 |
| G 无法对齐到专家转录 |       5 |       5 |       0 |       5 |         0 |
