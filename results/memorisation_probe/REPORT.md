# Memorisation probe (exploratory)

Changes to gold names in the 16 test pages' expert text, then G2 repair. `restored` on a *swap* (a fluent, error-free substitution) can only come from memory of the page, or from the original name printed elsewhere on the same page (split below).

|                              |   kept |   not_extracted |   other |   restored |   n |
|:-----------------------------|-------:|----------------:|--------:|-----------:|----:|
| ('claude-fable-5-2', 'swap') |     29 |               0 |       0 |          0 |  29 |
| ('claude-fable-5-2', 'typo') |      0 |               0 |       1 |         68 |  69 |
| ('claude-haiku-5-5', 'swap') |     28 |               1 |       0 |          0 |  29 |
| ('claude-haiku-5-5', 'typo') |     12 |               1 |       2 |         54 |  69 |
| ('claude-opus-5-5', 'swap')  |     29 |               0 |       0 |          0 |  29 |
| ('claude-opus-5-5', 'typo')  |      2 |               0 |       2 |         65 |  69 |

Swaps, by whether the original name is printed elsewhere on the page:

|                             |   kept |   not_extracted |
|:----------------------------|-------:|----------------:|
| ('claude-fable-5-2', False) |     22 |               0 |
| ('claude-fable-5-2', True)  |      7 |               0 |
| ('claude-haiku-5-5', False) |     22 |               0 |
| ('claude-haiku-5-5', True)  |      6 |               1 |
| ('claude-opus-5-5', False)  |     22 |               0 |
| ('claude-opus-5-5', True)   |      7 |               0 |
