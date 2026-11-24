# 036-1b delivery (本草綱目 pilot, dev), 2026-11-24

- Archived unchanged: `2026-11-24_bencao_036-1b_gloria.xlsx` (SHA-256 5723cfcadc32b1b05ba1a3e80e5eb9867585d521c232a86e48900bf4bf265b87), sheet 「标注」, 38 rows.
- Mechanical fix only: in the delivered sheet the `qualifier` and `text` columns are swapped (the entity strings
  are under `qualifier`, the qualifier words under `text`; the workbook layout changed when the `qualifier`
  column was added). `gold/gold_mentions_bencao_gloria.csv` swaps them back; no label was added, removed or changed.
- Offsets computed against `data/bencao/verified_plain/036-1b.txt`, repeated strings matched in reading order
  within the line; every span checked to equal its text.
- Provenance and labelling time: asked of the author on 2026-11-24 (see chat).
- The author, 2026-11-24: notes saying 留待人工裁定 / 需人工決定 mean the item is left for a domain expert. Those 7 rows carry `adjudication = expert_pending` (log: `gold/gold_changes_bencao_gloria.csv`); until an expert decides they are optional in scoring (neither required nor counted as false positives).
