"""Run src/run_extraction.py with models whose prices the frozen file does not list
(exploratory runs after the freeze; DEVIATIONS.md). The frozen file is imported, not edited,
so FREEZE.json still verifies. Same arguments as run_extraction.py.

    python src/run_extraction_x.py --model claude-fable-5-2 --pages test ...
"""
import run_extraction as rx

# $ per million tokens: input, output, cache write, cache read (Claude API pricing, 2026-11).
rx.PRICES.setdefault("claude-fable-5-2", (8.00, 40.00, 10.00, 0.20))

if __name__ == "__main__":
    rx.main()
