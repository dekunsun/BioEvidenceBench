# Four Claude models, G1, test pages (exploratory)

ALL_PRIMARY value F1 with 95% page-bootstrap interval, per book. Same prompt p4-guide-v0.6. Opus is the frozen pre-registered run; the others were run after unsealing (DEVIATIONS.md).

| model                           | ('Butler', 'expert')   | ('Butler', 'legacy')   | ('Butler', 'modern_dots-mocr')   | ('Butler', 'modern_dots-mocr_plain')   | ('Reeve', 'expert')   | ('Reeve', 'legacy')   | ('Reeve', 'modern_dots-mocr')   | ('Reeve', 'modern_dots-mocr_plain')   |
|:--------------------------------|:-----------------------|:-----------------------|:---------------------------------|:---------------------------------------|:----------------------|:----------------------|:--------------------------------|:--------------------------------------|
| claude-fable-5-2                | 0.964 [0.93-0.99]      | 0.596 [0.43-0.74]      | 0.956 [0.93-0.98]                | nan                                    | 0.988 [0.98-1.00]     | 0.648 [0.53-0.73]     | 0.981 [0.96-1.00]               | nan                                   |
| claude-haiku-5-5                | 0.956 [0.94-0.97]      | 0.610 [0.46-0.75]      | 0.941 [0.92-0.97]                | nan                                    | 0.962 [0.95-0.98]     | 0.604 [0.50-0.70]     | 0.945 [0.92-0.98]               | nan                                   |
| claude-opus-5-5 (batch, frozen) | 0.982 [0.95-1.00]      | 0.597 [0.45-0.74]      | 0.952 [0.92-0.98]                | 0.967 [0.93-0.99]                      | 0.981 [0.97-1.00]     | 0.638 [0.52-0.72]     | 0.977 [0.95-1.00]               | 0.977 [0.95-1.00]                     |
| claude-sonnet-5-5               | 0.903 [0.86-0.96]      | 0.581 [0.44-0.69]      | 0.927 [0.89-0.96]                | nan                                    | 0.944 [0.91-0.98]     | 0.635 [0.52-0.71]     | 0.965 [0.93-0.99]               | nan                                   |

Cost (all requests of the run, test pages; per request = one page x one text version x one condition):

| model                           |   requests_all |   usd_total_run |   usd_per_request |   usd_per_1000_pages | mode            | note               |
|:--------------------------------|---------------:|----------------:|------------------:|---------------------:|:----------------|:-------------------|
| claude-opus-5-5 (batch, frozen) |            128 |           1.499 |            0.0117 |                11.71 | batch (50% off) | 4 versions x G0,G1 |
| claude-sonnet-5-5               |             48 |           0.486 |            0.0101 |                10.12 | sync            | 3 versions x G1    |
| claude-haiku-5-5                |             48 |           0.072 |            0.0015 |                 1.49 | sync            | 3 versions x G1    |
| claude-fable-5-2                |             48 |           2.071 |            0.0432 |                43.15 | sync            | 3 versions x G1    |
