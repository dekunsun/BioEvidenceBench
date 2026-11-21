# Sealed test outputs

- File: `sealed/test_outputs.jsonl.gz`
- SHA-256: `feb5d05c09d0de21636946489559b95b35830d2148b18eb7d4437c780736e988`
- Responses: 16 (test pages only)
- Sealed at: 2026-11-21T23:26:22+00:00

Do not open this file before the gold labels for every test page are final.
Unseal with `python src/unseal.py 20261121-sftrepair_claude-opus-5-5_test_G1 --labeller <name>`; it checks the
gold file first and verifies this hash.
