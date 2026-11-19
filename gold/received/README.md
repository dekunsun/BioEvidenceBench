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
| 8992643, 8992644 | 2026-11-19 | labelled alone first, then discussed with an AI assistant before sending. Gloria states that the only row that came out of that discussion is `Sule Skerry Lighthouse (Sutherlandshire)` on 8992643 (it arrived marked `adjudicated`). Her independent version of 8992643 is therefore the delivered file without that row: `2026-11-19_test_8992643_gloria_independent.csv` (reconstructed on her statement). 8992644 is as she labelled it alone |

So for every page so far the independent version is on file: as delivered for five pages, and
reconstructed for 8992643. From the next delivery on, the independent version is to be sent before
any discussion, so that nothing has to be reconstructed.

## Butler taxon links (short procedure)

| File | Received | Notes |
|---|---|---|
| `2026-11-20_test_links_butler_names_gloria.tsv` | 2026-11-20 | the 29 names, pasted in chat as five tab-separated columns without a header; the header line was added on archiving, nothing else changed. No `notes` were given. Copied unchanged into `gold/gold_links_gloria_names.xlsx`/`.csv`, then `src/expand_links.py` |

## Second labeller (agreement check)

| File | Received | Notes |
|---|---|---|
| `2026-11-20_test_friend.tsv` | 2026-11-20 | 174 rows on the 5 agreement pages, pasted in chat by Gloria as the second labeller's file (tab-separated, header included); archived unchanged. Offsets were left empty, as the pack allows. Converted to CSV unchanged as `gold/gold_mentions_friend.csv` (input of `src/agreement.py`) |
