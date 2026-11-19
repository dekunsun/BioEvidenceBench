# Decision memo: where should the next investment in BHL data extraction go?

*Skeleton, 2026-11-20. Sections in italics are filled from the test results after the freeze.
Nothing here is a finding yet.*

**To:** a team deciding how to spend the next unit of effort on extracting structured data
(names, people, places, institutions, dates) from historical biodiversity literature.
**From:** Gloria Sun. **Evidence:** BioEvidenceBench V1, 16 locked test pages from two books
(Butler 1907, birds; Reeve 1849, shells), two LLMs, three text versions of every page.

## The decision

Four places to put the next unit of money or time:

| Option | It pays off if … | Measured by |
|---|---|---|
| A. Better OCR (re-OCR with a modern model) | most lost mentions are lost to OCR damage, and modern OCR recovers them | RQ1: value F1, legacy → modern → expert, per book |
| B. Better LLM extraction (model, prompt) | mentions are still missed or mislabelled on clean text | RQ1 expert-text F1; RQ2 gap to the rule baseline; error group "extraction/reasoning" |
| C. Automated verification (evidence, checks) | unsupported or silently corrected values are common, and evidence removes them cheaply | RQ3: unsupported-output rate and recall, G1 vs G0 |
| D. Human review, prioritised | errors concentrate where the models disagree or checks fail | RQ4: errors inside vs outside the flagged set; risk-coverage curve |
| (E. Entity resolution) | names survive extraction but are lost or mislinked at the database step | E4-lite: loss at linking vs before it (Butler) |

## What the evidence says

*One short paragraph per option, with the per-book number and its interval. Say "inconclusive"
where the interval spans the pre-registered threshold.*

- *OCR:* …
- *Extraction:* …
- *Verification:* …
- *Review prioritisation:* …
- *Entity resolution:* …

## Recommendation

*One paragraph: the order of investment for books like these two, and the condition under which
it would change (e.g. "if a collection's legacy CER is below X, skip re-OCR and …"). If there is
no single threshold, say so and say what to measure first on a new collection.*

## What this does not show

- Two books and 16 pages: a direction for a pilot, not a rule for all of BHL.
- Book and OCR quality are confounded; per-book results only.
- Agreement between two models is not correctness (on dev, both copied the same OCR damage).
- No real review-time study: workload in RQ4 is counted in mentions, not minutes.
- The texts are public and may be in the models' training data.

## Cost

*API cost per page for each configuration, and labelling time per page (Gloria's estimate).*
