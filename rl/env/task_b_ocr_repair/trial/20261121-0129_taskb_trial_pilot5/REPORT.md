# Task B trial `20261121-0129_taskb_trial_pilot5`

Dev pages 8967011, 8992478, 9684334, 9739676, 12341902 (40 items); models claude-haiku-5-5, claude-opus-5-5; K = 8 samples per item; effort low; temperature not sent (default 1.0); prompt `repair_v1`; Reward v1.2 (rl/env/task_b_ocr_repair/REWARD_DESIGN.md).

**has_signal**: the K rewards of an item are not all equal, so GRPO's group-normalised advantage is not zero. These API models stand in for the small model to be trained; their signal share says whether the reward and item design can produce signal at all, not what the small model will see.

## Cost

| model            |   calls |    usd |   out_tok |   errors |   usd_per_call |   usd_per_page |   usd_per_item_k |
|:-----------------|--------:|-------:|----------:|---------:|---------------:|---------------:|-----------------:|
| claude-haiku-5-5 |     320 | 0.0184 |   42.9094 |        0 |         0.0001 |         0.0037 |           0.0005 |
| claude-opus-5-5  |     320 | 0.7686 |   47.7094 |        0 |         0.0024 |         0.1537 |           0.0192 |

## Format and stop reasons

| model            |   format_invalid |   integrity_invalid |   stop_not_end_turn |
|:-----------------|-----------------:|--------------------:|--------------------:|
| claude-haiku-5-5 |               17 |                  17 |                   0 |
| claude-opus-5-5  |                0 |                   0 |                   0 |

|                                       |   n |
|:--------------------------------------|----:|
| ('claude-haiku-5-5', 'several lines') |  17 |

## Within-group signal per model

| model            |   items |   signal_share |   mean_reward |   mean_std |   pass_rate |   all_pass |   none_pass |
|:-----------------|--------:|---------------:|--------------:|-----------:|------------:|-----------:|------------:|
| claude-haiku-5-5 |      40 |          0.275 |         0.647 |      0.068 |       0.453 |      0.375 |       0.475 |
| claude-opus-5-5  |      40 |          0.1   |         0.806 |      0.018 |       0.684 |      0.625 |       0.275 |

## By damage class

|                               |   items |   signal_share |   mean_reward |   mean_std |   pass_rate |   all_pass |   none_pass |
|:------------------------------|--------:|---------------:|--------------:|-----------:|------------:|-----------:|------------:|
| ('claude-haiku-5-5', '1')     |       3 |          0     |         0.333 |      0     |       0.333 |      0.333 |       0.667 |
| ('claude-haiku-5-5', '2-5')   |      21 |          0.476 |         0.483 |      0.112 |       0.167 |      0.048 |       0.714 |
| ('claude-haiku-5-5', '>5')    |       1 |          0     |         0.5   |      0     |       0     |      0     |       1     |
| ('claude-haiku-5-5', 'clean') |      15 |          0.067 |         0.95  |      0.024 |       0.908 |      0.867 |       0.067 |
| ('claude-opus-5-5', '1')      |       3 |          0     |         0.667 |      0     |       0.667 |      0.667 |       0.333 |
| ('claude-opus-5-5', '2-5')    |      21 |          0.143 |         0.719 |      0.023 |       0.56  |      0.476 |       0.381 |
| ('claude-opus-5-5', '>5')     |       1 |          0     |         0.833 |      0     |       0     |      0     |       1     |
| ('claude-opus-5-5', 'clean')  |      15 |          0.067 |         0.954 |      0.016 |       0.908 |      0.867 |       0.067 |

## By book

|                                       |   items |   signal_share |   mean_reward |   mean_std |   pass_rate |   all_pass |   none_pass |
|:--------------------------------------|--------:|---------------:|--------------:|-----------:|------------:|-----------:|------------:|
| ('claude-haiku-5-5', 'Butler')        |       8 |          0.125 |         0.734 |      0.027 |       0.531 |      0.5   |       0.375 |
| ('claude-haiku-5-5', 'Chitinskelett') |       8 |          0     |         0.688 |      0     |       0.625 |      0.625 |       0.375 |
| ('claude-haiku-5-5', 'Piscium')       |       8 |          0.625 |         0.429 |      0.144 |       0.031 |      0     |       0.875 |
| ('claude-haiku-5-5', 'Reeve')         |       8 |          0.5   |         0.667 |      0.124 |       0.5   |      0.25  |       0.375 |
| ('claude-haiku-5-5', 'Trudy')         |       8 |          0.125 |         0.719 |      0.044 |       0.578 |      0.5   |       0.375 |
| ('claude-opus-5-5', 'Butler')         |       8 |          0     |         0.812 |      0     |       0.75  |      0.75  |       0.25  |
| ('claude-opus-5-5', 'Chitinskelett')  |       8 |          0     |         0.688 |      0     |       0.625 |      0.625 |       0.375 |
| ('claude-opus-5-5', 'Piscium')        |       8 |          0.125 |         0.898 |      0.026 |       0.703 |      0.625 |       0.25  |
| ('claude-opus-5-5', 'Reeve')          |       8 |          0.25  |         0.781 |      0.034 |       0.641 |      0.5   |       0.25  |
| ('claude-opus-5-5', 'Trudy')          |       8 |          0.125 |         0.852 |      0.03  |       0.703 |      0.625 |       0.25  |
