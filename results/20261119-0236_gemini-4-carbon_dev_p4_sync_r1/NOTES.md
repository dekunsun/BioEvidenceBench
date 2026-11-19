# Read this first

Gemini 4 Carbon, prompt `p4-guide-v0.6`, sync mode with the JSON schema enforced, DEV pages only.
**45 of 48 requests were answered; 3 were never sent** because the run stopped at its $1.30 cap:

- `8967147__modern_dots-mocr__G1`
- `8967147__modern_dots-mocr_plain__G0`
- `8967147__modern_dots-mocr_plain__G1`

(Reeve page 8967147.) The 45 answers: all `STOP`, 0 errors, 0 schema deviations.

What happened: the first attempt crashed after 18 answers when the session's network proxy dropped a
connection (`httpx ReadError`; the runner did not catch it). The run was continued with
`--resume` (added for this; see `config.json` → `resumed`), which kept the 18 answers and sent
only the missing requests with 2 workers.

Cost: `cost.json` → `usd_total` $1.21 is the cost of the 45 answers on disk, computed from token
counts. Four connections were dropped mid-request (2 in each attempt; 2 retried successfully in
the resume). Google may have billed those lost answers, so the cap also counted an allowance
($0.10 for the first attempt, the run's mean request cost per drop in the resume): $1.36 counted
≥ $1.30, so the last three requests were not started. One request was unusually expensive:
`8992612__legacy__G0` used 15,806 thinking tokens ($0.168; the others average $0.024).

Dev pages are not blind (guide and prompt were written from them): a pipeline check, not a result.
