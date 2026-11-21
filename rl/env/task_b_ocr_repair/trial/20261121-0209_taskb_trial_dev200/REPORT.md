# Task B trial `20261121-0209_taskb_trial_dev200`

Dev pages 8967007, 8967008, 8967015, 8967016, 8967076, 8967079, 8967083, 8967309, 8967313, 8967314, 8967317, 8967321, 8967343, 8967344, 8967349, 8967350, 8992423, 8992424, 8992428, 8992429, 8992430, 8992431, 8992434, 8992436, 8992467, 8992468, 8992469, 8992473, 8992474, 8992475, 8992479, 9684324, 9684325, 9684326, 9684327, 9684328, 9684335, 9739677, 9739678, 9739679, 9739680, 9739724, 9739725, 9739726, 9739727, 9739728, 12341905, 12341908, 12341909, 12342144, 12342145, 12342147, 12342148, 12342149, 12342151, 12342152, 12342264, 12342265, 12342266, 12342267, 12342268, 12342269, 12342271, 12342272, 12342273, 12342274, 12342277, 12342278, 12342279, 12342280, 12342281, 12342282, 12342304 (200 items); models claude-haiku-5-5, claude-opus-5-5; K = 8 samples per item; effort low; temperature not sent (default 1.0); prompt `repair_v2`; Reward v1.2 (rl/env/task_b_ocr_repair/REWARD_DESIGN.md).

**has_signal**: the K rewards of an item are not all equal, so GRPO's group-normalised advantage is not zero. These API models stand in for the small model to be trained; their signal share says whether the reward and item design can produce signal at all, not what the small model will see.

## Cost

| model            |   calls |    usd |   out_tok |   errors |   usd_per_call |   usd_per_page |   usd_per_item_k |
|:-----------------|--------:|-------:|----------:|---------:|---------------:|---------------:|-----------------:|
| claude-haiku-5-5 |    1600 | 0.0979 |   44.4212 |        0 |         0.0001 |         0.0013 |           0.0005 |
| claude-opus-5-5  |    1600 | 4.1381 |   51.3519 |        0 |         0.0026 |         0.0567 |           0.0207 |

## Format and stop reasons

| model            |   format_invalid |   integrity_invalid |   stop_not_end_turn |
|:-----------------|-----------------:|--------------------:|--------------------:|
| claude-haiku-5-5 |              139 |                 139 |                   0 |
| claude-opus-5-5  |                7 |                   7 |                   0 |

|                                       |   n |
|:--------------------------------------|----:|
| ('claude-haiku-5-5', 'several lines') | 139 |
| ('claude-opus-5-5', 'several lines')  |   7 |

## Within-group signal per model

| model            |   items |   signal_share |   mean_reward |   mean_std |   pass_rate |   all_pass |   none_pass |
|:-----------------|--------:|---------------:|--------------:|-----------:|------------:|-----------:|------------:|
| claude-haiku-5-5 |     200 |           0.32 |         0.553 |      0.074 |       0.396 |      0.345 |       0.535 |
| claude-opus-5-5  |     200 |           0.24 |         0.767 |      0.049 |       0.594 |      0.52  |       0.33  |

## By damage class

|                               |   items |   signal_share |   mean_reward |   mean_std |   pass_rate |   all_pass |   none_pass |
|:------------------------------|--------:|---------------:|--------------:|-----------:|------------:|-----------:|------------:|
| ('claude-haiku-5-5', '2-5')   |     164 |          0.372 |         0.463 |      0.086 |       0.278 |      0.226 |       0.646 |
| ('claude-haiku-5-5', 'clean') |      36 |          0.083 |         0.964 |      0.022 |       0.931 |      0.889 |       0.028 |
| ('claude-opus-5-5', '2-5')    |     164 |          0.28  |         0.723 |      0.057 |       0.521 |      0.439 |       0.39  |
| ('claude-opus-5-5', 'clean')  |      36 |          0.056 |         0.965 |      0.011 |       0.931 |      0.889 |       0.056 |

## By book

|                                       |   items |   signal_share |   mean_reward |   mean_std |   pass_rate |   all_pass |   none_pass |
|:--------------------------------------|--------:|---------------:|--------------:|-----------:|------------:|-----------:|------------:|
| ('claude-haiku-5-5', 'Butler')        |      40 |          0.075 |         0.851 |      0.026 |       0.722 |      0.7   |       0.25  |
| ('claude-haiku-5-5', 'Chitinskelett') |      40 |          0.375 |         0.596 |      0.078 |       0.378 |      0.325 |       0.525 |
| ('claude-haiku-5-5', 'Piscium')       |      40 |          0.525 |         0.312 |      0.112 |       0.138 |      0.075 |       0.8   |
| ('claude-haiku-5-5', 'Reeve')         |      40 |          0.375 |         0.55  |      0.088 |       0.403 |      0.35  |       0.525 |
| ('claude-haiku-5-5', 'Trudy')         |      40 |          0.25  |         0.458 |      0.067 |       0.338 |      0.275 |       0.575 |
| ('claude-opus-5-5', 'Butler')         |      40 |          0.125 |         0.91  |      0.037 |       0.809 |      0.75  |       0.15  |
| ('claude-opus-5-5', 'Chitinskelett')  |      40 |          0.2   |         0.841 |      0.041 |       0.703 |      0.625 |       0.25  |
| ('claude-opus-5-5', 'Piscium')        |      40 |          0.425 |         0.657 |      0.07  |       0.359 |      0.25  |       0.5   |
| ('claude-opus-5-5', 'Reeve')          |      40 |          0.25  |         0.793 |      0.047 |       0.606 |      0.5   |       0.325 |
| ('claude-opus-5-5', 'Trudy')          |      40 |          0.2   |         0.632 |      0.048 |       0.494 |      0.475 |       0.425 |

## Pass-rate distribution (share of items)

| model            |     0 |   (0.1, 0.9] |     1 |
|:-----------------|------:|-------------:|------:|
| claude-haiku-5-5 | 0.535 |         0.12 | 0.345 |
| claude-opus-5-5  | 0.33  |         0.15 | 0.52  |

Items with a pass rate in (0.1, 0.9] are the plan's mid-difficulty band (plan 9).
