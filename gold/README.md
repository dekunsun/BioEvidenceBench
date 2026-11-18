# gold/

Gloria's independent gold labels. Nothing in this folder is ever created or pre-filled by a model or a script (CLAUDE.md, rule 1).

- `gold_mentions_TEMPLATE.csv`: copy to `gold_mentions_<labeller>.csv`. One row per mention (see ANNOTATION_GUIDE.md section 1).
- `gold_links_TEMPLATE.csv`: copy to `gold_links_<labeller>.csv`. Butler taxon linking, done after the mentions (guide section 3).
- `python src/check_gold.py gold/gold_mentions_<labeller>.csv` checks offsets and writes `*.checked.csv` next to it. It never edits your file.

Label test pages before any model output exists for them.
