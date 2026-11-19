# Labels as received

One file per delivery, exactly as Gloria sent it (pasted rows are typed into CSV unchanged), and
committed **before** any comparison with another labeller or an AI assistant and before any
adjudication. These files are never edited afterwards. The working gold files one level up start
from them; every later change is logged in `gold_changes_<labeller>.csv`.

Test-page labels live in `gold/gold_mentions_gloria_test.csv` until all 16 pages are labelled and
adjudicated; dev-page labels are in `gold/gold_mentions_gloria.csv`.

## How each delivery was made (as told by Gloria)

| Pages | Delivered | Process |
|---|---|---|
| 8992328, 8992379, 8992408, 8992489 | 2026-11-19 | labelled alone; sent with open `UNCLEAR` rows, which were adjudicated afterwards in the Claude Code session |
| 8992643, 8992644 | 2026-11-19 | labelled alone first, then **single rows were discussed with an AI assistant before sending**; the file here is the version after that discussion (one row of 8992643 arrived already marked `adjudicated`). The first, pre-discussion version was not sent |

So "archived before any comparison" holds for the first four pages only. From the next delivery
on, the first independent version is to be sent before any discussion.
