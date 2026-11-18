# Annotation guide

> 中文版在本文件下方：[跳到中文版](#标注规范中文版)。两个版本内容相同；如有出入，以英文版为准，并请指出来改正。

**Version v0.3, draft, 2026-11-18.** Written before any labelling. v0.2 aligned the entity types with the
NHM BHL prototype (see section 2); v0.3 writes default answers for the span-boundary questions found in
the Opus p2 dev run (decisions 5-9 below).
Defaults marked **[DEFAULT]** were chosen to get started; Gloria confirms or changes them. Items
marked **[OPEN]** need a decision. Every change gets a line in the changelog at the bottom, and the
gold CSV records the guide version it used.

## Decisions needed before labelling (Gloria)

Collected 2026-11-18 from the guide and from the Opus p2 run on dev pages. Each one changes what
counts as a correct span, so settle them before labelling; then the prompt is updated once (p3)
and Opus is re-run once (about $1.30).

Items 1-4 are still open. Items 5-9 have a **[DEFAULT]** answer written into the rules in v0.3
(sections 2.0-2.4); Gloria confirms or changes it.

1. **Vernacular names** (`Hedge-Sparrow`, `THE CHASTE BULIMUS`): label as `taxon`, as a separate
   field, or not at all? Default: not at all.
2. **Relative words in localities** (`near Dover`): drop `near` from the span? Default: drop it.
3. **Month-only phenology** (`arrives in April`): a `date`? Default: no.
4. **Journal titles** (`Pro. Zool. Soc.`): an `institution`? Default: no.
5. **A full stop at the end of a span** (`Mus. Cuming.`, `LINN.`). **[DEFAULT, v0.3]** Keep it
   only when the word before it is shortened (`LINN.`, `Pfr.`, `Mus.`); drop it after a word
   printed in full (`Mus. Cuming`, `Lamarck`, `Brazil`). Rule 2.0.2. The value score ignores edge
   punctuation; only the exact-span score is affected.
6. **Titles other than Mr./Dr./Capt.** (`Lord Lilford`, `Herr Gätke`). **[DEFAULT, v0.3]** Treat
   every title like an honorific: span `Lilford`, `Gätke`, title in notes. Rule 2.3.
7. **Descriptive words before a place** (`valley of the Amoor`). **[DEFAULT, v0.3]** The whole
   phrase, following the existing narrowing-parts rule (`north coast of Norfolk`). Words that
   name a *part* of the place stay in; words that place something *relative to* it stay out
   (item 2). Rule 2.2.
8. **Same name in two roles on one page** (`Mus. Adams.` = institution; `ADAMS, MS.` = person, a
   manuscript source). **[DEFAULT, v0.3]** Label each by its role; added as worked examples in
   2.3 and 2.4.
9. **A name broken across lines** (`A. blak-|istoni`, `Ja‐|maica`). **[DEFAULT, v0.3]** One span
   from the first to the last character of the whole name, hyphen and line break included, for
   every field. Rule 2.0.3. A model output that covers only the first fragment is then not an
   exact match. Whether it earns credit under overlap match is a scoring decision for
   `PREREGISTRATION.md`, not a labelling rule.

Known prompt fix for p3 (not a guide question): the G1 prompt told the model to quote only the
first line of a name broken across lines, which truncates `A. blak-|istoni` to `A. blak-`. The
locator now handles quotes that run across lines, so p3 will ask for the whole name (matching 9).

## 0. Ground rules

1. **Label before you look.** Do not open any model output for a page before your gold labels for
   that page are final. This holds for every test page. For dev pages, label first if you can.
2. **Label the expert transcription**, not the legacy OCR: `data/sample/expert_view/<PageID>.txt` (in the repo; readable on GitHub).
   Use the scan (the `bhl_url` link in `data/sample_split.csv`) to resolve doubts about layout or
   italics, but the label always points into the expert text.
3. **Label what is printed.** Spans are copied as printed: archaic spelling, ligatures,
   abbreviations, hyphenation. Do not correct, expand or modernise in the span.
4. **One file per labeller**: `gold/gold_mentions_<labeller>.csv`, copied from the template.
5. When a rule does not cover a case, label your best guess, write `UNCLEAR:` and the reason in
   `notes`, and carry on. Unclear cases become rules in the next guide version.

## 1. What a label is

The unit is a **mention**: one span of characters in the expert text, plus a field type.

| Column | Meaning |
|---|---|
| `page_id` | BHL PageID |
| `start` | offset of the first character, counting from 0 |
| `end` | offset just *after* the last character (Python slice: `text[start:end]`) |
| `field` | `taxon`, `person`, `locality`, `institution` or `date` |
| `text` | the span, copied exactly |
| `notes` | free text; `UNCLEAR: …` for doubtful cases; `UNCERTAIN-IN-SOURCE` when the print itself hedges (e.g. a `?`) |
| `guide_version` | e.g. `v0.3` |

**Finding offsets.** Each line of `data/sample/expert_view/<PageID>.txt` starts with the offset where that line
begins. Offset of a word = line offset + its column, counting from 0. You can also leave `start`
and `end` empty and fill only `text`. `python src/check_gold.py` then reports the offsets when the
text occurs once on the page and asks you to resolve it when it occurs more than once. Either way,
the checker confirms that `text == page[start:end]` for every row.

A page with no target entities still gets one row: `field` = `none`, `start`/`end` empty. This
tells "labelled, nothing found" apart from "not labelled yet".

## 2. Fields

The entity types follow the NHM BHL prototype (Hartley, Gu & Smith, BHL Day 2026: taxa, people,
localities, institutions), so our numbers can be read next to theirs. `date` is our addition.
`taxon`, `person`, `locality` and `institution` are **named-entity mentions**: label every mention,
whatever role it plays on the page (collector, cited author, naming authority, distribution
statement...). `date` stays narrower: occurrence dates only (2.5).

### 2.0 Span edges (all fields)

1. A span starts at the first character of the entity and ends at its last character. Brackets,
   quotation marks, commas and semicolons around it stay out: `(Mus. Taylor.)` gives
   `Mus. Taylor`.
2. **[DEFAULT, v0.3]** **Full stop at the end.** Keep it only when the word right before it is a
   shortened form, because then the full stop is part of the abbreviation: `LINN.`, `Linn.`,
   `Pfr.`, `Gmel.`. Drop it after a word printed in full, where it is punctuation:
   `(Mus. Cuming.)` gives `Mus. Cuming`; `Achatina albolineata, Lamarck.` gives `Lamarck`;
   `Hab. Brazil.` gives `Brazil`. Full stops *inside* the span always stay (`Mus. Cuming`,
   `J. Smith`, `A. arvensis`). If you cannot tell whether a word is shortened, drop the full stop
   and write `UNCLEAR: abbreviation?` in notes.
3. **[DEFAULT, v0.3]** **Line breaks.** A name broken across lines is one span, from its first to
   its last character, with the hyphen and line break inside it: `A. blak-` + `istoni` is one
   `taxon`; `Ja‐` + `maica` is one `locality`. Never label only the first fragment.

### 2.1 `taxon`: scientific names

Label:
- Binomials and trinomials: `Accentor modularis`, `Bulimus castus`.
- Uninomials used as names of a taxon at any rank: `Bulimus`, `Turdidae`, `Coleoptera`.
- Abbreviated genus *with* an epithet: `A. modularis`, `Bul. castus`.
- Names in any case or style: `BULIMUS CASTUS` (small capitals) counts.
- A name broken across a line: one span, including the hyphen and line break.

Do not label:
- The authority after a name as part of the taxon: in `Accentor modularis (Linn.)` the taxon
  span is `Accentor modularis`; `Linn.` is a separate `person` mention (2.3).
- A bare abbreviated genus that only opens a Latin diagnosis: `Bul. testâ subfusiformi…`.
- Running heads, plate headings and other page furniture: the `BULIMUS.` printed at the top of
  every page of the monograph.
- **[DEFAULT]** Vernacular names (`Hedge-Sparrow`, `THE CHASTE BULIMUS`). **[OPEN]** Should they
  be labelled, perhaps as a separate field? Butler names most birds in English, so this choice
  changes Butler's counts a lot.

### 2.2 `locality`: a named geographic place

Label:
- Any named real place in the text, in whatever role: habitat, distribution, collection or
  observation statements, and other mentions such as `Key to the species of the Argentine Republic`.
  `Hab. Central America?` gives span `Central America`, with notes `UNCERTAIN-IN-SOURCE`.
- A place with its narrowing parts as one span: `Isle of Luzon, Philippine Islands`;
  `north coast of Norfolk`. **[DEFAULT, v0.3]** This includes descriptive words that name a part
  of the place: `valley of the Amoor`, `slopes of the Atlas Mountains`, `South-east Mongolia`.
  The test: the words name a piece of the place itself (coast, valley, slopes, mouth, interior,
  a compass part). Words that place something *relative to* the place (`near`, `north of`,
  `about ten miles from`) stay out; see the next list.
- Distribution statements in prose: in `it breeds in Scotland` the span is `Scotland`.
- Several different places as separate mentions: `Cornwall and Devon` gives two.

Do not label:
- Leading prepositions and relative words: in `near Dover` the span is `Dover`, with notes
  `near`. **[OPEN]** Keep or drop relative qualifiers ("near", "about", "north of")?
- Habitat types with no place name: `woods`, `marshes`, `on rocks`.
- **[DEFAULT]** Places inside bibliographic citations (place of publication).
- Places that are part of an institution's name: `Zoological Society of London` is one
  `institution`, not a locality.
- Adjectives like `British` in `British birds`, and places in titles or running heads.

### 2.3 `person`: a named person

Label:
- Any named person: collectors and observers (`shot by Mr. J. Smith` gives `J. Smith`), cited
  authors (`PFEIFFER, Pro. Zool. Soc.` gives `PFEIFFER`; `Giusti's (1997)` gives `Giusti`), and
  naming authorities, abbreviated or not (`Linn.`, `Pfr.`, `Lamarck`).
- Initials belong to the name (`J. Smith`); honorifics do not (`Mr.`, `Dr.`, `Capt.`; put them in notes).
  **[DEFAULT, v0.3]** The same holds for every other title, rank or form of address: `Lord`,
  `Sir`, `Herr`, `Rev.`, `Prof.`, `Lieut.`, `Col.`. `Lord Lilford` gives `Lilford` and
  `Herr Gätke` gives `Gätke`, with the title in notes.
- **[DEFAULT, v0.3]** Label a name by the role it plays at that spot, even when the same name has
  another role elsewhere on the page. On one Reeve page, `ADAMS, MS.` (a species described from
  Adams's manuscript) gives person `ADAMS` (`MS.` is not labelled), while `(Mus. Adams.)` gives
  institution `Mus. Adams` and no person.
- **[OPTIONAL]** The role in notes: `collector`, `author`, `authority`, `other`. It helps later
  analysis but is not scored in V1.

Do not label:
- A person's name inside a taxon name (`Cumingii` in `Bulimus Cumingii`) or inside an institution
  name (`Cuming` in `Mus. Cuming`).

### 2.4 `institution`: a named museum, collection or organisation

Label:
- Museums, herbaria, private collections, societies, universities, expeditions:
  `Mus. Cuming`, `Mus. Dennison`, `British Museum`, `Zoological Society of London`.
- The whole name as printed, including abbreviations such as `Mus.`. The full stop after the
  collector's name follows rule 2.0.2: `(Mus. Cuming.)` gives `Mus. Cuming`.
- A private collection named after a person who also appears as a person on the page: see the
  `Mus. Adams` / `ADAMS, MS.` example in 2.3.

Do not label:
- **[DEFAULT]** Journal titles in citations (`Pro. Zool. Soc.`, `Ann. Mag. Nat. Hist.`): they name a
  publication, not the organisation. **[OPEN]** Keep this default?
- Generic words without a name (`the museum`, `a collection`).

### 2.5 `date`: when an occurrence happened

Label:
- Dates of collection, observation, capture, nesting or arrival: `3rd May, 1890`; `May 1890`;
  `1890`; ranges such as `1880–85` (one span).
- The whole date expression as printed, with ordinal suffixes and commas inside it.

Do not label:
- Publication years in citations: in `PFEIFFER, Pro. Zool. Soc., 1846, p. 112` nothing is labelled.
- Seasons and months with no year that are only general phenology: `in spring`, `arrives in April`.
  **[OPEN]** Label month-only phenology (`arrives in April`)? Default: no.
- Ages, durations, page numbers.

Dates are expected to be rare in Reeve. That is a finding, not a problem.

## 3. Taxon linking (E4-lite, Butler only)

This is a separate pass, done **after** the mention labels for the page are final. It uses a
separate file, `gold/gold_links_<labeller>.csv`. One row per `taxon` mention:

| Column | Meaning |
|---|---|
| `page_id`, `start`, `end`, `text` | copied from the mention row |
| `match_type` | `exact` (name is the current accepted name) · `synonym` (name is an older name of an accepted taxon) · `fuzzy` (spelling variant of a known name) · `higher_rank` (only the genus or family can be identified) · `none` (no record found) · `ambiguous` (several candidates; list them in notes) |
| `gbif_usage_key` | GBIF key of the taxon the name refers to (the accepted taxon for `synonym`) |
| `accepted_name` | the current accepted name in GBIF |
| `notes` | sources consulted, reasoning |

Look names up by hand on gbif.org (species search). Note other sources you used, such as Avibase or
the IOC World Bird List. Reeve's names are not linked in V1: historical molluscan names need a
specialist.

## 4. Agreement check

A second labeller labels 5 test pages independently with this guide, without seeing Gloria's
labels. We report span-level agreement per field (exact and overlap) and discuss every
disagreement. A disagreement caused by the guide leads to a rule change and a new version.

## Changelog

| Version | Date | Change |
|---|---|---|
| v0.1 | 2026-11-18 | First draft. No pages labelled yet. |
| v0.2 | 2026-11-18 | Entity types aligned with the NHM BHL prototype: `collector` replaced by `person` (every named person); new `institution`; `locality` covers every named place, not only occurrence statements. `date` unchanged. No pages labelled yet. |
| v0.3 | 2026-11-18 | Default answers for decisions 5-9 (from the Opus p2 dev run): new 2.0 on span edges (full stop at the end kept only after a shortened word; names broken across lines are one span, every field); all titles treated like honorifics; descriptive part-of-place words stay in the locality span; `Mus. Adams` / `ADAMS, MS.` worked example. Decisions 1-4 still open. Prompt still `p2-guide-v0.2`; p3 waits until 1-4 are settled. No pages labelled yet. |

---

# 标注规范（中文版）

**版本 v0.3，草稿，2026-11-18。** 写于任何标注开始之前。v0.2 把实体类型和 NHM 的 BHL 原型对齐（见第 2 节）；v0.3 为 Opus p2 在开发集上发现的片段边界问题写了默认答案（见下面第 5–9 条）。
标 **[默认]** 的是为了先开始而选的做法，由 Gloria 确认或修改；标 **[待定]** 的需要做决定。每次修改都在文末的变更记录里加一行，gold CSV 里也记录所用的规范版本。

## 标注前需要决定的事（Gloria）

2026-11-18 从规范本身和 Opus p2 的开发集结果中整理。每一条都会改变"什么片段算对"，所以要在标注前定下来；定好后提示词只改一次（p3），Opus 只重跑一次（约 $1.30）。

第 1–4 条还没定。第 5–9 条在 v0.3 里已经写了 **[默认]** 答案（第 2.0–2.4 节），由 Gloria 确认或修改。

1. **英文俗名**（`Hedge-Sparrow`、`THE CHASTE BULIMUS`）：标成 `taxon`、单独设一个字段，还是不标？默认：不标。
2. **地点里的相对位置词**（`near Dover`）：片段里去掉 `near` 吗？默认：去掉。
3. **只有月份的物候**（`arrives in April`）：算 `date` 吗？默认：不算。
4. **期刊名**（`Pro. Zool. Soc.`）：算 `institution` 吗？默认：不算。
5. **片段末尾的句点**（`Mus. Cuming.`、`LINN.`）。**[默认，v0.3]** 只有句点前的词是缩写时才保留（`LINN.`、`Pfr.`、`Mus.`）；前面是完整拼写的词时去掉（`Mus. Cuming`、`Lamarck`、`Brazil`）。见规则 2.0.2。按值评分时忽略首尾标点，只影响"位置完全一致"这一级的分数。
6. **Mr./Dr./Capt. 以外的头衔**（`Lord Lilford`、`Herr Gätke`）。**[默认，v0.3]** 所有头衔都按敬称处理：片段是 `Lilford`、`Gätke`，头衔写进备注。见规则 2.3。
7. **地名前的描述词**（`valley of the Amoor`）。**[默认，v0.3]** 整个短语都算，沿用已有的"缩小范围的部分算在地名里"规则（`north coast of Norfolk`）。表示地点*一部分*的词留在片段里；表示*相对于*这个地点的位置的词不算（见第 2 条）。见规则 2.2。
8. **同一页上同一个名字有两种角色**（`Mus. Adams.` 是机构；`ADAMS, MS.` 是人，指手稿出处）。**[默认，v0.3]** 按各自的角色分别标；已在 2.3 和 2.4 中加了示例。
9. **跨行断开的名字**（`A. blak-|istoni`、`Ja‐|maica`）。**[默认，v0.3]** 所有字段都标成一个片段，从整个名字的第一个字符到最后一个字符，中间的连字符和换行都包括在内。见规则 2.0.3。模型输出如果只覆盖第一段，就不算"位置完全一致"；在"位置重叠"这一级算不算对，是 `PREREGISTRATION.md` 里的评分决定，不是标注规则。

p3 已知要修的提示词问题（不是规范问题）：G1 的提示词让模型对跨行断开的名字只引用第一行的部分，结果 `A. blak-|istoni` 被截成了 `A. blak-`。定位代码现在已经能处理跨行引文，所以 p3 会要求模型引用完整的名字（与第 9 条一致）。

## 0. 基本原则

1. **先标注，后看输出。** 一页的 gold 标签定稿之前，不要打开这一页的任何模型输出。所有测试页都必须这样；开发页能做到最好。
2. **在专家转录上标注**，不是在旧 OCR 上：`data/sample/expert_view/<PageID>.txt`（在仓库里，GitHub 上就能看）。版式或斜体有疑问时可以看扫描图（`data/sample_split.csv` 里的 `bhl_url` 链接），但标签始终指向专家转录的文字。
3. **按印刷原样标。** 片段照原样抄：古旧拼法、连字、缩写、断词都保留。不要在片段里改正、展开或现代化。
4. **每个标注人一个文件**：`gold/gold_mentions_<标注人>.csv`，从模板复制。
5. 规则没覆盖到的情况，按你的最佳判断标，在 `notes` 里写 `UNCLEAR:` 和原因，然后继续。不清楚的情况会在下一版规范里变成规则。

## 1. 一个标签是什么

标注单位是一个**提及**（mention）：专家转录里的一段字符，加上字段类型。

| 列 | 含义 |
|---|---|
| `page_id` | BHL PageID |
| `start` | 第一个字符的位置，从 0 开始数 |
| `end` | 最后一个字符*之后*的位置（Python 切片：`text[start:end]`） |
| `field` | `taxon`、`person`、`locality`、`institution` 或 `date` |
| `text` | 片段，原样抄写 |
| `notes` | 自由文本；拿不准的写 `UNCLEAR: …`；原文本身就有保留（比如带 `?`）时写 `UNCERTAIN-IN-SOURCE` |
| `guide_version` | 例如 `v0.3` |

**怎么找位置。** `data/sample/expert_view/<PageID>.txt` 每一行开头都是这一行起始字符的位置。一个词的位置 = 行起始位置 + 它在这一行里的列号（从 0 开始数）。你也可以把 `start` 和 `end` 留空，只填 `text`：运行 `python src/check_gold.py`，文字在页面上只出现一次时它会给出位置，出现多次时会列出所有位置让你选。不管哪种方式，检查脚本都会确认每一行都满足 `text == page[start:end]`。

没有目标实体的页面也要写一行：`field` 填 `none`，`start`/`end` 留空。这样能区分"标过了，什么都没有"和"还没标"。

## 2. 字段

实体类型沿用 NHM 的 BHL 原型（Hartley、Gu、Smith，BHL Day 2026：学名、人、地点、机构），这样我们的数字可以和他们的放在一起看。`date` 是我们另加的。`taxon`、`person`、`locality`、`institution` 是**命名实体提及**：不管它在页面上起什么作用（采集人、被引用的作者、命名人、分布描述……），每一次出现都要标。`date` 范围窄一些：只标发生日期（2.5）。

### 2.0 片段边界（所有字段）

1. 片段从实体的第一个字符开始，到它的最后一个字符结束。外面的括号、引号、逗号、分号都不算：`(Mus. Taylor.)` 标成 `Mus. Taylor`。
2. **[默认，v0.3]** **末尾的句点。** 只有句点前的词是缩写形式时才保留，因为这时句点是缩写的一部分：`LINN.`、`Linn.`、`Pfr.`、`Gmel.`。前面是完整拼写的词时去掉，因为这时句点只是标点：`(Mus. Cuming.)` 标成 `Mus. Cuming`；`Achatina albolineata, Lamarck.` 标成 `Lamarck`；`Hab. Brazil.` 标成 `Brazil`。片段*内部*的句点一律保留（`Mus. Cuming`、`J. Smith`、`A. arvensis`）。分不清一个词是不是缩写时，去掉句点，并在备注里写 `UNCLEAR: abbreviation?`。
3. **[默认，v0.3]** **换行。** 跨行断开的名字是一个片段，从第一个字符到最后一个字符，中间的连字符和换行包括在内：`A. blak-` + `istoni` 是一个 `taxon`；`Ja‐` + `maica` 是一个 `locality`。不要只标第一段。

### 2.1 `taxon`：学名

要标：
- 二名和三名：`Accentor modularis`、`Bulimus castus`。
- 用作任一等级分类单元名称的单名：`Bulimus`、`Turdidae`、`Coleoptera`。
- 缩写属名*加*种加词：`A. modularis`、`Bul. castus`。
- 任何大小写或字体都算：`BULIMUS CASTUS`（小型大写）也算。
- 跨行断开的名字：一个片段，包括连字符和换行。

不标：
- 名字后面的命名人不算在学名里：`Accentor modularis (Linn.)` 中，学名片段是 `Accentor modularis`；`Linn.` 另外标成一个 `person`（2.3）。
- 只是用来开头一段拉丁文描述的单独缩写属名：`Bul. testâ subfusiformi…`。
- 页眉、图版标题等版面元素：比如专著每页顶部印的 `BULIMUS.`。
- **[默认]** 英文俗名（`Hedge-Sparrow`、`THE CHASTE BULIMUS`）。**[待定]** 要不要标，比如作为单独字段？Butler 大多用英文名称呼鸟，所以这个决定对 Butler 的计数影响很大。

### 2.2 `locality`：有名字的地理位置

要标：
- 文中任何有名字的真实地点，不管起什么作用：栖息地、分布、采集或观察记录，以及其他提到地点的地方，比如 `Key to the species of the Argentine Republic`。`Hab. Central America?` 标成 `Central America`，备注写 `UNCERTAIN-IN-SOURCE`。
- 地点连同缩小范围的部分算一个片段：`Isle of Luzon, Philippine Islands`；`north coast of Norfolk`。**[默认，v0.3]** 这也包括表示地点一部分的描述词：`valley of the Amoor`、`slopes of the Atlas Mountains`、`South-east Mongolia`。判断标准：这些词指的是地点本身的一部分（海岸、河谷、山坡、河口、内陆、某个方位的部分）。表示*相对于*这个地点的位置的词（`near`、`north of`、`about ten miles from`）不算进去，见下一组。
- 正文中的分布描述：`it breeds in Scotland` 中，片段是 `Scotland`。
- 几个不同的地点分别标：`Cornwall and Devon` 是两个。

不标：
- 开头的介词和相对位置词：`near Dover` 中，片段是 `Dover`，备注写 `near`。**[待定]** 相对位置词（"near"、"about"、"north of"）保留还是去掉？
- 没有地名的生境类型：`woods`、`marshes`、`on rocks`。
- **[默认]** 文献引用里的地点（出版地）。
- 属于机构名称一部分的地点：`Zoological Society of London` 是一个 `institution`，不是地点。
- 形容词，比如 `British birds` 里的 `British`；标题或页眉里的地点。

### 2.3 `person`：有名字的人

要标：
- 任何有名字的人：采集人和观察者（`shot by Mr. J. Smith` 标成 `J. Smith`），被引用的作者（`PFEIFFER, Pro. Zool. Soc.` 标成 `PFEIFFER`；`Giusti's (1997)` 标成 `Giusti`），以及命名人，缩写与否都算（`Linn.`、`Pfr.`、`Lamarck`）。
- 首字母缩写属于名字（`J. Smith`）；敬称不属于（`Mr.`、`Dr.`、`Capt.`，写进备注）。**[默认，v0.3]** 其他头衔、军衔和称呼也一样：`Lord`、`Sir`、`Herr`、`Rev.`、`Prof.`、`Lieut.`、`Col.`。`Lord Lilford` 标成 `Lilford`，`Herr Gätke` 标成 `Gätke`，头衔写进备注。
- **[默认，v0.3]** 按名字在那个位置的角色来标，即使同一个名字在同一页别处有另一种角色。Reeve 的某一页上，`ADAMS, MS.`（根据 Adams 的手稿描述的物种）标成人 `ADAMS`（`MS.` 不标），而 `(Mus. Adams.)` 标成机构 `Mus. Adams`，不另标人。
- **[可选]** 在备注里写角色：`collector`、`author`、`authority`、`other`。对之后的分析有帮助，V1 不计分。

不标：
- 学名里的人名（`Bulimus Cumingii` 里的 `Cumingii`），或机构名里的人名（`Mus. Cuming` 里的 `Cuming`）。

### 2.4 `institution`：有名字的博物馆、收藏或组织

要标：
- 博物馆、植物标本馆、私人收藏、学会、大学、考察队：`Mus. Cuming`、`Mus. Dennison`、`British Museum`、`Zoological Society of London`。
- 按印刷的完整名称标，包括 `Mus.` 这样的缩写。收藏者名字后面的句点按规则 2.0.2 处理：`(Mus. Cuming.)` 标成 `Mus. Cuming`。
- 以某个人命名、而这个人在同一页上也作为人出现的私人收藏：见 2.3 里 `Mus. Adams` / `ADAMS, MS.` 的例子。

不标：
- **[默认]** 文献引用里的期刊名（`Pro. Zool. Soc.`、`Ann. Mag. Nat. Hist.`）：它们指的是出版物，不是组织本身。**[待定]** 保留这个默认吗？
- 没有名字的泛称（`the museum`、`a collection`）。

### 2.5 `date`：发生的日期

要标：
- 采集、观察、捕获、筑巢或抵达的日期：`3rd May, 1890`；`May 1890`；`1890`；`1880–85` 这样的范围（一个片段）。
- 按印刷的完整日期表达式标，包括序数后缀和中间的逗号。

不标：
- 文献引用里的出版年份：`PFEIFFER, Pro. Zool. Soc., 1846, p. 112` 里什么都不标。
- 只描述一般物候、没有年份的季节和月份：`in spring`、`arrives in April`。**[待定]** 只有月份的物候（`arrives in April`）要不要标？默认：不标。
- 年龄、时长、页码。

Reeve 里日期预计会很少。这是一个发现，不是问题。

## 3. 学名关联（E4-lite，只做 Butler）

这是单独的一轮，在一页的提及标签定稿**之后**做，用单独的文件 `gold/gold_links_<标注人>.csv`。每个 `taxon` 提及一行：

| 列 | 含义 |
|---|---|
| `page_id`、`start`、`end`、`text` | 从提及那一行复制 |
| `match_type` | `exact`（这个名字就是现在的有效名）· `synonym`（是某个有效分类单元的旧名）· `fuzzy`（已知名字的拼写变体）· `higher_rank`（只能确定到属或科）· `none`（找不到记录）· `ambiguous`（有几个候选，在备注里列出来） |
| `gbif_usage_key` | 这个名字所指分类单元的 GBIF key（`synonym` 填对应有效分类单元的） |
| `accepted_name` | GBIF 里现在的有效名 |
| `notes` | 查过的来源和理由 |

在 gbif.org 上手动查（物种搜索）。用了其他来源也要记下来，比如 Avibase 或 IOC World Bird List。V1 不关联 Reeve 的名字：历史上的软体动物名称需要专家判断。

## 4. 一致性检查

第二位标注人按这份规范独立标注 5 页测试页，不看 Gloria 的标签。我们按字段报告片段级的一致性（完全一致和重叠两种口径），并逐条讨论每一处分歧。因规范不清而产生的分歧会变成规则修改和新版本。

## 变更记录

| 版本 | 日期 | 修改 |
|---|---|---|
| v0.1 | 2026-11-18 | 初稿。尚未标注任何页面。 |
| v0.2 | 2026-11-18 | 实体类型对齐 NHM 的 BHL 原型：`collector` 改为 `person`（所有有名字的人）；新增 `institution`；`locality` 覆盖所有有名字的地点，不只是发生记录。`date` 不变。尚未标注任何页面。 |
| v0.3 | 2026-11-18 | 为第 5–9 条写默认答案（来自 Opus p2 的开发集结果）：新增 2.0 片段边界（末尾句点只在缩写后保留；跨行断开的名字在所有字段都算一个片段）；所有头衔按敬称处理；表示地点一部分的描述词留在地点片段里；增加 `Mus. Adams` / `ADAMS, MS.` 示例。第 1–4 条仍待定。提示词仍是 `p2-guide-v0.2`；p3 等第 1–4 条定下来再改。尚未标注任何页面。中文版于同日加入本文件。 |
