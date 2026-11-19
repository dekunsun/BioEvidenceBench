# Annotation guide

> 中文版在本文件下方：[跳到中文版](#标注规范中文版)。两个版本内容相同；如有出入，以英文版为准，并请指出来改正。

**Version v0.10, 2026-11-20.** v0.5 was written before any labelling. v0.6 adds the rules Gloria
decided after labelling the six dev pages; v0.7 to v0.10 add rules decided while labelling the test pages
(see the changelog). None changes an earlier rule. The prompt (`p4`) was written from v0.6 and
is **not** updated from rules found on test pages (section 4); the gold set uses the latest version. Later changes get a new version number and a changelog line; the gold CSV
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
| `scan_text` | normally empty. Fill it only where the **transcription itself is wrong against the scan**: the text as the scan prints it. The row's `text` and offsets still follow the transcription file exactly (the checker requires that), and notes get `TRANSCRIPTION-ERROR`. Example: the file has `Fringilla nontifringilla`, the scan prints `Fringilla montifringilla`. At value level the scorer accepts either reading, and the linking step looks up the scan's reading |
| `adjudication` | empty for a clear row. For a row that was `UNCLEAR`: `adjudicated` (decided; scored normally) or `ambiguous` (still open; left out of strict scoring). `excluded`: the row was considered and is **not** a mention under the rule named in notes; it is kept so the decision stays visible, and it is not gold. See section 4 |
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
5. **Titles of cited works (every field, v0.8).** Nothing inside the title of a cited book, paper
   or journal is a mention: the title names a publication, it does not say anything about an
   organism or a place. `"Foreign Finches in Captivity", p. 249` gives no `vernacular`;
   `"Birds of Northamptonshire"` gives no `locality`. An author named beside the title is still
   a `person`.

### 2.1 `taxon`: scientific names

Label:
- Binomials and trinomials: `Accentor modularis`, `Bulimus castus`.
- Uninomials used as names of a taxon at any rank: `Bulimus`, `Turdidae`, `Coleoptera`.
- Abbreviated genus *with* an epithet: `A. modularis`, `Bul. castus`.
- Names in any case or style: `BULIMUS CASTUS` (small capitals) counts.
- The Latin plural of a genus name, used for the members of that genus: `these small Bulimi and
  Achatinæ` gives two `taxon` mentions, `Bulimi` and `Achatinæ`, with `plural form` in notes.
  (The same way `the Buntings` is a `vernacular`.)
- A genus name given in brackets inside a citation, saying under which genus the species was
  described: `PFEIFFER, (Glandina,) Pro. Zool. Soc.` gives taxon `Glandina`.
- A bare epithet that shares the genus of a name just before it in the same phrase (v0.10):
  `the B. rugiferus and Darwinii` gives two `taxon` mentions, `B. rugiferus` and `Darwinii`; notes
  `epithet only, genus implied`. An epithet standing alone with no such name before it is not
  covered by this rule: label it and write `UNCLEAR`.

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
- Capital or lower-case makes no difference: `pheasants`, `partridges`, `grouse`, `Owls` are
  labelled like `Jackdaw`. Any kind of organism counts, not only the group the book is about
  (`hares`, `chickens`).
- Broad group names count as well: `insects`, `lizards`, `mice`. (v0.7)
- A name that stands as its own word is labelled even when it refers to material or surroundings
  rather than a living organism: `moss` in a nest, `a hawthorn hedge`. (v0.7)

Do not label:
- Generic words that name no particular kind: `species`, `the male`, `the young`, and the book's
  own subject word (`bird` in Butler, `shell` in Reeve).
- A name that is only one part of a hyphenated compound for something else: `grass` in
  `grass-stalks` (v0.7; the same idea as `Sparrow-Hawk` below).
- Words for an age, a sex or a stage rather than a kind: `lambs`, `chicks`, `nestlings`, `the hen`.
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
- Named regions used as proper names: `the Continent` (span `Continent`), `Old World`.
- A place that shares its name with a person is labelled by its role at that spot: `Lord Lilford`
  is a `person`; `the park and pleasure-grounds of Lilford` is a `locality`.

**One place or several?** Decide from the wording, not from geography you look up.
- Names separated by commas, each later name being the wider region that holds the earlier one,
  are **one span**: `Merida, Andes of Bolivia`; `Humeerpore, Bundelkhund, India`;
  `Coban, Vera Cruz, Central America`. Test: the comma can be read as "in".
- Names joined by `and` or `or`, separated by a semicolon, or listed side by side as places of the
  same kind (`China, North-west India, Afghanistan, Persia`) are **separate mentions**.
- If you do not know the places: in a `Hab.` line, assume the order runs from narrow to wide (that
  is how Reeve writes localities), label one span and write `hierarchy assumed` in notes. Old or
  doubtful geography is not corrected and not checked (`Coban, Vera Cruz` stays as printed).

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

Only a word for a natural feature or a compass part, joined directly to the name, counts as part
of the place: `valley of`, `coast of`, `cliffs of` (`cliffs of Dover`), `slopes of`, `mouth of`,
`banks of`, `interior of`, `North-west`. Buildings and grounds do not: `the park and
pleasure-grounds of Lilford` gives `Lilford`.

Do not label:
- Habitat types with no place name: `woods`, `marshes`, `on rocks`.
- Places inside bibliographic citations (place of publication).
- Places that are part of an institution's name: `Zoological Society of London` is one
  `institution`, not a locality.
- Adjectives like `British` in `British birds`, and places in titles or running heads. Titles
  include the titles of cited works: `"Birds of Northamptonshire"`, `"Natural History and Sport
  in Moray"` and `"Notes from Redcar"` give no locality.
- Common nouns that point back to a place: `the island`, `this county`.

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
| `the immigration of Hoodies from the 12th to the 30th of October` | `12th to the 30th of October`, notes `NO-YEAR` | a dated, recorded movement: the day numbers make it an event |
| `arrives in April` | no | general phenology, not one event |
| `noticed in largest numbers in October and November` | no | what generally happens |
| `breeds in spring` | no | general phenology |
| `PFEIFFER, Pro. Zool. Soc., 1846, p. 112` | no date (`PFEIFFER` is a `person`) | publication year |
| `published in April 1890` | no | publication date |

Label:
- The whole date expression as printed, with ordinal suffixes and commas inside it; ranges such
  as `1880–85` or `12th to the 30th of October` are one span.
- Rule of thumb: a day number or a year tied to something observed marks an event. A bare month
  or season that says what generally happens does not.

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

**Short procedure (Gloria, 2026-11-20).** Fill one row per distinct printed name in
`gold/gold_links_gloria_names.csv`; `python src/expand_links.py` copies each decision to every
mention. Only four columns are required: `printed_rank`, `resolution_status`, `accepted_name`
(the accepted name you settled on, e.g. `Alauda arvensis`; the genus for `partial`; empty for
`unresolved`) and `evidence_source`; the other columns are optional. No number is copied: the
GBIF website now shows new taxon codes (gbif.org/taxon/BFFT), while the API the scorer uses keeps
the numeric backbone keys, so `expand_links.py` looks the accepted name up in that API by exact,
rank-checked match and fills `accepted_usage_key`; a name that is not an exact accepted match is
left empty and listed for review (`gold/gold_links_gloria_key_lookup.csv`). For a species name:
look the name up in Avibase first (independent of GBIF) to learn the current species. Spend **at most about
three minutes per name**; if it is not settled by then, write `ambiguous` (candidates in notes)
or `unresolved` (where you looked in notes). Both are legitimate answers and are counted apart.

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

**Two kinds of doubt, kept apart.** `UNCLEAR` means *we*, the labellers, are not sure how to label
or where the span ends; such a row waits for adjudication. `UNCERTAIN-IN-SOURCE` means the label
is sure but the *author* hedges a fact (`is reputed to have occurred on Greenland`; `probably
from New Granada, but I have no authority`); such a row is scored like any other.

**Order of work on a test page.** Gloria labels the page alone first and saves that file (a
commit) before she looks at anyone else's labels for it, a person's or an AI assistant's. A
comparison afterwards is a second opinion: it may raise questions, and every change it leads to
is one row in `gold/gold_changes_<labeller>.csv`. The assistant should not be a model under
evaluation; if it is, the report says so. (The six dev pages were made this way: labelled by
Gloria first, then compared with an AI assistant.)

**Rules found while labelling test pages.** A new rule goes into the guide (new version) and the
rows it decides are marked with that version in the column `later_rule` (filled in at
adjudication; the labeller leaves it empty). `guide_version` only says which guide was in force
when the row was labelled. It is **not** added to the prompt: the prompt is tuned
on dev pages only, and a rule that exists because of a test page would leak the test set into it.
Scores are reported twice, with all gold rows and with the rows decided under a later guide
version than the prompt's treated as optional. That covers both directions: a row labelled under
a later rule, and an `excluded` row that a later rule took out.

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
| v0.6 | 2026-11-19 | Rules decided by Gloria after labelling the six dev pages; no earlier rule changes. `taxon`: Latin plurals of genus names (`Bulimi`, `Achatinæ`) and a genus in citation brackets (`(Glandina,)`) are labelled. `vernacular`: case makes no difference; age, sex and stage words are out. `locality`: one span for comma-separated names running from narrow to wide, separate mentions for lists (decided from the wording, not from looked-up geography); named regions (`Continent`, `Old World`); only natural-feature words are part of a place; places in titles of cited works and common nouns (`the island`) are out. `date`: a day number tied to a recorded movement is an event (`12th to the 30th of October`, `NO-YEAR`). Section 4: `UNCLEAR` vs `UNCERTAIN-IN-SOURCE`; a test page is labelled alone and saved before any comparison. Dev gold: three rows added on Gloria's decision (`gold/gold_changes_gloria.csv`). |
| v0.7 | 2026-11-19 | Decided by Gloria on the first test page (8992328), `vernacular` only: broad group names are labelled (`insects`); only the book's own subject word is generic; a name standing as its own word is labelled even when it means material (`moss`); a name that is one part of a hyphenated compound is not (`grass` in `grass-stalks`). Section 4: rules found on test pages go into the guide but not into the prompt; scores are reported with and without the rows they decide. |
| v0.8 | 2026-11-19 | Decided by Gloria on test page 8992379: nothing inside the title of a cited work is a mention, in any field (2.0.5; v0.6 said this for places only). New `adjudication` value `excluded` for a row that was considered and is not a mention. |
| v0.9 | 2026-11-19 | Found by Gloria on test page 8992489: the expert transcription has a typo (`Fringilla nontifringilla` for the scan's `montifringilla`). New optional column `scan_text` for such cases; `text` and offsets keep following the transcription. Known cases are listed in `data/transcription_errata.csv`. No rule about what counts as a mention changes. |
| v0.10 | 2026-11-20 | Decided by Gloria on test page 8966802: a bare epithet sharing the genus of the name just before it (`B. rugiferus and Darwinii`) is a `taxon` mention (2.1). |

---

# 标注规范（中文版）

**版本 v0.10，2026-11-20。** v0.5 写于任何标注开始之前。v0.6 加入 Gloria 标完 6 页开发集后决定的规则；v0.7 到 v0.10 加入标测试页过程中决定的规则（见变更记录）。这几版都没有改动之前的规则。提示词（`p4`）按 v0.6 写成，**不会**根据测试页上发现的规则更新（第 4 节）；gold set 以最新版为准。之后再改要换版本号，并在变更记录里加一行；gold CSV 的每一行都记录所用的规范版本。

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
| `scan_text` | 一般留空。只有**转录文件本身和扫描图不一致**时才填：填扫描图上印的文字。这一行的 `text` 和位置仍然严格按转录文件来（检查脚本要求一致），备注里写 `TRANSCRIPTION-ERROR`。例子：文件里是 `Fringilla nontifringilla`，扫描图上印的是 `Fringilla montifringilla`。值级评分时两种读法都算对，学名关联时用扫描图的读法去查 |
| `adjudication` | 清楚的行留空。曾经标过 `UNCLEAR` 的行填：`adjudicated`（已裁定，正常评分）或 `ambiguous`（仍有歧义，不纳入严格评分）。见第 4 节 `excluded`：这一行考虑过，但按备注里写的规则**不算**提及；保留它是为了让这个决定看得见，它不是 gold。 |
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
5. **被引用著作的标题（所有字段，v0.8）。** 被引用的书、论文或期刊的标题里，任何内容都不算提及：标题指的是一份出版物，不是在陈述某种生物或某个地点。`"Foreign Finches in Captivity", p. 249` 不标 `vernacular`；`"Birds of Northamptonshire"` 不标 `locality`。标题旁边写出的作者仍然标 `person`。

### 2.1 `taxon`：学名

要标：
- 二名和三名：`Accentor modularis`、`Bulimus castus`。
- 用作任一等级分类单元名称的单名：`Bulimus`、`Turdidae`、`Coleoptera`。
- 缩写属名*加*种加词：`A. modularis`、`Bul. castus`。
- 任何大小写或字体都算：`BULIMUS CASTUS`（小型大写）也算。
- 属名的拉丁复数形式，用来指这个属的成员：`these small Bulimi and Achatinæ` 标成两个 `taxon`，`Bulimi` 和 `Achatinæ`，备注写 `plural form`。（道理和 `the Buntings` 标成 `vernacular` 一样。）
- 文献引用里括号中的属名，说明这个种当初归在哪个属下：`PFEIFFER, (Glandina,) Pro. Zool. Soc.` 标出 taxon `Glandina`。
- 同一句里和前一个学名共用属名的单独种加词（v0.10）：`the B. rugiferus and Darwinii` 标成两个 `taxon`，`B. rugiferus` 和 `Darwinii`，备注写 `epithet only, genus implied`。前面没有这样的学名、孤零零的种加词不适用这条，先标上并写 `UNCLEAR`。

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
- 大写小写都一样：`pheasants`、`partridges`、`grouse`、`Owls` 和 `Jackdaw` 一样要标。任何生物的种类名都算，不限于这本书讲的类群（`hares`、`chickens`）。
- 大的类群名也算：`insects`、`lizards`、`mice`。（v0.7）
- 独立成词的名字，即使指的是材料或环境而不是活的生物，也要标：巢里的 `moss`、`a hawthorn hedge`。（v0.7）

不标：
- 不指特定类群的泛称：`species`、`the male`、`the young`，以及这本书自己的主题词（Butler 里的 `bird`，Reeve 里的 `shell`）。
- 只是连字符复合词一部分、而复合词指的是别的东西的名字：`grass-stalks` 里的 `grass`（v0.7；和下面 `Sparrow-Hawk` 是同一个道理）。
- 表示年龄、性别或发育阶段而不是种类的词：`lambs`、`chicks`、`nestlings`、`the hen`。
- 页眉等版面元素（规则 2.0.4，和 `taxon` 是同一条规则）。物种条目开头的标题*要*标。
- 另一个名字内部的修饰成分（`Sparrow-Hawk` 是一个名字，不是 `Sparrow` 加 `Hawk`）。

### 2.3 `locality`：有名字的地理位置

要标：
- 文中任何有名字的真实地点，不管起什么作用：栖息地、分布、采集或观察记录，以及其他提到地点的地方，比如 `Key to the species of the Argentine Republic`。`Hab. Central America?` 标成 `Central America`，备注写 `UNCERTAIN-IN-SOURCE`。
- 地点连同缩小范围的部分算一个片段：`Isle of Luzon, Philippine Islands`。
- 正文中的分布描述：`it breeds in Scotland` 中，片段是 `Scotland`。
- 几个不同的地点分别标：`Cornwall and Devon` 是两个。
- 当专名用的区域名：`the Continent`（片段是 `Continent`）、`Old World`。
- 和人同名的地点，按它在这个位置的角色标：`Lord Lilford` 是 `person`；`the park and pleasure-grounds of Lilford` 是 `locality`。

**一个地点还是几个？** 根据原文的写法判断，不靠去查地理知识。
- 用逗号隔开、后一个是包含前一个的更大区域的地名，算**一个片段**：`Merida, Andes of Bolivia`；`Humeerpore, Bundelkhund, India`；`Coban, Vera Cruz, Central America`。检验方法：逗号可以读成"位于"。
- 用 `and` 或 `or` 连接、用分号隔开，或者作为同类地点并列列举的（`China, North-west India, Afghanistan, Persia`），算**多个提及**。
- 不认识这些地名时：在 `Hab.` 行里，默认顺序是由小到大（Reeve 就是这样写产地的），标成一个片段，备注写 `hierarchy assumed`。过时或可疑的地理关系不改也不查（`Coban, Vera Cruz` 照原样）。

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

只有直接连着地名的自然地貌词或方位词才算地点的一部分：`valley of`、`coast of`、`cliffs of`（`cliffs of Dover`）、`slopes of`、`mouth of`、`banks of`、`interior of`、`North-west`。建筑和庭园不算：`the park and pleasure-grounds of Lilford` 只标 `Lilford`。

不标：
- 没有地名的生境类型：`woods`、`marshes`、`on rocks`。
- 文献引用里的地点（出版地）。
- 属于机构名称一部分的地点：`Zoological Society of London` 是一个 `institution`，不是地点。
- 形容词，比如 `British birds` 里的 `British`；标题或页眉里的地点。标题包括被引用著作的标题：`"Birds of Northamptonshire"`、`"Natural History and Sport in Moray"`、`"Notes from Redcar"` 里的地名都不标。
- 回指某个地点的普通名词：`the island`、`this county`。

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
| `the immigration of Hoodies from the 12th to the 30th of October` | 标 `12th to the 30th of October`，备注 `NO-YEAR` | 一次有日期记录的迁入：带具体的日，就是事件 |
| `arrives in April` | 不标 | 一般物候规律，不是一次事件 |
| `noticed in largest numbers in October and November` | 不标 | 一般情况 |
| `breeds in spring` | 不标 | 一般物候规律 |
| `PFEIFFER, Pro. Zool. Soc., 1846, p. 112` | 不标日期（`PFEIFFER` 标成 `person`） | 出版年份 |
| `published in April 1890` | 不标 | 出版日期 |

要标：
- 按印刷的完整日期表达式标，包括序数后缀和中间的逗号；`1880–85` 或 `12th to the 30th of October` 这样的范围算一个片段。
- 经验法则：和某次观察连在一起的具体的日或年份，表示一次事件。只说一般规律的月份或季节不算。

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

**简化做法（Gloria，2026-11-20）。** 在 `gold/gold_links_gloria_names.csv` 里每个不同的名字填一行，`python src/expand_links.py` 会把你的决定复制到这个名字的每一次出现。只有四列必填：`printed_rank`、`resolution_status`、`accepted_name`（你认定的今天的有效名，例如 `Alauda arvensis`；`partial` 填属名；`unresolved` 留空）、`evidence_source`；其余几列可以留空。不用抄任何编号：GBIF 网站现在显示的是新的分类代码（gbif.org/taxon/BFFT），而评分用的接口仍是旧的数字编号，所以由 `expand_links.py` 用你填的名字在同一个接口里精确查找（同时核对等级），自动填 `accepted_usage_key`；不是精确有效匹配的名字不填，列出来请你再看（`gold/gold_links_gloria_key_lookup.csv`）。种名的查法：先在 Avibase 查这个名字现在对应哪个物种（和 GBIF 无关的独立来源）。**每个名字最多花三分钟左右**；到时还定不了，就填 `ambiguous`（候选写进 notes）或 `unresolved`（查过哪里写进 notes）。这两种都是合法答案，会单独计数。

**关联结果怎么统计。** 只有 `resolved`（也就是在原文印的等级上确定）才算关联正确。对原文印成物种的名字，结果分四个数分别报告：物种级正确、`partial`（只到属或更高）、`ambiguous`、`unresolved`。物种名只匹配到属，绝不计入物种级的成功率。

## 4. 裁定、一致性检查和冻结

**不清楚的行在处理之前不算标准答案。** 评分之前，备注里写了 `UNCLEAR` 的每一行都要填 `adjudication`：
- `adjudicated`：已经做了决定（如果是缺规则，就把规则补进规范，出一个新版本）。和其他行一样评分。
- `ambiguous`：合理的标注人可能有不同标法。不纳入严格评分：模型的预测和它匹配上，不加分也不扣分；漏掉它也不算错。这类行的数量会单独报告。（文字不连续的情况不是 `ambiguous` 行，它记在标注问题表里。）

**两种不确定要分开。** `UNCLEAR` 是*我们*标注人不确定该怎么标、片段到哪里结束；这样的行要等裁定。`UNCERTAIN-IN-SOURCE` 是标注本身没问题，但*作者*对事实有保留（`is reputed to have occurred on Greenland`；`probably from New Granada, but I have no authority`）；这样的行照常评分。

**测试页的工作顺序。** Gloria 先独自标完一页并保存文件（提交一次），之后才看别人对这一页的标签，不管是人还是 AI 助手。之后的对比只是第二意见：它可以提出问题，由它引起的每一处改动都在 `gold/gold_changes_<标注人>.csv` 里记一行。这个助手不应该是被评测的模型；如果是，报告里要写明。（6 页开发集就是这样做的：Gloria 先标，再和 AI 助手对比。）

**标测试页时发现的规则。** 新规则写进规范（出新版本），由它决定的行在 `later_rule` 列里记下这个版本号（裁定时填写，标注人留空）。`guide_version` 只表示标这一行时用的是哪一版规范。它**不**加进提示词：提示词只在开发集上调，因为某一页测试页才有的规则会把测试集的信息泄漏进提示词。分数报告两遍：一遍用全部 gold 行，一遍把规范版本晚于提示词的那些行当作可选。两个方向都包括：按后来的规则标上的行，以及被后来的规则排除的 `excluded` 行。

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
| v0.6 | 2026-11-19 | Gloria 标完 6 页开发集后决定的规则；之前的规则不变。`taxon`：属名的拉丁复数（`Bulimi`、`Achatinæ`）和引用括号里的属名（`(Glandina,)`）要标。`vernacular`：不分大小写；年龄、性别、发育阶段词不标。`locality`：逗号隔开、由小到大的地名算一个片段，并列列举的算多个（按原文写法判断，不查地理）；当专名用的区域名（`Continent`、`Old World`）要标；只有自然地貌词算地点的一部分；被引用著作标题里的地名和普通名词（`the island`）不标。`date`：和一次有记录的迁移连在一起的具体的日算事件（`12th to the 30th of October`，`NO-YEAR`）。第 4 节：区分 `UNCLEAR` 和 `UNCERTAIN-IN-SOURCE`；测试页先独自标完并保存，再做任何对比。开发集 gold：按 Gloria 的决定加了三行（`gold/gold_changes_gloria.csv`）。 |
| v0.7 | 2026-11-19 | Gloria 在第一页测试页（8992328）上的决定，只涉及 `vernacular`：大的类群名要标（`insects`）；只有这本书自己的主题词算泛称；独立成词的名字即使指材料也标（`moss`）；只是连字符复合词一部分的不标（`grass-stalks` 里的 `grass`）。第 4 节：测试页上发现的规则写进规范但不进提示词；分数按是否包含这些行各报告一遍。 |
| v0.8 | 2026-11-19 | Gloria 在测试页 8992379 上的决定：被引用著作标题里的任何内容都不算提及，所有字段都一样（2.0.5；v0.6 只对地名这样规定）。`adjudication` 新增取值 `excluded`，表示这一行考虑过、但不算提及。 |
| v0.9 | 2026-11-19 | Gloria 在测试页 8992489 上发现：专家转录有一处笔误（把扫描图上的 `montifringilla` 写成了 `Fringilla nontifringilla`）。新增可选列 `scan_text` 处理这种情况；`text` 和位置仍按转录文件。已知的笔误列在 `data/transcription_errata.csv`。"什么算提及"的规则没有变化。 |
| v0.10 | 2026-11-20 | Gloria 在测试页 8966802 上的决定：和前一个学名共用属名的单独种加词（`B. rugiferus and Darwinii`）算 `taxon` 提及（2.1）。 |
