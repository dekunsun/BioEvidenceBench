# Sealed test outputs

- File: `sealed/test_outputs.jsonl.gz`
- SHA-256: `148c706ae147a9c1ffc36a15893537b57d5f2113f8281b23cc406ec17cc9c52b`
- Responses: 128 (test pages only)
- Sealed at: 2026-11-19T20:59:27+00:00

Do not open this file before the gold labels for every test page are final.
Unseal with `python src/unseal.py 20261119-2052_claude-opus-5-5_test_batch --labeller <name>`; it checks the
gold file first and verifies this hash.
