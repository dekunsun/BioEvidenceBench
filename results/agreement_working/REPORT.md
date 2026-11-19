# Agreement: working

A = Gloria, B = second labeller. Agreement = 2 × matched / (n_A + n_B).

| book      | field       |   pages |   n_a |   n_b |   exact |   overlap |   agreement_exact |   agreement_overlap |   field_differs |   only_a |   only_b |   value_matched |   agreement_value |
|:----------|:------------|--------:|------:|------:|--------:|----------:|------------------:|--------------------:|----------------:|---------:|---------:|----------------:|------------------:|
| Butler    | taxon       |       2 |    18 |    12 |      12 |        12 |             0.8   |               0.8   |               0 |        6 |        0 |              12 |             0.8   |
| Butler    | person      |       2 |     4 |     4 |       4 |         4 |             1     |               1     |               0 |        0 |        0 |               4 |             1     |
| Butler    | locality    |       2 |    14 |    14 |      14 |        14 |             1     |               1     |               0 |        0 |        0 |              14 |             1     |
| Butler    | date        |       2 |    18 |    18 |      16 |        18 |             0.889 |               1     |               0 |        0 |        0 |              16 |             0.889 |
| Butler    | vernacular  |       2 |    11 |    11 |      11 |        11 |             1     |               1     |               0 |        0 |        0 |              11 |             1     |
| Butler    | ALL_PRIMARY |       2 |    54 |    48 |      46 |        48 |             0.902 |               0.941 |               0 |        6 |        0 |              46 |             0.902 |
| Reeve     | taxon       |       3 |    35 |    37 |      34 |        34 |             0.944 |               0.944 |               0 |        1 |        3 |              35 |             0.972 |
| Reeve     | person      |       3 |    41 |    43 |      41 |        41 |             0.976 |               0.976 |               0 |        0 |        2 |              41 |             0.976 |
| Reeve     | locality    |       3 |    17 |    17 |      10 |        16 |             0.588 |               0.941 |               0 |        1 |        1 |              10 |             0.588 |
| Reeve     | institution |       3 |    11 |    11 |      11 |        11 |             1     |               1     |               0 |        0 |        0 |              11 |             1     |
| Reeve     | vernacular  |       3 |     8 |     7 |       7 |         7 |             0.933 |               0.933 |               0 |        1 |        0 |               7 |             0.933 |
| Reeve     | ALL_PRIMARY |       3 |   104 |   108 |      96 |       102 |             0.906 |               0.962 |               0 |        2 |        6 |              97 |             0.915 |
| ALL_BOOKS | taxon       |       5 |    53 |    49 |      46 |        46 |             0.902 |               0.902 |               0 |        7 |        3 |              47 |             0.922 |
| ALL_BOOKS | person      |       5 |    45 |    47 |      45 |        45 |             0.978 |               0.978 |               0 |        0 |        2 |              45 |             0.978 |
| ALL_BOOKS | locality    |       5 |    31 |    31 |      24 |        30 |             0.774 |               0.968 |               0 |        1 |        1 |              24 |             0.774 |
| ALL_BOOKS | institution |       5 |    11 |    11 |      11 |        11 |             1     |               1     |               0 |        0 |        0 |              11 |             1     |
| ALL_BOOKS | date        |       5 |    18 |    18 |      16 |        18 |             0.889 |               1     |               0 |        0 |        0 |              16 |             0.889 |
| ALL_BOOKS | vernacular  |       5 |    19 |    18 |      18 |        18 |             0.973 |               0.973 |               0 |        1 |        0 |              18 |             0.973 |
| ALL_BOOKS | ALL_PRIMARY |       5 |   158 |   156 |     142 |       150 |             0.904 |               0.955 |               0 |        8 |        6 |             143 |             0.911 |

Disagreements to look at: 23 (`disagreements.csv`; kinds: only_a 9, boundary 8, only_b 6).
Rows left out of the span comparison (text not found on the page): 0 (`unplaced.csv`; they still count in `agreement_value`).
How rows without offsets were placed (never by looking at the other labeller): A given 177; B unique 104, reading_order 70.
`agreement_value` compares the label texts per page and field and needs no offsets.
