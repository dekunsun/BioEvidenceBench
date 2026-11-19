# Repeat report: p4_dev (DEV pages only)

Runs: `20261119-0113_claude-opus-5-5_dev_p4_r1`, `20261119-0113_claude-opus-5-5_dev_p4_r2`, `20261119-0113_claude-opus-5-5_dev_p4_r3`
Configuration (identical in all runs): model `claude-opus-5-5`, prompt `p4-guide-v0.6`, effort `medium`.

## Output consistency (no gold needed)

A mention is (page, field, start, end) in the text the model read. `all_over_any` is the share
of mentions found by every repeat among those found by any repeat.

| version                | condition   |   n_r1 |   n_r2 |   n_r3 |   in_all |   in_any |   all_over_any |   mean_pairwise_f1 |   unlocated |
|:-----------------------|:------------|-------:|-------:|-------:|---------:|---------:|---------------:|-------------------:|------------:|
| expert                 | G0          |    186 |    185 |    185 |      185 |      186 |          0.995 |              0.998 |           0 |
| expert                 | G1          |    185 |    186 |    185 |      185 |      186 |          0.995 |              0.998 |           0 |
| legacy                 | G0          |    185 |    185 |    186 |      185 |      186 |          0.995 |              0.998 |           0 |
| legacy                 | G1          |    185 |    185 |    185 |      180 |      190 |          0.947 |              0.982 |           0 |
| modern_dots-mocr       | G0          |    186 |    185 |    185 |      184 |      187 |          0.984 |              0.995 |           0 |
| modern_dots-mocr       | G1          |    186 |    185 |    185 |      184 |      187 |          0.984 |              0.995 |           0 |
| modern_dots-mocr_plain | G0          |    185 |    186 |    185 |      184 |      186 |          0.989 |              0.996 |           0 |
| modern_dots-mocr_plain | G1          |    186 |    185 |    187 |      183 |      189 |          0.968 |              0.989 |           0 |

By field: `consistency.csv`.

## F1 per repeat (dev gold)

Mean and sample standard deviation over the repeats, primary fields together.
Per repeat and per field: `f1_by_repeat.csv`, `f1_summary.csv`.

| book   | version                | condition   |   gold |   value_F1_mean |   value_F1_sd |   value_F1_min |   value_F1_max |   lenient_F1_mean |   lenient_F1_sd |
|:-------|:-----------------------|:------------|-------:|----------------:|--------------:|---------------:|---------------:|------------------:|----------------:|
| Butler | expert                 | G0          |     63 |           1     |         0     |          1     |          1     |             1     |           0     |
| Butler | expert                 | G1          |     63 |           1     |         0     |          1     |          1     |             1     |           0     |
| Butler | legacy                 | G0          |     63 |           0.794 |         0     |          0.794 |          0.794 |             1     |           0     |
| Butler | legacy                 | G1          |     63 |           0.794 |         0     |          0.794 |          0.794 |             1     |           0     |
| Butler | modern_dots-mocr       | G0          |     63 |           0.979 |         0.009 |          0.968 |          0.984 |             1     |           0     |
| Butler | modern_dots-mocr       | G1          |     63 |           0.968 |         0     |          0.968 |          0.968 |             0.984 |           0     |
| Butler | modern_dots-mocr_plain | G0          |     63 |           0.984 |         0     |          0.984 |          0.984 |             1     |           0     |
| Butler | modern_dots-mocr_plain | G1          |     63 |           0.968 |         0     |          0.968 |          0.968 |             0.984 |           0     |
| Reeve  | expert                 | G0          |     70 |           1     |         0     |          1     |          1     |             1     |           0     |
| Reeve  | expert                 | G1          |     70 |           1     |         0     |          1     |          1     |             1     |           0     |
| Reeve  | legacy                 | G0          |     70 |           0.714 |         0     |          0.714 |          0.714 |             1     |           0     |
| Reeve  | legacy                 | G1          |     70 |           0.714 |         0     |          0.714 |          0.714 |             1     |           0     |
| Reeve  | modern_dots-mocr       | G0          |     70 |           0.971 |         0     |          0.971 |          0.971 |             1     |           0     |
| Reeve  | modern_dots-mocr       | G1          |     70 |           0.979 |         0.012 |          0.965 |          0.986 |             0.998 |           0.004 |
| Reeve  | modern_dots-mocr_plain | G0          |     70 |           0.986 |         0     |          0.986 |          0.986 |             1     |           0     |
| Reeve  | modern_dots-mocr_plain | G1          |     70 |           0.986 |         0     |          0.986 |          0.986 |             1     |           0     |
