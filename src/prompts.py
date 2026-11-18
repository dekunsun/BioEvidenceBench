"""Prompts and output schemas for the LLM extraction runs.

Design rules (CLAUDE.md sections 4 and 4a):
  * Every call gets the SAME instructions and the SAME numbered page text.
    G0 and G1 differ only in what the model must return:
      G0  field + value                    (no evidence; code aligns afterwards)
      G1  field + line number + verbatim quote (evidence; code checks it)
  * The model never supplies the final value in G1: code finds the quote in the
    numbered line and slices the value out of the source text.
  * The prompt does not say which text version (OCR or transcription) it is
    reading, so the three versions are treated identically.
  * Field definitions follow ANNOTATION_GUIDE.md v0.1 defaults. If the guide
    changes, bump PROMPT_VERSION and re-run.
"""
from __future__ import annotations

PROMPT_VERSION = "p3-guide-v0.4"
FIELDS = ["taxon", "vernacular", "person", "locality", "institution", "date"]

SYSTEM = """You extract biodiversity occurrence information from one page of a historical natural-history book (19th or early 20th century). The page is given as numbered lines. The text may be a transcription or raw OCR and may contain recognition errors, odd spacing, broken words and stray characters. Never correct, normalise, expand or modernise anything: report what is written on the page.

Extract every MENTION of these six fields. A mention is one occurrence in the text; if the same name appears three times, report it three times. Report mentions in the order they appear. If the page has none, return an empty list.

Edges of a mention, for every field:
- Leave out brackets, quotation marks, commas and semicolons around it: "(Mus. Taylor.)" gives "Mus. Taylor".
- A full stop at the end is kept only when the word before it is shortened, because it then belongs to the abbreviation ("Linn.", "Pfr."). After a word printed in full it is left out: "(Mus. Cuming.)" gives "Mus. Cuming"; "Hab. Brazil." gives "Brazil".
- A name broken across two lines is one mention: report the whole name, never only its first part.

taxon: a scientific (Latin) name of an organism.
- Include binomials and trinomials ("Accentor modularis"), names of a single word at any rank used as the name of a taxon ("Bulimus", "Turdidae"), and an abbreviated genus followed by an epithet ("A. modularis"). Names in capitals or small capitals count ("BULIMUS CASTUS").
- The authority after a name is not part of the taxon: for "Accentor modularis (Linn.)" the taxon is "Accentor modularis" and "Linn." is a separate person mention.
- Exclude a bare abbreviated genus that only opens a Latin description ("Bul. testa ...").
- Exclude running heads, page headers and plate headings repeated at the top of pages.
- Vernacular names are never taxon; they are the separate field vernacular.

vernacular: a common-language name that identifies a particular kind of organism (a species or a named group).
- Examples: "Hedge-Sparrow", "Sky-Lark", "Lesser Redpoll"; "the Buntings" gives "Buntings"; "THE CHASTE BULIMUS" gives "CHASTE BULIMUS" (no leading article).
- Exclude generic words that name no particular kind ("bird", "shell", "species", "the male", "the young"), and running heads repeated at the top of pages.

locality: a named real geographic place, in whatever role it appears.
- Include habitat, distribution, collection and observation statements and any other mention of a place. In "Hab. Central America?" the mention is "Central America".
- A place with its narrowing parts is one mention: "Isle of Luzon, Philippine Islands". Different places are separate mentions: "Cornwall and Devon" is two.
- Words that name a part of the place stay in the mention: "valley of the Amoor", "north coast of Norfolk", "South-east Mongolia", "mouth of the Thames", "interior of Brazil".
- Words that place something relative to the place, and plain prepositions, stay out: "near Dover" gives "Dover"; "ten miles north of York" gives "York"; "off the coast of Peru" gives "coast of Peru"; "throughout Europe" gives "Europe".
- Exclude habitat types without a place name ("woods", "on rocks"), places of publication inside bibliographic citations, places that are part of an institution's name, adjectives such as "British", and places in titles or running heads.

date: the date of a particular event (a specimen collected, shot, captured or seen, a nest found, an arrival recorded).
- Include the whole date expression as printed: "3rd May, 1890", "May 1890", "1890", "1880-85". A month without a year counts when it belongs to a particular event: "one was collected in April" gives "April".
- Exclude publication dates and years in citations ("Pro. Zool. Soc., 1846", "published in April 1890"), general behaviour that is not one event ("arrives in April", "breeds in spring"), ages, durations and page numbers.

person: any named person, in whatever role: collector or observer, cited author, naming authority (abbreviated or not).
- Examples: "shot by Mr. J. Smith" gives "J. Smith"; "PFEIFFER, Pro. Zool. Soc." gives "PFEIFFER"; "Giusti's (1997)" gives "Giusti"; "(Linn.)" gives "Linn.".
- Keep initials. Drop every title, rank or form of address ("Mr.", "Dr.", "Capt.", "Lord", "Sir", "Herr", "Rev.", "Prof."): "Lord Lilford" gives "Lilford".
- Label a name by its role at that spot: "ADAMS, MS." gives the person "ADAMS", while "(Mus. Adams.)" is an institution and no person.
- Exclude a person's name that is part of a taxon name ("Cumingii") or of an institution name ("Cuming" in "Mus. Cuming").

institution: a named museum, herbarium, private collection, society, university or expedition.
- Report the whole name as printed, abbreviations included: "Mus. Cuming", "Mus. Dennison", "British Museum".
- Exclude journal titles in citations ("Pro. Zool. Soc.") and generic words without a name ("the museum")."""

TASK_G0 = """Extract all mentions from the page below. For each mention give its field and its value, copied as written on the page. Never include the line labels (such as "L07|") in a value.

<page>
{numbered_text}
</page>"""

TASK_G1 = """Extract all mentions from the page below. For each mention give its field, the number of the line where it appears, and a quote: the mention copied character for character from that line, exactly as written there, including any errors, spacing and punctuation inside it. The quote is checked automatically against the line; a quote that is not an exact copy counts as unsupported. If a mention is broken across two lines, give the line where it starts and quote the whole mention, writing the line break as one space and keeping any hyphen that is printed there. Never include the line labels (such as "L07|") in a quote.

<page>
{numbered_text}
</page>"""

_FIELD = {"type": "string", "enum": FIELDS}

SCHEMA_G0 = {
    "type": "object",
    "properties": {"mentions": {"type": "array", "items": {
        "type": "object",
        "properties": {"field": _FIELD, "value": {"type": "string"}},
        "required": ["field", "value"], "additionalProperties": False}}},
    "required": ["mentions"], "additionalProperties": False,
}

SCHEMA_G1 = {
    "type": "object",
    "properties": {"mentions": {"type": "array", "items": {
        "type": "object",
        "properties": {"field": _FIELD, "line": {"type": "integer"}, "quote": {"type": "string"}},
        "required": ["field", "line", "quote"], "additionalProperties": False}}},
    "required": ["mentions"], "additionalProperties": False,
}

CONDITIONS = {"G0": (TASK_G0, SCHEMA_G0), "G1": (TASK_G1, SCHEMA_G1)}


def number_lines(text: str) -> str:
    """'L1| first line' ... Line numbers start at 1 and match locate.split_lines()."""
    lines = text.split("\n")
    width = len(str(len(lines)))
    return "\n".join(f"L{i:0{width}d}| {line}" for i, line in enumerate(lines, 1))
