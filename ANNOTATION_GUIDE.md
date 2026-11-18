# Annotation guide

**Version v0.2, draft, 2026-11-18.** Written before any labelling. v0.2 aligns the entity types with the
NHM BHL prototype (see section 2).
Defaults marked **[DEFAULT]** were chosen to get started; Gloria confirms or changes them. Items
marked **[OPEN]** need a decision. Every change gets a line in the changelog at the bottom, and the
gold CSV records the guide version it used.

## Decisions needed before labelling (Gloria)

Collected 2026-11-18 from the guide and from the Opus p2 run on dev pages. Each one changes what
counts as a correct span, so settle them before labelling; then the prompt is updated once (p3)
and Opus is re-run once (about $1.30).

1. **Vernacular names** (`Hedge-Sparrow`, `THE CHASTE BULIMUS`): label as `taxon`, as a separate
   field, or not at all? Default: not at all.
2. **Relative words in localities** (`near Dover`): drop `near` from the span? Default: drop it.
3. **Month-only phenology** (`arrives in April`): a `date`? Default: no.
4. **Journal titles** (`Pro. Zool. Soc.`): an `institution`? Default: no.
5. **A full stop that ends an abbreviation** (`Mus. Cuming.`, `LINN.`): inside the span or not?
   The value score ignores edge punctuation; only the exact-span score is affected. Suggested:
   include a full stop that belongs to an abbreviation (`LINN.`), exclude a sentence-ending one
   (`Mus. Cuming`).
6. **Titles other than Mr./Dr./Capt.** (`Lord Lilford`, `Herr Gätke`): part of the person span?
   Suggested: treat like honorifics, span `Lilford`.
7. **Descriptive words before a place** (`valley of the Amoor`): span `Amoor` or the whole phrase?
   The guide now says a place with its narrowing parts is one span (`north coast of Norfolk`), so
   by that rule the whole phrase. Confirm.
8. **Same name in two roles on one page** (`Mus. Adams` = institution; `ADAMS, MS.` = person, a
   manuscript source): label each by its role, as the guide says. Add as an example? Suggested: yes.

Known prompt fix for p3 (not a guide question): the G1 prompt told the model to quote only the
first line of a name broken across lines, which truncates `A. blak-|istoni` to `A. blak-`. The
locator now handles quotes that run across lines, so p3 will ask for the whole name.

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
| `guide_version` | e.g. `v0.2` |

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
  `north coast of Norfolk`.
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
- **[OPTIONAL]** The role in notes: `collector`, `author`, `authority`, `other`. It helps later
  analysis but is not scored in V1.

Do not label:
- A person's name inside a taxon name (`Cumingii` in `Bulimus Cumingii`) or inside an institution
  name (`Cuming` in `Mus. Cuming`).

### 2.4 `institution`: a named museum, collection or organisation

Label:
- Museums, herbaria, private collections, societies, universities, expeditions:
  `Mus. Cuming`, `Mus. Dennison`, `British Museum`, `Zoological Society of London`.
- The whole name as printed, including abbreviations such as `Mus.`.

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
