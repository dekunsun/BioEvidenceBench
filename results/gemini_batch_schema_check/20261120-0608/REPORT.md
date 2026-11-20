# Gemini Batch API: is response_json_schema enforced?

Run 20261120-0608. Model `gemini-4-carbon` (API reports version `3.0`), SDK google-genai 3.6.1, endpoint https://generativelanguage.googleapis.com/ v1beta. Batch submitted 2026-11-20T06:10:18+00:00, final state JOB_STATE_SUCCEEDED.
Identical requests (frozen G1 prompt, expert text, dev pages; `requests.json`) sent synchronously and as one inline batch. Every answer is checked against the schema in code.

| mode   |   page_id | finish   | follows_schema   | deviation   | top_level_type   |   prompt_tokens |   thought_tokens |    usd |
|:-------|----------:|:---------|:-----------------|:------------|:-----------------|----------------:|-----------------:|-------:|
| sync   |   8992582 | STOP     | True             |             | dict             |            2981 |             2632 | 0.0363 |
| sync   |   8992601 | STOP     | True             |             | dict             |            3016 |                0 | 0.0128 |
| sync   |   8992612 | STOP     | True             |             | dict             |            2687 |              804 | 0.0301 |
| batch  |   8992582 | STOP     | False            | bare_array  | list             |            2814 |             4656 | 0.0281 |
| batch  |   8992601 | STOP     | False            | bare_array  | list             |            2849 |             3437 | 0.0223 |
| batch  |   8992612 | STOP     | False            | bare_array  | list             |            2520 |             2727 | 0.022  |

Total cost (computed from token counts): $0.152.