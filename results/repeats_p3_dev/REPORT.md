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

## F1 per repeat

Not computed: there are no dev gold labels yet. Re-run with `--gold` once the 6 dev
pages are labelled.
