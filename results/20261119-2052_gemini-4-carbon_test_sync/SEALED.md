# Sealed test outputs

- File: `sealed/test_outputs.jsonl.gz`
- SHA-256: `ce530a10717409af6e09f9ee6d1dd885597a626aa70a783c5423683d089f4255`
- Responses: 128 (test pages only)
- Sealed at: 2026-11-19T21:30:28+00:00

Do not open this file before the gold labels for every test page are final.
Unseal with `python src/unseal.py 20261119-2052_gemini-4-carbon_test_sync --labeller <name>`; it checks the
gold file first and verifies this hash.
