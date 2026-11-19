# Notes on this run

**Batch mode, schema not enforced, bare arrays wrapped.**

- Sent through Google's Batch API (inline requests). The SDK put `responseJsonSchema` into every
  request, but the answers show the schema was not enforced: 44 of 48 are a bare JSON array of
  mentions instead of `{"mentions": [...]}`, 3 have another wrong shape, and the prompt token
  counts are lower than the sync pilot's for the same page by about the size of the schema.
  Thinking tokens were about 2.4 times those of the sync pilot.
- `gemini_backend.check_shape` validated every answer afterwards. A bare array of valid mention
  objects was wrapped as `{"mentions": [...]}` (`schema_deviation: "bare_array"` in the record;
  values untouched). The 3 other shapes are `parsed: null`, i.e. parse errors:
  `8992582__legacy__G1`, `8967047__legacy__G1`, `8967147__modern_dots-mocr_plain__G0`.
  `8967047__legacy__G0` is a valid answer with no mentions (`empty`).
- Raw responses in `dev_outputs.jsonl` are exactly what the API returned. The records were rebuilt
  from them with `python src/run_extraction.py --reparse <run_id>` (no API call).
- So this run is NOT the same setting as the sync pilot
  (`20261119-0216_gemini-4-carbon_dev5_sync_p4`, schema enforced, 40/40 valid) or as the Opus runs
  (schema enforced). Read its scores with that caveat. Dev pages only; pipeline check, not a result.
