# Gemini Batch API: is response_json_schema enforced?

Run 20261120-0655. Model `gemini-4-carbon` (API reports version `3.0`), SDK google-genai 3.6.1, endpoint https://generativelanguage.googleapis.com/ v1beta. Batch submitted 2026-11-20T07:01:34+00:00, final state JOB_STATE_SUCCEEDED.
Identical requests (frozen G1 prompt, expert text, dev pages; `requests.json`) sent synchronously and as one inline batch. Every answer is checked against the schema in code.
Schema sent in the field `response_schema` (with `additionalProperties` removed: the field does not take it).

| mode   |   page_id | finish   | follows_schema   | deviation   | top_level_type   |   prompt_tokens |   thought_tokens |    usd |
|:-------|----------:|:---------|:-----------------|:------------|:-----------------|----------------:|-----------------:|-------:|
| sync   |   8992582 | STOP     | True             |             | dict             |            2973 |             2232 | 0.0323 |
| sync   |   8992601 | STOP     | True             |             | dict             |            3008 |             1066 | 0.0211 |
| sync   |   8992612 | STOP     | True             |             | dict             |            2679 |             1059 | 0.0276 |
| batch  |   8992582 | STOP     | True             |             | dict             |            2973 |             2396 | 0.0195 |
| batch  |   8992601 | STOP     | True             |             | dict             |            3008 |              870 | 0.0096 |
| batch  |   8992612 | STOP     | True             |             | dict             |            2679 |             1189 | 0.017  |

Total cost (computed from token counts): $0.127.