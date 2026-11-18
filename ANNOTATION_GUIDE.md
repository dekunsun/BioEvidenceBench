# Annotation guide

> 中文版在本文件下方：[跳到中文版](#标注规范中文版)。两个版本内容相同；如有出入，以英文版为准，并请指出来改正。

**Version v0.5, 2026-11-18.** Written before any labelling. Gloria settled the nine open decisions
(v0.4) and asked for four further changes (v0.5); see the changelog. This version is the one the
prompt (`p3`) and the gold set use. Later changes get a new version number and a changelog line; the gold CSV
records the guide version of every row.

## Decision record (Gloria, 2026-11-18)

| # | Question | Decision | Rule |
|---|---|---|---|
| 1 | Vernacular names (`Hedge-Sparrow`, `THE CHASTE BULIMUS`) | Own field `vernacular`; never mixed into `taxon`; scored separately | 2.2 |
| 2 | Relative words (`near Dover`) | Span is `Dover`; `near` goes in the `qualifier` column | 2.3 |
| 3 | Month-only phenology (`arrives in April`) | Not a `date` | 2.6 |
| 4 | Journal titles (`Pro. Zool. Soc.`) | Not an `institution` | 2.5 |
| 5 | Full stop at the end of a span | Kept only after a shortened word (`Linn.`, `Pfr.`) | 2.0.2 |
| 6 | Titles (`Lord`, `Herr`, `Mr.`) | Never part of a `person` span | 2.4 |
| 7 | Descriptive words before a place (`valley of the Amoor`) | Part-of-place words stay in; relative words stay out | 2.3 |
| 8 | Same name, two roles on one page | Labelled by its role at that spot | 2.4, 2.5 |
| 9 | Name broken across lines | One continuous span; non-contiguous cases go in the issues file, not in the gold set | 2.0.3 |

## 0. Ground rules

1. **Label before you look (test pages).** Do not open any model output for a test page before
   your gold labels for that page are final.
2. **Dev pages follow a different discipline.** Model outputs on the 6 dev pages have already been
   read and were used to write v0.3 and v0.4. Dev pages are for finding problems and tuning
   prompts and rules. Their gold labels are useful, but dev scores are never reported as
   independent results; only the locked test pages are.
3. **Label the expert transcription**, not the legacy OCR: `data/sample/expert_view/<PageID>.txt`
   (in the repo; readable on GitHub). Use the scan (the `bhl_url` link in
   `data/sample_split.csv`) to resolve doubts about layout or italics, but the label always
   points into the expert text.
4. **Label what is printed.** Spans are copied as printed: archaic spelling, ligatures,
   abbreviations, hyphenation. Do not correct, expand or modernise in the span.
5. **One file per labeller**: `gold/gold_mentions_<labeller>.csv`, copied from the template.
6. When a rule does not cover a case, label your best guess, write `UNCLEAR:` and the reason in
   `notes`, and carry on. Every `UNCLEAR` row is resolved before scoring (section 4).

## 1. What a label is

The unit is a **mention**: one span of characters in the expert text, plus a field type.

| Column | Meaning |
|---|---|
| `page_id` | BHL PageID |
| `start` | offset of the first character, counting from 0 |
| `end` | offset just *after* the last character (Python slice: `text[start:end]`) |
| `field` | `taxon`, `vernacular`, `person`, `locality`, `institution` or `date` |
| `text` | the span, copied exactly |
| `qualifier` | localities only: the relative words left out of the span (`near`, `ten miles north of`). Empty otherwise. Recorded, not scored in V1 |
| `notes` | free text; `UNCLEAR: …` for doubtful cases; `UNCERTAIN-IN-SOURCE` when the print itself hedges (e.g. a `?`); `NO-YEAR` (2.6) |
| `adjudication` | empty for a clear row. For a row that was `UNCLEAR`: `adjudicated` (decided; scored normally) or `ambiguous` (still open; left out of strict scoring). See section 4 |
| `guide_version` | e.g. `v0.4` |

**Finding offsets.** Each line of `data/sample/expert_view/<PageID>.txt` starts with the offset
where that line begins. Offset of a word = line offset + its column, counting from 0. You can also
leave `start` and `end` empty and fill only `text`. `python src/check_gold.py` then reports the
offsets when the text occurs once on the page and asks you to resolve it when it occurs more than
once. Either way, the checker confirms that `text == page[start:end]` for every row.

A page with no target entities still gets one row: `field` = `none`, `start`/`end` empty. This
tells "labelled, nothing found" apart from "not labelled yet".

**Annotation issues file.** Text that cannot be labelled as one clean span does not go in the gold
file. It goes in `gold/annotation_issues_<labeller>.csv` (rule 2.0.3):

| Column | Meaning |
|---|---|
| `page_id` | BHL PageID |
| `issue_type` | `non_contiguous` (a name split by unrelated text), `reading_order` (text out of order), or `other` |
| `field` | the field the entity would have had |
| `full_text` | the whole name as it should read |
| `frag1_start`, `frag1_end` | offsets of the first fragment |
| `frag2_start`, `frag2_end` | offsets of the second fragment (empty if there is none) |
| `notes` | what separates the fragments |

The scorer ignores these regions completely: a model output that overlaps a listed fragment is
neither right nor wrong, and nothing there counts as missed. The number of regions and of
outputs set aside is reported.

## 2. Fields

**Where the entity types come from.** Entity types are inspired by the NHM BHL prototype
(Hartley, Gu & Smith, BHL Day 2026: taxa, people, localities, institutions). However, annotation
boundaries, evaluation criteria, and datasets are independently defined. Our scores are not
directly comparable to NHM's reported results.

**This is a mixed design, on purpose.** `taxon`, `vernacular`, `person`, `locality` and
`institution` are **named-entity mentions**: label every mention, whatever role it plays on the
page (collector, cited author, naming authority, distribution statement...). `date` is narrower:
it is tied to an event, and only dates of occurrences are labelled (2.6). So in
`PFEIFFER, Pro. Zool. Soc., 1846, p. 112`, `PFEIFFER` is a `person`, the journal is not an
`institution`, and `1846` is not a `date` because it is a publication year.

### 2.0 Span edges (all fields)

1. A span starts at the first character of the entity and ends at its last character. Brackets,
   quotation marks, commas and semicolons around it stay out: `(Mus. Taylor.)` gives
   `Mus. Taylor`.
2. **Full stop at the end.** Keep it only when the word right before it is a shortened form,
   because then the full stop is part of the abbreviation: `LINN.`, `Linn.`, `Pfr.`, `Gmel.`.
   Drop it after a word printed in full, where it is punctuation: `(Mus. Cuming.)` gives
   `Mus. Cuming`; `Achatina albolineata, Lamarck.` gives `Lamarck`; `Hab. Brazil.` gives
   `Brazil`. Full stops *inside* the span always stay (`Mus. Cuming`, `J. Smith`,
   `A. arvensis`). If you cannot tell whether a word is shortened, drop the full stop and write
   `UNCLEAR: abbreviation?` in notes.
3. **Line breaks.** A name broken across lines by ordinary hyphenation or wrapping is one span,
   from its first to its last character, with the hyphen and line break inside it: `A. blak-` +
   `istoni` is one `taxon`; `Ja‐` + `maica` is one `locality`. Never label only the first
   fragment.
   **Exception: non-contiguous text.** If anything other than a hyphen, spaces and one line break
   sits between the two fragments (text from another column, a caption, a footnote, a page
   number, a running head), do **not** stretch one span over it, and do **not** label a fragment
   as if it were the entity: a fragment is not a real mention. Make no gold row. Record the case
   in the annotation issues file (section 1) with both fragment positions and the full name.
   A wrong or partial character range must never enter the gold set.
4. **Headings and page furniture (same rule for every field, `taxon` and `vernacular` alike).**
   Label text that carries scientific content; do not label text that is only there for
   navigating the page.
   - **Label**: the heading that opens a species or genus account (`BULIMUS CASTUS.` at the start
     of its description; `THE SKY-LARK.` above the account of that bird); names in a real plate
     legend or figure caption that says what is shown (`Fig. 3. Bulimus castus`).
   - **Do not label**: running heads repeated at the top of pages (`BULIMUS.` on every page of the
     monograph; `THE JACKDAW` beside a page number); a bare plate label (`PLATE XLV.`); page
     numbers, signatures, catchwords and other decoration.
   - Test: would the page lose information about *which organism is treated here* if this text
     were removed? An account heading or a caption: yes. A running head that repeats the genus
     or the chapter: no.
   - If you cannot tell which it is, label it and write `UNCLEAR: running head?` in notes.

### 2.1 `taxon`: scientific names

Label:
- Binomials and trinomials: `Accentor modularis`, `Bulimus castus`.
- Uninomials used as names of a taxon at any rank: `Bulimus`, `Turdidae`, `Coleoptera`.
- Abbreviated genus *with* an epithet: `A. modularis`, `Bul. castus`.
- Names in any case or style: `BULIMUS CASTUS` (small capitals) counts.

Do not label:
- The authority after a name as part of the taxon: in `Accentor modularis (Linn.)` the taxon
  span is `Accentor modularis`; `Linn.` is a separate `person` mention (2.4).
- A bare abbreviated genus that only opens a Latin diagnosis: `Bul. testâ subfusiformi…`.
- Running heads and other page furniture (rule 2.0.4). A heading that opens a species account
  *is* labelled.
- Vernacular names: they are `vernacular` (2.2), never `taxon`.

### 2.2 `vernacular`: common names of organisms

A common-language name that identifies a particular kind of organism (a species or a named
group). Kept apart from `taxon` because the two are recognised differently, and Butler names most
birds in English. `vernacular` has its own scores and is never part of the taxon F1 or the
primary all-fields F1.

| Printed | Label |
|---|---|
| `Hedge-Sparrow` | `vernacular` |
| `Accentor modularis` | `taxon` |
| `THE CHASTE BULIMUS` | `vernacular`, span `CHASTE BULIMUS` |
| `Bulimus castus` | `taxon` |

Label:
- Names of a kind, at any rank, used as a name: `Sky-Lark`, `Hedge-Sparrow`, `the Buntings`
  (span `Buntings`), `Lesser Redpoll`.
- Every mention, as for other entity fields.
- The name without a leading article: `THE CHASTE BULIMUS` gives `CHASTE BULIMUS`.

Do not label:
- Generic words that name no particular kind: `bird`, `shell`, `species`, `the male`, `the young`.
- Running heads and other page furniture (rule 2.0.4, the same rule as for `taxon`). A heading
  that opens a species account *is* labelled.
- Adjective uses inside another name (`Sparrow-Hawk` is one name, not `Sparrow` plus `Hawk`).

### 2.3 `locality`: a named geographic place

Label:
- Any named real place in the text, in whatever role: habitat, distribution, collection or
  observation statements, and other mentions such as `Key to the species of the Argentine Republic`.
  `Hab. Central America?` gives span `Central America`, with notes `UNCERTAIN-IN-SOURCE`.
- A place with its narrowing parts as one span: `Isle of Luzon, Philippine Islands`.
- Distribution statements in prose: in `it breeds in Scotland` the span is `Scotland`.
- Several different places as separate mentions: `Cornwall and Devon` gives two.

**Part of the place, or relative to it?** Words that name a piece of the place itself stay in the
span. Words that place something relative to the place stay out and go in `qualifier`.

| Printed | Span | `qualifier` | Why |
|---|---|---|---|
| `valley of the Amoor` | `valley of the Amoor` | | a part of the place |
| `north coast of Norfolk` | `north coast of Norfolk` | | a part |
| `South-east Mongolia` | `South-east Mongolia` | | a part |
| `mouth of the Thames` | `mouth of the Thames` | | a part |
| `interior of Brazil` | `interior of Brazil` | | a part |
| `banks of the Amazon` | `banks of the Amazon` | | a part |
| `near Dover` | `Dover` | `near` | relative |
| `ten miles north of York` | `York` | `ten miles north of` | relative |
| `in the neighbourhood of London` | `London` | `in the neighbourhood of` | relative |
| `off the coast of Peru` | `coast of Peru` | `off` | `coast of` is a part, `off` is relative |
| `between Dover and Calais` | `Dover`, `Calais` (two rows) | `between` on each | relative |
| `throughout Europe` | `Europe` | | plain preposition, nothing to record |

Plain prepositions (`in`, `at`, `from`, `throughout`) are left out of the span and are not
recorded. If the table does not settle a case, use the shorter span and write `UNCLEAR: boundary`.

Do not label:
- Habitat types with no place name: `woods`, `marshes`, `on rocks`.
- Places inside bibliographic citations (place of publication).
- Places that are part of an institution's name: `Zoological Society of London` is one
  `institution`, not a locality.
- Adjectives like `British` in `British birds`, and places in titles or running heads.

### 2.4 `person`: a named person

Label:
- Any named person: collectors and observers (`shot by Mr. J. Smith` gives `J. Smith`), cited
  authors (`PFEIFFER, Pro. Zool. Soc.` gives `PFEIFFER`; `Giusti's (1997)` gives `Giusti`), and
  naming authorities, abbreviated or not (`Linn.`, `Pfr.`, `Lamarck`).
- Initials belong to the name (`J. Smith`). Titles, ranks and forms of address never do: `Mr.`,
  `Dr.`, `Capt.`, `Lord`, `Sir`, `Herr`, `Rev.`, `Prof.`, `Lieut.`, `Col.`. `Lord Lilford` gives
  `Lilford` and `Herr Gätke` gives `Gätke`, with the title in notes.
- Label a name by the role it plays at that spot, even when the same name has another role
  elsewhere on the page. On one Reeve page, `ADAMS, MS.` (a species described from Adams's
  manuscript) gives person `ADAMS` (`MS.` is not labelled), while `(Mus. Adams.)` gives
  institution `Mus. Adams` and no person.
- **[OPTIONAL]** The role in notes: `collector`, `author`, `authority`, `other`. It helps later
  analysis but is not scored in V1.

Do not label:
- A person's name inside a taxon name (`Cumingii` in `Bulimus Cumingii`) or inside an institution
  name (`Cuming` in `Mus. Cuming`).

### 2.5 `institution`: a named museum, collection or organisation

Label:
- Museums, herbaria, private collections, societies, universities, expeditions:
  `Mus. Cuming`, `Mus. Dennison`, `British Museum`, `Zoological Society of London`.
- The whole name as printed, including abbreviations such as `Mus.`. The full stop after the
  collector's name follows rule 2.0.2: `(Mus. Cuming.)` gives `Mus. Cuming`.
- A private collection named after a person who also appears as a person on the page: see the
  `Mus. Adams` / `ADAMS, MS.` example in 2.4.

Do not label:
- Journal titles in citations (`Pro. Zool. Soc.`, `Ann. Mag. Nat. Hist.`): a publication and an
  organisation are different kinds of entity.
- Generic words without a name (`the museum`, `a collection`).

### 2.6 `date`: when an occurrence happened

A `date` belongs to a particular event: a specimen collected, shot, captured or seen, a nest
found, an arrival recorded.

| Printed | Label? | Why |
|---|---|---|
| `shot on 3rd May, 1890` | `3rd May, 1890` | a particular event |
| `obtained in 1850` | `1850` | a particular event |
| `one was collected in April` | `April`, notes `NO-YEAR` | a particular event, year not given |
| `arrives in April` | no | general phenology, not one event |
| `breeds in spring` | no | general phenology |
| `PFEIFFER, Pro. Zool. Soc., 1846, p. 112` | no date (`PFEIFFER` is a `person`) | publication year |
| `published in April 1890` | no | publication date |

Label:
- The whole date expression as printed, with ordinal suffixes and commas inside it; ranges such
  as `1880–85` are one span.

Do not label:
- Publication dates and years in citations, general phenology, ages, durations, page numbers.

No separate phenology label in V1: it would add labelling work without serving a research
question. Dates are expected to be rare in Reeve. That is a finding, not a problem.

## 3. Taxon linking (E4-lite, Butler only)

A separate pass, done **after** the mention labels for the page are final, in a separate file
`gold/gold_links_<labeller>.csv`. One row per `taxon` mention (not `vernacular`).

Finding a name in a database and identifying the right taxonomic entity are two different
judgements, so they are recorded in separate columns. A historical name can be found by fuzzy
matching *and* be a synonym of an accepted name; one combined label could not say both.

| Column | Values | Meaning |
|---|---|---|
| `page_id`, `start`, `end`, `text` | | copied from the mention row |
| `printed_rank` | `species` / `subspecies` / `genus` / `family` / … | Rank of the name as printed. `Alauda arvensis` is `species`; `Alauda` is `genus` |
| `resolution_status` | `resolved` / `partial` / `ambiguous` / `unresolved` | `resolved`: you settled the taxon **at the printed rank**. `partial`: only a higher rank could be matched (a binomial matched to its genus). `ambiguous`: several candidates remain (list them in notes). `unresolved`: no usable record |
| `match_method` | `exact` / `fuzzy` / `manual` | How the record was found: the printed string as is; a spelling variant; or your own research beyond string search |
| `matched_rank` | `species` / `subspecies` / `genus` / `family` / … | Rank of the matched record. A binomial matched only at genus level is `genus`, and its status is `partial`, never `resolved` |
| `taxonomic_status` | `accepted` / `synonym` / `uncertain` | Status of the matched name in the source today |
| `matched_usage_key` | GBIF key | The name record actually matched |
| `accepted_usage_key` | GBIF key | The accepted taxon it belongs to (same as matched when `accepted`) |
| `evidence_source` | `GBIF` / `Avibase` / `IOC` / other | Where the decision rests |
| `notes` | | why it is ambiguous or unresolved; candidates |

Leave the key columns empty when `resolution_status` is `unresolved`. Reeve's names are not
linked in V1: historical molluscan names need a specialist.

**How linking is counted.** A link is correct only when it is `resolved`, that is, at the printed
rank. For names printed as species, results are reported as four separate counts: species-level
correct, `partial` (genus or higher only), `ambiguous`, `unresolved`. A genus-only match for a
species name is never added to the species-level success rate.

## 4. Adjudication, agreement and freezing

**Unclear rows are not ground truth until resolved.** Before any scoring, every row with
`UNCLEAR` in notes gets an `adjudication` value:
- `adjudicated`: a decision was made (if the rule was missing, it is added to the guide as a new
  version). Scored like any other row.
- `ambiguous`: reasonable labellers could differ. Left out of strict scoring: a prediction that
  matches it earns no credit and costs nothing, and missing it is not an error. The number of
  such rows is reported. (Non-contiguous text is not an `ambiguous` row; it goes in the
  annotation issues file.)

**Agreement check.** A second labeller labels 5 test pages independently with this guide, without
seeing Gloria's labels. We report span-level agreement per field (exact and overlap) and discuss
every disagreement. A disagreement is settled by adjudication: the gold row is corrected, or
marked `ambiguous`, or the guide gets a clearer rule.

**The gold set is finished before anything is unsealed.** The order is fixed: (1) Gloria labels;
(2) the second labeller labels 5 test pages; (3) every disagreement and every `UNCLEAR` row is
adjudicated; (4) the gold files are frozen (their SHA-256 goes into `PREREGISTRATION.md`);
(5) only then is any test output unsealed. Frozen with the gold set: `guide_version`,
`prompt_version`, the output schema, the scorer (code commit), and each model's configuration.

**Corrections after unsealing.** If a real labelling mistake is found later, it is corrected by an
independent review: the reviewer decides from the page and the guide, without looking at any model
answer for that mention. The original label is kept. Each correction is one row in
`gold/gold_changes.csv` (date, page, old row, new row, reason, reviewer, whether model output had
been seen), the gold file gets a new version, and scores are reported for both the frozen and the
corrected gold. Scoring rules are never changed to improve a score.

## Changelog

| Version | Date | Change |
|---|---|---|
| v0.1 | 2026-11-18 | First draft. No pages labelled yet. |
| v0.2 | 2026-11-18 | Entity types aligned with the NHM BHL prototype: `collector` replaced by `person` (every named person); new `institution`; `locality` covers every named place, not only occurrence statements. `date` unchanged. |
| v0.3 | 2026-11-18 | Default answers for the span-edge questions found in the Opus p2 dev run: 2.0 on span edges; all titles treated like honorifics; part-of-place words stay in the locality span; `Mus. Adams` / `ADAMS, MS.` worked example. |
| v0.4 | 2026-11-18 | Gloria's decisions on all nine questions. New field `vernacular`, scored separately (decision 1). New `qualifier` column for relative words (2). More in/out examples for place boundaries (7). Non-contiguous exception for names broken across lines (9). Fixed the `PFEIFFER … 1846` example and stated the mixed design: entity fields are general NER, `date` is event-bound; a month without a year counts when it belongs to a particular event. NHM statement reworded: types inspired by NHM, scores not comparable. Taxon linking split into resolution status, match method, matched rank and taxonomic status. New `adjudication` column and rules for unclear rows; dev and test discipline separated; freeze list before unsealing. No pages labelled yet. |
| v0.5 | 2026-11-18 | Four changes asked for by Gloria. One heading rule for all fields (2.0.4): account headings and real captions are labelled, running heads and bare plate labels are not; `taxon` and `vernacular` now agree. Non-contiguous text makes no gold row; it is recorded in the annotation issues file and the scorer ignores those regions. Linking: new `printed_rank` and status `partial`; a genus-only match for a species name is never counted as species-level correct. Gold set (double labelling, adjudication, freeze) is finished before unsealing; later corrections go through independent review and `gold/gold_changes.csv`. No pages labelled yet. |

---

# 标注规范（中文版）

**版本 v0.5，2026-11-18。** 写于任何标注开始之前。Gloria 已经对九个待定问题做了决定（v0.4），之后又提出四处修改（v0.5），见变更记录。提示词（`p3`）和 gold set 都以这一版为准。之后再改要换版本号，并在变更记录里加一行；gold CSV 的每一行都记录所用的规范版本。

## 决定记录（Gloria，2026-11-18）

| # | 问题 | 决定 | 规则 |
|---|---|---|---|
| 1 | 俗名（`Hedge-Sparrow`、`THE CHASTE BULIMUS`） | 单独的字段 `vernacular`；不混进 `taxon`；单独评分 | 2.2 |
| 2 | 相对位置词（`near Dover`） | 片段是 `Dover`；`near` 填进 `qualifier` 列 | 2.3 |
| 3 | 只有月份的物候（`arrives in April`） | 不算 `date` | 2.6 |
| 4 | 期刊名（`Pro. Zool. Soc.`） | 不算 `institution` | 2.5 |
| 5 | 片段末尾的句点 | 只在缩写词后面保留（`Linn.`、`Pfr.`） | 2.0.2 |
| 6 | 头衔（`Lord`、`Herr`、`Mr.`） | 一律不算进 `person` 片段 | 2.4 |
| 7 | 地名前的描述词（`valley of the Amoor`） | 表示地点一部分的词留下；表示相对位置的词不算 | 2.3 |
| 8 | 同一页上同一个名字有两种角色 | 按它在那个位置的角色标 | 2.4、2.5 |
| 9 | 跨行断开的名字 | 标成一个连续片段；不连续的情况记到问题表里，不进 gold set | 2.0.3 |

## 0. 基本原则

1. **先标注，后看输出（测试页）。** 一页测试页的 gold 标签定稿之前，不要打开这一页的任何模型输出。
2. **开发页用另一套纪律。** 6 页开发页的模型输出已经被看过，并且用来写了 v0.3 和 v0.4。开发页的用途是发现问题、调提示词和规则。它们的 gold 标签仍然有用，但开发页的分数不作为独立结果报告；只有锁定的测试页才是。
3. **在专家转录上标注**，不是在旧 OCR 上：`data/sample/expert_view/<PageID>.txt`（在仓库里，GitHub 上就能看）。版式或斜体有疑问时可以看扫描图（`data/sample_split.csv` 里的 `bhl_url` 链接），但标签始终指向专家转录的文字。
4. **按印刷原样标。** 片段照原样抄：古旧拼法、连字、缩写、断词都保留。不要在片段里改正、展开或现代化。
5. **每个标注人一个文件**：`gold/gold_mentions_<标注人>.csv`，从模板复制。
6. 规则没覆盖到的情况，按你的最佳判断标，在 `notes` 里写 `UNCLEAR:` 和原因，然后继续。所有 `UNCLEAR` 的行都要在评分前处理（第 4 节）。

## 1. 一个标签是什么

标注单位是一个**提及**（mention）：专家转录里的一段字符，加上字段类型。

| 列 | 含义 |
|---|---|
| `page_id` | BHL PageID |
| `start` | 第一个字符的位置，从 0 开始数 |
| `end` | 最后一个字符*之后*的位置（Python 切片：`text[start:end]`） |
| `field` | `taxon`、`vernacular`、`person`、`locality`、`institution` 或 `date` |
| `text` | 片段，原样抄写 |
| `qualifier` | 只用于地点：没有算进片段的相对位置词（`near`、`ten miles north of`）。其他情况留空。只记录，V1 不评分 |
| `notes` | 自由文本；拿不准的写 `UNCLEAR: …`；原文本身有保留（比如带 `?`）时写 `UNCERTAIN-IN-SOURCE`；另有 `NO-YEAR`（2.6） |
| `adjudication` | 清楚的行留空。曾经标过 `UNCLEAR` 的行填：`adjudicated`（已裁定，正常评分）或 `ambiguous`（仍有歧义，不纳入严格评分）。见第 4 节 |
| `guide_version` | 例如 `v0.4` |

**怎么找位置。** `data/sample/expert_view/<PageID>.txt` 每一行开头都是这一行起始字符的位置。一个词的位置 = 行起始位置 + 它在这一行里的列号（从 0 开始数）。你也可以把 `start` 和 `end` 留空，只填 `text`：运行 `python src/check_gold.py`，文字在页面上只出现一次时它会给出位置，出现多次时会列出所有位置让你选。不管哪种方式，检查脚本都会确认每一行都满足 `text == page[start:end]`。

没有目标实体的页面也要写一行：`field` 填 `none`，`start`/`end` 留空。这样能区分"标过了，什么都没有"和"还没标"。

**标注问题表。** 没法标成一个干净片段的文字不进 gold 文件，而是记到 `gold/annotation_issues_<标注人>.csv`（规则 2.0.3）：

| 列 | 含义 |
|---|---|
| `page_id` | BHL PageID |
| `issue_type` | `non_contiguous`（名字被无关文字隔开）、`reading_order`（文字顺序错乱）或 `other` |
| `field` | 这个实体本来应该属于的字段 |
| `full_text` | 完整的名字应该怎么读 |
| `frag1_start`、`frag1_end` | 第一段的位置 |
| `frag2_start`、`frag2_end` | 第二段的位置（没有就留空） |
| `notes` | 两段之间隔着什么 |

评分代码会完全忽略这些区域：模型输出和表里的某一段重叠时，既不算对也不算错，这里也不算漏。这类区域的数量和被搁置的模型输出数量会单独报告。

## 2. 字段

**实体类型的来源。** 实体类型参考了 NHM 的 BHL 原型（Hartley、Gu、Smith，BHL Day 2026：学名、人、地点、机构）。但标注边界、评估标准和数据集都是我们独立定义的。我们的分数不能和 NHM 报告的结果直接比较。

**这是有意的混合设计。** `taxon`、`vernacular`、`person`、`locality`、`institution` 是**命名实体提及**：不管它在页面上起什么作用（采集人、被引用的作者、命名人、分布描述……），每一次出现都要标。`date` 范围更窄：它和事件绑定，只标发生事件的日期（2.6）。所以在 `PFEIFFER, Pro. Zool. Soc., 1846, p. 112` 里，`PFEIFFER` 是 `person`，期刊不是 `institution`，`1846` 是出版年份，不是 `date`。

### 2.0 片段边界（所有字段）

1. 片段从实体的第一个字符开始，到它的最后一个字符结束。外面的括号、引号、逗号、分号都不算：`(Mus. Taylor.)` 标成 `Mus. Taylor`。
2. **末尾的句点。** 只有句点前的词是缩写形式时才保留，因为这时句点是缩写的一部分：`LINN.`、`Linn.`、`Pfr.`、`Gmel.`。前面是完整拼写的词时去掉，因为这时句点只是标点：`(Mus. Cuming.)` 标成 `Mus. Cuming`；`Achatina albolineata, Lamarck.` 标成 `Lamarck`；`Hab. Brazil.` 标成 `Brazil`。片段*内部*的句点一律保留（`Mus. Cuming`、`J. Smith`、`A. arvensis`）。分不清一个词是不是缩写时，去掉句点，并在备注里写 `UNCLEAR: abbreviation?`。
3. **换行。** 因为普通断词或换行而跨行的名字是一个片段，从第一个字符到最后一个字符，中间的连字符和换行包括在内：`A. blak-` + `istoni` 是一个 `taxon`；`Ja‐` + `maica` 是一个 `locality`。不要只标第一段。
   **例外：文字不连续。** 如果两段之间除了连字符、空格和一个换行之外还夹着别的东西（另一栏的文字、图注、脚注、页码、页眉），**不要**用一个片段把它们硬连起来，也**不要**把其中一段当成实体来标：一个片段不是真正的提及。gold 里不写这一行，而是把它记到标注问题表（第 1 节），写上两段的位置和完整的名字。错误的或不完整的字符范围绝不能进入 gold set。
4. **标题和版面元素（所有字段同一条规则，`taxon` 和 `vernacular` 一样）。** 承载科学内容的文字要标；只用来在页面上导航的文字不标。
   - **要标**：物种或属的条目开头的标题（描述开头的 `BULIMUS CASTUS.`；某种鸟的条目上方的 `THE SKY-LARK.`）；真正的图版说明或图注里说明图中内容的名字（`Fig. 3. Bulimus castus`）。
   - **不标**：每页顶部重复出现的页眉（专著每页顶上的 `BULIMUS.`；页码旁边的 `THE JACKDAW`）；光秃秃的图版编号（`PLATE XLV.`）；页码、印张记号、接页词等装饰性内容。
   - 判断方法：去掉这段文字，页面会不会丢掉"这里讲的是哪种生物"的信息？条目标题和图注：会。只是重复属名或章节名的页眉：不会。
   - 分不清是哪一种时，先标上，并在备注里写 `UNCLEAR: running head?`。

### 2.1 `taxon`：学名

要标：
- 二名和三名：`Accentor modularis`、`Bulimus castus`。
- 用作任一等级分类单元名称的单名：`Bulimus`、`Turdidae`、`Coleoptera`。
- 缩写属名*加*种加词：`A. modularis`、`Bul. castus`。
- 任何大小写或字体都算：`BULIMUS CASTUS`（小型大写）也算。

不标：
- 名字后面的命名人不算在学名里：`Accentor modularis (Linn.)` 中，学名片段是 `Accentor modularis`；`Linn.` 另外标成一个 `person`（2.4）。
- 只是用来开头一段拉丁文描述的单独缩写属名：`Bul. testâ subfusiformi…`。
- 页眉等版面元素（规则 2.0.4）。物种条目开头的标题*要*标。
- 俗名：它们是 `vernacular`（2.2），不是 `taxon`。

### 2.2 `vernacular`：生物的俗名

指用日常语言称呼某一类特定生物（一个物种或一个有名字的类群）的名称。它和 `taxon` 分开，是因为两者的识别方式不同，而且 Butler 大多用英文名称呼鸟。`vernacular` 有自己单独的分数，不计入学名 F1，也不计入全字段的主要 F1。

| 原文 | 标签 |
|---|---|
| `Hedge-Sparrow` | `vernacular` |
| `Accentor modularis` | `taxon` |
| `THE CHASTE BULIMUS` | `vernacular`，片段是 `CHASTE BULIMUS` |
| `Bulimus castus` | `taxon` |

要标：
- 任一等级上、用作名称的类群名：`Sky-Lark`、`Hedge-Sparrow`、`the Buntings`（片段是 `Buntings`）、`Lesser Redpoll`。
- 每一次出现都标，和其他实体字段一样。
- 不带开头的冠词：`THE CHASTE BULIMUS` 标成 `CHASTE BULIMUS`。

不标：
- 不指特定类群的泛称：`bird`、`shell`、`species`、`the male`、`the young`。
- 页眉等版面元素（规则 2.0.4，和 `taxon` 是同一条规则）。物种条目开头的标题*要*标。
- 另一个名字内部的修饰成分（`Sparrow-Hawk` 是一个名字，不是 `Sparrow` 加 `Hawk`）。

### 2.3 `locality`：有名字的地理位置

要标：
- 文中任何有名字的真实地点，不管起什么作用：栖息地、分布、采集或观察记录，以及其他提到地点的地方，比如 `Key to the species of the Argentine Republic`。`Hab. Central America?` 标成 `Central America`，备注写 `UNCERTAIN-IN-SOURCE`。
- 地点连同缩小范围的部分算一个片段：`Isle of Luzon, Philippine Islands`。
- 正文中的分布描述：`it breeds in Scotland` 中，片段是 `Scotland`。
- 几个不同的地点分别标：`Cornwall and Devon` 是两个。

**是地点的一部分，还是相对于地点的位置？** 表示地点本身某一部分的词留在片段里。表示相对于这个地点的位置的词不算进片段，填进 `qualifier` 列。

| 原文 | 片段 | `qualifier` | 原因 |
|---|---|---|---|
| `valley of the Amoor` | `valley of the Amoor` | | 地点的一部分 |
| `north coast of Norfolk` | `north coast of Norfolk` | | 一部分 |
| `South-east Mongolia` | `South-east Mongolia` | | 一部分 |
| `mouth of the Thames` | `mouth of the Thames` | | 一部分 |
| `interior of Brazil` | `interior of Brazil` | | 一部分 |
| `banks of the Amazon` | `banks of the Amazon` | | 一部分 |
| `near Dover` | `Dover` | `near` | 相对位置 |
| `ten miles north of York` | `York` | `ten miles north of` | 相对位置 |
| `in the neighbourhood of London` | `London` | `in the neighbourhood of` | 相对位置 |
| `off the coast of Peru` | `coast of Peru` | `off` | `coast of` 是一部分，`off` 是相对位置 |
| `between Dover and Calais` | `Dover`、`Calais`（两行） | 每行都填 `between` | 相对位置 |
| `throughout Europe` | `Europe` | | 普通介词，不用记 |

普通介词（`in`、`at`、`from`、`throughout`）不算进片段，也不用记录。表里的例子判断不了时，用较短的片段，并写 `UNCLEAR: boundary`。

不标：
- 没有地名的生境类型：`woods`、`marshes`、`on rocks`。
- 文献引用里的地点（出版地）。
- 属于机构名称一部分的地点：`Zoological Society of London` 是一个 `institution`，不是地点。
- 形容词，比如 `British birds` 里的 `British`；标题或页眉里的地点。

### 2.4 `person`：有名字的人

要标：
- 任何有名字的人：采集人和观察者（`shot by Mr. J. Smith` 标成 `J. Smith`），被引用的作者（`PFEIFFER, Pro. Zool. Soc.` 标成 `PFEIFFER`；`Giusti's (1997)` 标成 `Giusti`），以及命名人，缩写与否都算（`Linn.`、`Pfr.`、`Lamarck`）。
- 首字母缩写属于名字（`J. Smith`）。头衔、军衔和称呼一律不属于：`Mr.`、`Dr.`、`Capt.`、`Lord`、`Sir`、`Herr`、`Rev.`、`Prof.`、`Lieut.`、`Col.`。`Lord Lilford` 标成 `Lilford`，`Herr Gätke` 标成 `Gätke`，头衔写进备注。
- 按名字在那个位置的角色来标，即使同一个名字在同一页别处有另一种角色。Reeve 的某一页上，`ADAMS, MS.`（根据 Adams 的手稿描述的物种）标成人 `ADAMS`（`MS.` 不标），而 `(Mus. Adams.)` 标成机构 `Mus. Adams`，不另标人。
- **[可选]** 在备注里写角色：`collector`、`author`、`authority`、`other`。对之后的分析有帮助，V1 不评分。

不标：
- 学名里的人名（`Bulimus Cumingii` 里的 `Cumingii`），或机构名里的人名（`Mus. Cuming` 里的 `Cuming`）。

### 2.5 `institution`：有名字的博物馆、收藏或组织

要标：
- 博物馆、植物标本馆、私人收藏、学会、大学、考察队：`Mus. Cuming`、`Mus. Dennison`、`British Museum`、`Zoological Society of London`。
- 按印刷的完整名称标，包括 `Mus.` 这样的缩写。收藏者名字后面的句点按规则 2.0.2 处理：`(Mus. Cuming.)` 标成 `Mus. Cuming`。
- 以某个人命名、而这个人在同一页上也作为人出现的私人收藏：见 2.4 里 `Mus. Adams` / `ADAMS, MS.` 的例子。

不标：
- 文献引用里的期刊名（`Pro. Zool. Soc.`、`Ann. Mag. Nat. Hist.`）：出版物和机构是不同类型的实体。
- 没有名字的泛称（`the museum`、`a collection`）。

### 2.6 `date`：发生的日期

`date` 属于某一次具体的事件：采到、打到、捕到或看到一个标本，发现一个巢，记录到一次抵达。

| 原文 | 标不标 | 原因 |
|---|---|---|
| `shot on 3rd May, 1890` | 标 `3rd May, 1890` | 一次具体事件 |
| `obtained in 1850` | 标 `1850` | 一次具体事件 |
| `one was collected in April` | 标 `April`，备注 `NO-YEAR` | 一次具体事件，没写年份 |
| `arrives in April` | 不标 | 一般物候规律，不是一次事件 |
| `breeds in spring` | 不标 | 一般物候规律 |
| `PFEIFFER, Pro. Zool. Soc., 1846, p. 112` | 不标日期（`PFEIFFER` 标成 `person`） | 出版年份 |
| `published in April 1890` | 不标 | 出版日期 |

要标：
- 按印刷的完整日期表达式标，包括序数后缀和中间的逗号；`1880–85` 这样的范围算一个片段。

不标：
- 出版日期和引用里的年份、一般物候、年龄、时长、页码。

V1 不另设物候标签：它会增加标注工作量，却不对应任何一个研究问题。Reeve 里日期预计会很少。这是一个发现，不是问题。

## 3. 学名关联（E4-lite，只做 Butler）

单独的一轮，在一页的提及标签定稿**之后**做，用单独的文件 `gold/gold_links_<标注人>.csv`。每个 `taxon` 提及一行（`vernacular` 不做）。

"在数据库里找到一个名字"和"认对了分类学实体"是两个不同的判断，所以分开记在不同的列里。一个历史学名可能是靠模糊匹配找到的，*同时*又是某个有效名的异名；合成一个标签就没法同时表达这两点。

| 列 | 取值 | 含义 |
|---|---|---|
| `page_id`、`start`、`end`、`text` | | 从提及那一行复制 |
| `printed_rank` | `species` / `subspecies` / `genus` / `family` / … | 原文印的名字是什么等级。`Alauda arvensis` 是 `species`；`Alauda` 是 `genus` |
| `resolution_status` | `resolved` / `partial` / `ambiguous` / `unresolved` | `resolved`：你**在原文印的等级上**确定了分类单元。`partial`：只匹配到更高的等级（一个二名只匹配到它的属）。`ambiguous`：还剩几个候选（在备注里列出来）。`unresolved`：没有可用的记录 |
| `match_method` | `exact` / `fuzzy` / `manual` | 记录是怎么找到的：按印刷的字符串原样找到；按拼写变体找到；或者靠字符串搜索以外的人工查证 |
| `matched_rank` | `species` / `subspecies` / `genus` / `family` / … | 匹配到的记录的等级。一个二名只匹配到属，就填 `genus`，状态是 `partial`，不能填 `resolved` |
| `taxonomic_status` | `accepted` / `synonym` / `uncertain` | 匹配到的名字今天在该来源里的状态 |
| `matched_usage_key` | GBIF key | 实际匹配到的名称记录 |
| `accepted_usage_key` | GBIF key | 它所属的有效分类单元（状态是 `accepted` 时和上一列相同） |
| `evidence_source` | `GBIF` / `Avibase` / `IOC` / 其他 | 判断依据的来源 |
| `notes` | | 为什么有歧义或没解决；候选名单 |

`resolution_status` 是 `unresolved` 时，两个 key 列留空。V1 不关联 Reeve 的名字：历史上的软体动物名称需要专家判断。

**关联结果怎么统计。** 只有 `resolved`（也就是在原文印的等级上确定）才算关联正确。对原文印成物种的名字，结果分四个数分别报告：物种级正确、`partial`（只到属或更高）、`ambiguous`、`unresolved`。物种名只匹配到属，绝不计入物种级的成功率。

## 4. 裁定、一致性检查和冻结

**不清楚的行在处理之前不算标准答案。** 评分之前，备注里写了 `UNCLEAR` 的每一行都要填 `adjudication`：
- `adjudicated`：已经做了决定（如果是缺规则，就把规则补进规范，出一个新版本）。和其他行一样评分。
- `ambiguous`：合理的标注人可能有不同标法。不纳入严格评分：模型的预测和它匹配上，不加分也不扣分；漏掉它也不算错。这类行的数量会单独报告。（文字不连续的情况不是 `ambiguous` 行，它记在标注问题表里。）

**一致性检查。** 第二位标注人按这份规范独立标注 5 页测试页，不看 Gloria 的标签。我们按字段报告片段级的一致性（完全一致和重叠两种口径），并逐条讨论每一处分歧。分歧通过裁定解决：改正 gold 的那一行，或者标成 `ambiguous`，或者给规范补一条更清楚的规则。

**gold set 要在解封之前全部完成。** 顺序是固定的：（1）Gloria 标注；（2）第二位标注人标 5 页测试页；（3）所有分歧和所有 `UNCLEAR` 行都裁定完；（4）冻结 gold 文件（把它们的 SHA-256 写进 `PREREGISTRATION.md`）；（5）这之后才解封测试输出。和 gold set 一起冻结的还有：`guide_version`、`prompt_version`、输出格式（schema）、评分代码（提交号），以及每个模型的配置。

**解封之后的更正。** 如果之后确实发现了标注错误，要通过独立审核来更正：审核人只根据页面和规范来判断，不看模型对这个提及给出的答案。原来的标签保留。每一处更正在 `gold/gold_changes.csv` 里记一行（日期、页面、原来的行、新的行、原因、审核人、是否已经看过模型输出），gold 文件出一个新版本，并且同时报告冻结版和更正版两套分数。绝不为了提高分数而修改评分规则。

## 变更记录

| 版本 | 日期 | 修改 |
|---|---|---|
| v0.1 | 2026-11-18 | 初稿。尚未标注任何页面。 |
| v0.2 | 2026-11-18 | 实体类型对齐 NHM 的 BHL 原型：`collector` 改为 `person`（所有有名字的人）；新增 `institution`；`locality` 覆盖所有有名字的地点，不只是发生记录。`date` 不变。 |
| v0.3 | 2026-11-18 | 为 Opus p2 开发集结果里发现的片段边界问题写默认答案：2.0 片段边界；所有头衔按敬称处理；表示地点一部分的词留在地点片段里；增加 `Mus. Adams` / `ADAMS, MS.` 示例。 |
| v0.4 | 2026-11-18 | Gloria 对九个问题的决定。新增字段 `vernacular`，单独评分（决定 1）。新增 `qualifier` 列记录相对位置词（2）。地点边界增加更多正反例（7）。跨行名字增加"文字不连续"的例外（9）。修正 `PFEIFFER … 1846` 的例子，并写明混合设计：实体字段是一般的命名实体识别，`date` 和事件绑定；属于一次具体事件、没有年份的月份也算。NHM 的说法改为：类型参考 NHM，分数不可比。学名关联拆成解析状态、匹配方式、匹配等级和分类学状态。新增 `adjudication` 列和不清楚行的处理规则；开发页和测试页的纪律分开；解封前的冻结清单。尚未标注任何页面。 |
| v0.5 | 2026-11-18 | Gloria 提出的四处修改。所有字段用同一条标题规则（2.0.4）：条目标题和真正的图注要标，页眉和光秃秃的图版编号不标；`taxon` 和 `vernacular` 现在一致。文字不连续的情况不写 gold 行，记到标注问题表里，评分时忽略这些区域。学名关联新增 `printed_rank` 和状态 `partial`；物种名只匹配到属，绝不算物种级正确。gold set（双人标注、裁定、冻结）要在解封之前完成；之后的更正要经过独立审核并记入 `gold/gold_changes.csv`。尚未标注任何页面。 |
