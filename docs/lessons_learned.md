# Lessons learned

What went wrong while building and running BioEvidenceBench, what it taught, and where the record
is. The biggest lesson: **most of the work in an evaluation is not calling the model. It is
deciding what counts as right, and keeping those decisions out of the thing being tested.** Every
item below actually happened; each fix and its reason is in `DEVIATIONS.md`, a change log in
`gold/`, or the commit history.

## A. Labels and the gold set

| What happened | Lesson | What to do next time |
| --- | --- | --- |
| The guide went from v0.1 to v0.10; almost every page raised a new case (is `insects` a vernacular name? a word inside a cited title? a bare epithet like `Darwinii`?) | The guide keeps growing | Version it and keep a changelog. Rules found on test pages go into the guide and the gold, never into the prompt; mark the affected rows (`later_rule`) and report scores with and without them |
| The expert transcription itself had typos (`nontifringilla` for `montifringilla`, `I898` for `1898`) | "Ground truth" has errors too | Keep gold offsets on the transcription, record the scan's reading in a separate column (`scan_text`), accept both, and list known errata |
| Two labellers agreed on only 0.75 of localities exactly, almost all at span edges (habitat brackets, `shores of`, compound place names) | Boundaries are harder than categories | Report exact and overlap agreement side by side; put more boundary examples in the guide |
| Two test pages were labelled alone, then discussed with an AI assistant before being sent | Independence needs a record | Archive every delivery unchanged before any comparison; log changes that came from discussion and rebuild the independent version |
| Two examples in the guide came from the second labeller's own pages | Material for a second labeller can leak the answer | Make a labeller copy: same rules, invented examples, no changelog |
| A page sampled as "no entities" by TaxonFinder had two mentions under the guide | Automatic detectors cannot define strata | Use strata only to secure coverage, and say so in the report |
| On the botany case, the labeller (labelling against scans, a new kind of text) put titles inside person names, against a rule she had applied on every test page | Labellers forget existing rules on new material | Re-read the boundary rules before a new domain; when adjudicating after seeing model output, report both versions, because every fix moves the gold towards the model |

## B. Experimental discipline

| What happened | Lesson | What to do next time |
| --- | --- | --- |
| The guide and prompt were written from the dev pages; dev F1 was 1.000 | The dev set will saturate | Seal test outputs from the first call; treat dev numbers as pipeline checks only |
| A spoken "we won't change it any more" is not checkable | A freeze must be machine-checkable | `FREEZE.json` holds the hashes, the unseal script verifies them first; the pre-registration itself is frozen, so deviations go in a separate `DEVIATIONS.md`. (A change log appended to a frozen file broke the check once; it was moved out and the check is clean again) |
| The most interesting findings (LLM repair, the LLM linker) came after seeing the results | Post-unsealing experiments are exploratory | Report them apart from the pre-registered results; to count, they need a fresh test set |
| Google's batch interface did not enforce the output schema (44 of 48 answers in the wrong shape); a dropped proxy connection crashed a run halfway | The call mode is a variable too | Freeze the call mode with the configuration; retry a failed request once and record both attempts; make runs resumable |
| RQ4 left 0 to 2 "unflagged" predictions per cell | A new question can make an old threshold meaningless | Write a minimum sample size into the pre-registration and report "too few to compare" rather than force a verdict |

## C. Metrics and analysis

| What happened | Lesson | What to do next time |
| --- | --- | --- |
| OCR models with a low page error rate still kept only 57-80% of Butler's names intact | Metrics should match the use | Measure name preservation and value-level F1 directly |
| On legacy OCR, lenient F1 was 0.93-0.97 while value F1 was 0.60-0.64 | Separate "found the right place" from "copied the right characters" | Report all three match levels; the gap between them is itself the diagnosis |
| A misread name is one miss plus one extra output in the scorer: 396 scorer rows were 183 cases | Attribute errors per case, not per scorer row | Merge first, group by facts, show what the input held at that place; leave only the judgment to a person |
| Two models from different providers agreed on 99% of outputs, errors included | Agreement is not correctness | Validate any review signal against the gold set; do not assume multi-model voting helps |
| Requiring a verbatim quote changed no accuracy number | A null result is a statement about the metric | Both arms took values from the source by code, so the test compared two forms of verification. Evidence's value is traceability and audit cost; measure those (traceable share, reviewer time per value, errors caught with and without evidence) |
| GBIF's website shows new taxon codes while the API keeps numeric keys; the backbone has no subfamily rank; `Passer` has a homonym | External databases have their own traps | The labeller writes accepted names; a script finds keys by exact, rank-checked match and lists what it cannot resolve |
| 19 of 21 "unsure" spot-check rows were index entries | Much apparent model error is undefined scope | Write the scope (index pages, authorities, broad vernacular words) before scaling; one scope rule cut the review queue by 60% |

## D. Working with an AI assistant

The project was built with Claude Code, and Claude is one of the model families under evaluation.
The rules that worked all **separate powers: the AI does engineering and gathers facts; a person
makes every judgment, and every judgment leaves a record.**

| Rule | Why it mattered |
| --- | --- |
| The AI never writes or pre-fills gold labels; it types in only decisions the labeller made explicitly, each logged | A model under test must not help set the exam; every change traces to who, when and which sentence |
| The AI does not review test labels for omissions or attribute errors | Same reason; it supplies facts ("is this word in the OCR input?"), the person judges |
| Deliveries are archived and committed unchanged before any comparison | Independence of the labels can be shown afterwards |
| A small paid pilot first, cost per page reported, then a go-ahead; a cap on every run | Total API spend $55.96 (per run in `eval_settings.md`), no overrun |
| Caps need headroom | One Gemini cap set too tight left 3 requests unsent and cost a re-run |
| Decisions go into `CLAUDE.md` with the date and the labeller's own words | After a new session or a context reset, the assistant still knows what is settled |
| Questions that need a person are grouped, each with a recommendation | 23 disagreements in 9 groups were adjudicated in one sentence |
| Exploratory work is logged as a deviation before a conclusion is written | A post-hoc experiment is never presented as a pre-registered result |

Pitfalls met on the way: reading a pasted spreadsheet row by position (paste whole rows with
context, or send the xlsx); placing a second labeller's mention when its text occurs twice on the
page (marked as inferred); Excel on a Mac not reading UTF-8 CSV (send xlsx); legacy OCR decoded
with the wrong encoding (`â`); a batch API refusing a dot in a request id; GBIF website codes
differing from API keys.

## E. When the platform fails silently

Twice, across two projects, a model API reported a normal finish while something had gone wrong on
the provider's side. Both times the failure looked like the **model's behaviour**, and both times
only a control on the **same request** sent another way exposed it.

| What happened | How it looked | How it was found |
| --- | --- | --- |
| **BioEvidenceBench, Gemini Batch API (2026-11-19, reproduced 2026-11-20).** The JSON schema was not enforced in batch mode: 44 of 48 dev answers were a bare array instead of `{"mentions": [...]}`, 3 others another wrong shape. Finish reason `STOP`, job "succeeded", no error | A model that ignores the output format | The same 3 requests sent synchronously all followed the schema; in batch all 3 were bare arrays, with prompt token counts a constant 167 lower on every page. Sent through the older `response_schema` field instead, batch followed the schema 3 of 3 with token counts identical to sync: the batch path drops the newer `response_json_schema` field. [Check](../results/gemini_batch_schema_check/) · [story](stories/when_success_is_a_failure.md) |
| **LiveLab, Gemini Live Extended Thinking on the free tier (2026-09-19).** Over a six-hour run the share of items with no tool call rose 1/12 → 9/12. The server ended each turn normally (`generation_complete`, `turn_complete`); the model said *"I apologize, but a system error occurred."* The error went to the model, not to the client | A model that declines to answer, which under the first scoring would have supported the study's own conclusion | The standard `gemini-3.8-live`, same item, same key, same minute, answered in 1.3 s. A token-quota hypothesis was tested and refuted (a request cut to a sixth failed the same way); the mechanism was never found. With billing on, the missing data took 20 minutes and $0.20 ([LiveLab](https://github.com/dekunsun/livelab), `docs/probe_preregistration.md`, deviation 7) |
| **LiveLab, a cap of our own (contrast).** Claude answers were cut at a 1,024-token output cap; 128 answers lost their later fields | Missing fields | The API did report it (`stop_reason = "max_tokens"`); the runner did not save it. Silent on our side, not the provider's |

Both provider-side failures happened on a cheaper or secondary path (batch at half price, the free
tier); the standard paid synchronous path, sent the same request, worked and raised its errors.
That is two cases, not a rule.

| Lesson | What to do |
| --- | --- |
| "Success" from an API is not evidence the request was processed as sent | Save the full request, the finish reason and the usage of every call; check the finish reason |
| A platform failure can masquerade as model behaviour, and may even favour your hypothesis | Validate every answer in code (`check_shape`); count non-answers and malformed answers separately, never as the model's choice; report coverage beside every rate |
| The decisive test is a control on the identical request | When a model behaves oddly, resend the same request by another path (sync instead of batch, the standard model instead of the variant, paid instead of free) before interpreting it |
| The call path is part of the configuration | Freeze the call mode with the model; record SDK version, endpoint and tier; do not mix modes within one comparison |
| Diagnostics can disturb what they measure | In LiveLab, a second test started four minutes after the first ran inside the first one's failure window; space diagnostics out and change one thing at a time |

## F. Training a model on a verifiable reward (RL module, 2026-11-21)

| What happened | Lesson | What to do next time |
| --- | --- | --- |
| GRPO from the base model learned to return the OCR unchanged: copying never scores below 0, and the base model's edits were right 4% of the time | A reward that never penalises doing nothing makes doing nothing the safe optimum for a weak policy | Before training, score "copy the input" and "edit at random" under the reward; if copying is the best reachable policy, change the reward or the starting model first |
| Groups with no reward difference rose from about 50% to 95% while the training reward rose | A falling learning signal can mean success or collapse; the reward alone cannot tell which | Log every completion with its step and reward, and watch the copy share, entropy and a dev metric beside the reward |
| GRPO after SFT raised the training reward from 0.54 to 0.65 with no repair gain on dev or test | Training reward is not the measure of success | Fix the success metrics and decision rules before training, and judge only on held-out lines |
| 41% of the untrained model's answers ran on into the next line, because the prompt put the next line just before the answer | The input layout can be the real cause of a "model" failure | Read the answers that fail before tuning anything; put the item to act on last and mark its boundary |
| The automated probes found three reward holes; the author's manual reading found two more (finishing a line-end hyphenated word scored 1.0; dash glyphs scored inconsistently) | Constructed attacks only find what you thought of | Have a person read high-reward answers blind to the model; keep each hole as a failing test until it is fixed |
| bf16 weights would have rounded away most updates at lr 1e-6 | Precision is part of the experiment | Train with float32 master weights, or check that updates survive at the chosen learning rate |
| TRL gives vLLM the same sampling seed in every run | Two "seeds" can be nearly the same run | Check what a seed actually changes; vary data order or sampling explicitly |
| Name-word counts were first reported per answer (×4), not per word | Counts and rates need the same unit check as code | Recompute every count from the test file itself before writing it down |
