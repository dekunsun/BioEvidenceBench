# Repeat report: p3_dev (DEV pages only)

Runs: `20261118-2108_claude-opus-5-5_dev_p3_r1`, `20261118-2108_claude-opus-5-5_dev_p3_r2`, `20261118-2108_claude-opus-5-5_dev_p3_r3`
Configuration (identical in all runs): model `claude-opus-5-5`, prompt `p3-guide-v0.5`, effort `medium`.

## Output consistency (no gold needed)

A mention is (page, field, start, end) in the text the model read. `all_over_any` is the share
of mentions found by every repeat among those found by any repeat.

| version                | condition   |   n_r1 |   n_r2 |   n_r3 |   in_all |   in_any |   all_over_any |   mean_pairwise_f1 |   unlocated |
|:-----------------------|:------------|-------:|-------:|-------:|---------:|---------:|---------------:|-------------------:|------------:|
| expert                 | G0          |    183 |    185 |    186 |      182 |      187 |          0.973 |              0.991 |           0 |
| expert                 | G1          |    181 |    182 |    181 |      180 |      183 |          0.984 |              0.994 |           0 |
| legacy                 | G0          |    182 |    185 |    182 |      181 |      186 |          0.973 |              0.991 |           0 |
| legacy                 | G1          |    182 |    182 |    180 |      179 |      183 |          0.978 |              0.993 |           0 |
| modern_dots-mocr       | G0          |    181 |    181 |    184 |      181 |      184 |          0.984 |              0.995 |           0 |
| modern_dots-mocr       | G1          |    182 |    181 |    182 |      181 |      182 |          0.995 |              0.998 |           0 |
| modern_dots-mocr_plain | G0          |    181 |    181 |    181 |      180 |      182 |          0.989 |              0.996 |           0 |
| modern_dots-mocr_plain | G1          |    181 |    181 |    181 |      180 |      182 |          0.989 |              0.996 |           0 |

By field: `consistency.csv`.

## F1 per repeat (dev gold)

Mean and sample standard deviation over the repeats, primary fields together.
Per repeat and per field: `f1_by_repeat.csv`, `f1_summary.csv`.

| book   | version                | condition   |   gold |   value_F1_mean |   value_F1_sd |   value_F1_min |   value_F1_max |   lenient_F1_mean |   lenient_F1_sd |
|:-------|:-----------------------|:------------|-------:|----------------:|--------------:|---------------:|---------------:|------------------:|----------------:|
| Butler | expert                 | G0          |     62 |           0.965 |         0.005 |          0.959 |          0.968 |             0.965 |           0.005 |
| Butler | expert                 | G1          |     62 |           0.976 |         0     |          0.976 |          0.976 |             0.976 |           0     |
| Butler | legacy                 | G0          |     62 |           0.742 |         0     |          0.742 |          0.742 |             0.968 |           0     |
| Butler | legacy                 | G1          |     62 |           0.771 |         0.006 |          0.764 |          0.774 |             0.981 |           0.005 |
| Butler | modern_dots-mocr       | G0          |     62 |           0.941 |         0.003 |          0.937 |          0.943 |             0.957 |           0.004 |
| Butler | modern_dots-mocr       | G1          |     62 |           0.949 |         0.005 |          0.943 |          0.952 |             0.965 |           0.005 |
| Butler | modern_dots-mocr_plain | G0          |     62 |           0.946 |         0.005 |          0.943 |          0.952 |             0.962 |           0.005 |
| Butler | modern_dots-mocr_plain | G1          |     62 |           0.946 |         0.005 |          0.943 |          0.952 |             0.962 |           0.005 |
| Reeve  | expert                 | G0          |     68 |           0.95  |         0     |          0.95  |          0.95  |             0.964 |           0     |
| Reeve  | expert                 | G1          |     68 |           0.979 |         0.013 |          0.964 |          0.986 |             0.983 |           0.005 |
| Reeve  | legacy                 | G0          |     68 |           0.696 |         0     |          0.696 |          0.696 |             0.971 |           0     |
| Reeve  | legacy                 | G1          |     68 |           0.71  |         0     |          0.71  |          0.71  |             0.986 |           0     |
| Reeve  | modern_dots-mocr       | G0          |     68 |           0.957 |         0     |          0.957 |          0.957 |             0.971 |           0     |
| Reeve  | modern_dots-mocr       | G1          |     68 |           0.986 |         0     |          0.986 |          0.986 |             0.986 |           0     |
| Reeve  | modern_dots-mocr_plain | G0          |     68 |           0.971 |         0     |          0.971 |          0.971 |             0.971 |           0     |
| Reeve  | modern_dots-mocr_plain | G1          |     68 |           0.986 |         0     |          0.986 |          0.986 |             0.986 |           0     |
