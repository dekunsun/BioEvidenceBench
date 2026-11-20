# Labelling guide addendum (after the freeze)

`ANNOTATION_GUIDE.md` (v0.10) is frozen (`FREEZE.json`) and is not edited. Rules Gloria decides after
the freeze are listed here, newest first. They apply to labelling done after the freeze (the PCAS
case, any later pages); they never change the frozen test gold or its scores.

| Date | Rule | Field | Decided by | First used on |
|---|---|---|---|---|
| 2026-11-20 | A joint authority citation joined by `&` is **one** `person` span: `H. & A.` (Hooker & Arnott), `Torr. & Gr.`, `T. & G.` | person | Gloria ("H. & A. 算一个人名就行"), after seeing model outputs on PCAS | PCAS gold (already labelled this way; no row changed) |
| 2026-11-20 | A sub-unit and its parent written narrow to wide (`Division of Agrostology, U. S. Department of Agriculture`) is one `institution` span, by analogy with the locality rule (guide v0.6) | institution | Gloria ("按建议"), after seeing model outputs on PCAS | PCAS adjudicated gold |
