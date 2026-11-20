# Sealed test outputs

- File: `sealed/test_outputs.jsonl.gz`
- SHA-256: `514f70ef52642b242fe3b194254922f9577f915460c1103e0d1e5a41bcd12251`
- Responses: 48 (test pages only)
- Sealed at: 2026-11-20T01:45:07+00:00

Do not open this file before the gold labels for every test page are final.
Unseal with `python src/unseal.py 20261120-0143_claude-sonnet-5-5_test_sync --labeller <name>`; it checks the
gold file first and verifies this hash.
