# V3 box accuracy (exploratory)

Run `20261120-0153_explore_V3`. Only mentions whose value equals a gold value on the page are judged. Reference: IA hOCR word boxes (legacy OCR), nearest matching occurrence (lenient). `hit` = target word centre inside the model's box; `near` = within 1.5 line heights (lenient: no penalty for a box that is too big). `strict_hit_rate` = share with IoU >= 0.5 against the box of the whole printed value (span-level, added 2026-11-27); `median_area_ratio` = model box area / value box area.

| book   |   hit |   near |   no_target |   off |   judged |   hit_rate |   hit_or_near |   strict_hit_rate |   median_iou |   median_area_ratio |   lenient_hits_box_over_4x |
|:-------|------:|-------:|------------:|------:|---------:|-----------:|--------------:|------------------:|-------------:|--------------------:|---------------------------:|
| Butler |   105 |      2 |          14 |    51 |      158 |      0.665 |         0.677 |             0.519 |         0.51 |                0.98 |                          2 |
| Reeve  |    88 |      7 |           6 |   127 |      222 |      0.396 |         0.428 |             0.23  |         0.07 |                1.2  |                          1 |

By field:

| field       |   hit |   near |   no_target |   off |
|:------------|------:|-------:|------------:|------:|
| date        |    12 |      1 |           1 |     8 |
| institution |    16 |      0 |           0 |     7 |
| locality    |    41 |      0 |           1 |    36 |
| person      |    46 |      7 |           2 |    49 |
| taxon       |    38 |      1 |          15 |    61 |
| vernacular  |    40 |      0 |           1 |    17 |
