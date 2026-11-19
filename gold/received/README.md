# Labels as received

One file per delivery, exactly as Gloria sent it (pasted rows are typed into CSV unchanged), and
committed **before** any comparison with another labeller or an AI assistant and before any
adjudication. These files are never edited afterwards. The working gold files one level up start
from them; every later change is logged in `gold_changes_<labeller>.csv`.

Test-page labels live in `gold/gold_mentions_gloria_test.csv` until all 16 pages are labelled and
adjudicated; dev-page labels are in `gold/gold_mentions_gloria.csv`.
