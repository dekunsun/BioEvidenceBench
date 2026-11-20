# Sealed test outputs

- File: `sealed/test_outputs.jsonl.gz`
- SHA-256: `65221fd4c5caf6c58b88f9476e7527377956c4a96379fd2eedbb193f804a6245`
- Responses: 16 (test pages only)
- Sealed at: 2026-11-20T19:29:19+00:00

Do not open this file before the gold labels for every test page are final.
Unseal with `python src/unseal.py 20261120-ocrladder3_claude-opus-5-5_test_G1 --labeller <name>`; it checks the
gold file first and verifies this hash.
