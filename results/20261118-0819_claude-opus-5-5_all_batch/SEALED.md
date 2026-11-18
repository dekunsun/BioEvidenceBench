# Sealed test outputs

- File: `sealed/test_outputs.jsonl.gz`
- SHA-256: `0b7a4a024a685ab50cd5759f9e19a08b43130aa05e6bb1402cbb1b78a089445d`
- Responses: 96 (test pages only)
- Sealed at: 2026-11-18T08:22:58+00:00

Do not open this file before the gold labels for every test page are final.
Unseal with `python src/unseal.py 20261118-0819_claude-opus-5-5_all_batch --labeller <name>`; it checks the
gold file first and verifies this hash.
