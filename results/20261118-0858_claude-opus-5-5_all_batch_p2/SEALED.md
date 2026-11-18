# Sealed test outputs

- File: `sealed/test_outputs.jsonl.gz`
- SHA-256: `96655f69ec6e884520e33b1f9f3e81569ab7ba24082e8cdd476ed8e593824a9b`
- Responses: 96 (test pages only)
- Sealed at: 2026-11-18T09:01:46+00:00

Do not open this file before the gold labels for every test page are final.
Unseal with `python src/unseal.py 20261118-0858_claude-opus-5-5_all_batch_p2 --labeller <name>`; it checks the
gold file first and verifies this hash.
