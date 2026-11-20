# Sealed test outputs

- File: `sealed/test_outputs.jsonl.gz`
- SHA-256: `3b7cd6d57f8bd2e133429aea74282935b2d0b708146dfde51daca9ccc317acae`
- Responses: 320 (test pages only)
- Sealed at: 2026-11-20T00:28:07+00:00

Do not open this file before the gold labels for every test page are final.
Unseal with `python src/unseal.py 20261120-ocrladder_claude-opus-5-5_test_G1 --labeller <name>`; it checks the
gold file first and verifies this hash.
