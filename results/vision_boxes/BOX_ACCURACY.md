# V3 box accuracy (exploratory)

Run `20261120-0153_explore_V3`. Only mentions whose value equals a gold value on the page are judged. Reference: IA hOCR word boxes (legacy OCR), nearest matching occurrence (lenient). `hit` = target word centre inside the model's box; `near` = within 1.5 line heights.

| book   |   hit |   near |   no_target |   off |   judged |   hit_rate |   hit_or_near |
|:-------|------:|-------:|------------:|------:|---------:|-----------:|--------------:|
| Butler |   105 |      2 |          14 |    51 |      158 |      0.665 |         0.677 |
| Reeve  |    88 |      7 |           6 |   127 |      222 |      0.396 |         0.428 |

By field:

| field       |   hit |   near |   no_target |   off |
|:------------|------:|-------:|------------:|------:|
| date        |    12 |      1 |           1 |     8 |
| institution |    16 |      0 |           0 |     7 |
| locality    |    41 |      0 |           1 |    36 |
| person      |    46 |      7 |           2 |    49 |
| taxon       |    38 |      1 |          15 |    61 |
| vernacular  |    40 |      0 |           1 |    17 |
