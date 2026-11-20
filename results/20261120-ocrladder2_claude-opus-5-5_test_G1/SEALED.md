# Sealed test outputs

- File: `sealed/test_outputs.jsonl.gz`
- SHA-256: `c569c40c69ffb32548c57920cc5b03536c37bfa7fde0279c07d29c5a08731e50`
- Responses: 16 (test pages only)
- Sealed at: 2026-11-20T00:28:09+00:00

Do not open this file before the gold labels for every test page are final.
Unseal with `python src/unseal.py 20261120-ocrladder2_claude-opus-5-5_test_G1 --labeller <name>`; it checks the
gold file first and verifies this hash.
