# Sealed test outputs

- File: `sealed/test_outputs.jsonl.gz`
- SHA-256: `f044c7f31e2ace4283ce2419182d53bd5b90fb3668b2fc74aaad6050eb4fc223`
- Responses: 48 (test pages only)
- Sealed at: 2026-11-20T01:50:07+00:00

Do not open this file before the gold labels for every test page are final.
Unseal with `python src/unseal.py 20261120-0148_claude-fable-5-2_test_sync --labeller <name>`; it checks the
gold file first and verifies this hash.
