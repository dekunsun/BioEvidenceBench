# Annotation guide

**Version v0.1, draft, 2026-11-18.** Written before any labelling and before any model output exists.
Defaults marked **[DEFAULT]** were chosen to get started; Gloria confirms or changes them. Items
marked **[OPEN]** need a decision. Every change gets a line in the changelog at the bottom, and the
gold CSV records the guide version it used.

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
| `field` | `taxon`, `locality`, `date` or `collector` |
| `text` | the span, copied exactly |
| `notes` | free text; `UNCLEAR: …` for doubtful cases; `UNCERTAIN-IN-SOURCE` when the print itself hedges (e.g. a `?`) |
| `guide_version` | e.g. `v0.1` |

**Finding offsets.** Each line of `data/sample/expert_view/<PageID>.txt` starts with the offset where that line
begins. Offset of a word = line offset + its column, counting from 0. You can also leave `start`
and `end` empty and fill only `text`. `python src/check_gold.py` then reports the offsets when the
text occurs once on the page and asks you to resolve it when it occurs more than once. Either way,
the checker confirms that `text == page[start:end]` for every row.

A page with no target entities still gets one row: `field` = `none`, `start`/`end` empty. This
tells "labelled, nothing found" apart from "not labelled yet".

## 2. Fields

The fields follow what a biodiversity database would keep from a page: **who was where, when**.
That is why citation years and naming authorities are *not* labelled in V1.

### 2.1 `taxon`: scientific names

Label:
- Binomials and trinomials: `Accentor modularis`, `Bulimus castus`.
- Uninomials used as names of a taxon at any rank: `Bulimus`, `Turdidae`, `Coleoptera`.
- Abbreviated genus *with* an epithet: `A. modularis`, `Bul. castus`.
- Names in any case or style: `BULIMUS CASTUS` (small capitals) counts.
- A name broken across a line: one span, including the hyphen and line break.

Do not label:
- The authority or citation after a name: in `Accentor modularis (Linn.)` the span is
  `Accentor modularis` only.
- A bare abbreviated genus that only opens a Latin diagnosis: `Bul. testâ subfusiformi…`.
- Running heads, plate headings and other page furniture: the `BULIMUS.` printed at the top of
  every page of the monograph.
- **[DEFAULT]** Vernacular names (`Hedge-Sparrow`, `THE CHASTE BULIMUS`). **[OPEN]** Should they
  be labelled, perhaps as a separate field? Butler names most birds in English, so this choice
  changes Butler's counts a lot.

### 2.2 `locality`: where an organism lives, was found, or was seen

Label:
- Place names in a habitat, distribution, collection or observation statement:
  `Hab. Central America?` gives span `Central America`, with notes `UNCERTAIN-IN-SOURCE`.
- A place with its narrowing parts as one span: `Isle of Luzon, Philippine Islands`;
  `north coast of Norfolk`.
- Distribution statements in prose: in `it breeds in Scotland` the span is `Scotland`.
- Several different places as separate mentions: `Cornwall and Devon` gives two.

Do not label:
- Leading prepositions and relative words: in `near Dover` the span is `Dover`, with notes
  `near`. **[OPEN]** Keep or drop relative qualifiers ("near", "about", "north of")?
- Habitat types with no place name: `woods`, `marshes`, `on rocks`.
- Places in bibliographic citations, publishers, or museum names: `Mus. Cuming` is not a locality.
- Adjectives like `British` in `British birds`, and places in titles or running heads.

### 2.3 `date`: when an occurrence happened

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

### 2.4 `collector`: who collected or observed it

Label:
- A person named as collecting, shooting, finding, observing or sending the specimen:
  in `shot by Mr. J. Smith` the span is `J. Smith` (honorific excluded, notes `Mr.`).

Do not label:
- Naming authorities and cited authors: `Pfeiffer`, `Lamarck`, `Linn.`.
- Collections, museums and owners: `Mus. Dennison`, `Mus. Cuming`. In Reeve, `Mus.` means the
  specimen's collection, not who collected it. If the text says so explicitly
  (`collected by Mr. Cuming`), label it.

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
