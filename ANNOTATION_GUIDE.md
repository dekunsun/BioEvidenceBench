# Annotation guide

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
