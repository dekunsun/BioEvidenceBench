# Read this first

The Gemini run here is `20261119-0236_gemini-4-carbon_dev_p4_sync_r1` (sync, schema enforced). It has 45 of 48 answers: for **Reeve page
8967147** the requests `modern_dots-mocr` G1 and `modern_dots-mocr_plain` G0 and G1 were never sent
(cost cap, see the run's NOTES.md). The scorer counts a missing request as "no predictions", and
`outcomes.csv` lists only the 45 requests that exist. So every Gemini row for **Reeve ×
modern_dots-mocr G1 / modern_dots-mocr_plain** (value F1 0.635, 34 predictions for 70 gold; RQ4
flagged share 0.48, "against" verdicts) is lowered by the missing page and says nothing about the
model. All Butler rows and Reeve expert / legacy rows are complete.

The earlier analyses with the batch run r1 (schema not enforced) are in
`results/analysis_dev_p4_rq4_gemini_batch/`.

Dev pages only and not blind: a pipeline check, not a result.
