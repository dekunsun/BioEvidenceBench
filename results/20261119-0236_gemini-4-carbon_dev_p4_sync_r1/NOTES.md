# Read this first

Gemini 4 Carbon, prompt `p4-guide-v0.6`, sync mode with the JSON schema enforced, DEV pages only.
**Complete: 48 of 48 requests answered**, all `STOP`, 0 errors, 0 schema deviations.
`cost.json` → `usd_total` **$1.31** (computed from token counts, answers on disk only).

The run was made in three attempts (`config.json` → `resumed`):

1. The first attempt crashed after 18 answers when the session's network proxy dropped a
   connection (`httpx ReadError`; the runner did not catch it then).
2. `--resume` (added for this) kept the 18 answers and sent the rest with 2 workers. It stopped
   at the $1.30 cap with 45 answers ($1.21 on disk): the cap also counted an allowance for
   answers that were lost to dropped connections but may have been billed.
3. Gloria approved a higher cap (2026-11-19). `--resume ... --max-usd 1.80 --unrecorded-usd 0.15`
   sent only the three requests never sent, all for Reeve page 8967147:
   `modern_dots-mocr` G1 ($0.045), `modern_dots-mocr_plain` G0 ($0.027) and G1 ($0.026),
   **$0.098 together**, no dropped connections.

Not in `usd_total`: four connections were dropped mid-request in attempts 1 and 2. Google may
have billed those lost answers (allowance $0.15, see `cost.json` → `not_in_usd_total`); check the
Google billing page for the exact figure. One request was unusually expensive:
`8992612__legacy__G0` used 15,806 thinking tokens ($0.168; the others average about $0.024).

Dev pages are not blind (guide and prompt were written from them): a pipeline check, not a result.
