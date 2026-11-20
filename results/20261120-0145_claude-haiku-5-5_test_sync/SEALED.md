# Sealed test outputs

- File: `sealed/test_outputs.jsonl.gz`
- SHA-256: `1def56360c0d14d3edb04974c85299d188929bbad231b573134ff17517f55e8d`
- Responses: 48 (test pages only)
- Sealed at: 2026-11-20T01:47:51+00:00

Do not open this file before the gold labels for every test page are final.
Unseal with `python src/unseal.py 20261120-0145_claude-haiku-5-5_test_sync --labeller <name>`; it checks the
gold file first and verifies this hash.
