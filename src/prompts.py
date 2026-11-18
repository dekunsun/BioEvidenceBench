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

PROMPT_VERSION = "p2-guide-v0.2"
FIELDS = ["taxon", "person", "locality", "institution", "date"]

SYSTEM = """You extract biodiversity occurrence information from one page of a historical natural-history book (19th or early 20th century). The page is given as numbered lines. The text may be a transcription or raw OCR and may contain recognition errors, odd spacing, broken words and stray characters. Never correct, normalise, expand or modernise anything: report what is written on the page.

Extract every MENTION of these five fields. A mention is one occurrence in the text; if the same name appears three times, report it three times. Report mentions in the order they appear. If the page has none, return an empty list.

taxon: a scientific (Latin) name of an organism.
- Include binomials and trinomials ("Accentor modularis"), names of a single word at any rank used as the name of a taxon ("Bulimus", "Turdidae"), and an abbreviated genus followed by an epithet ("A. modularis"). Names in capitals or small capitals count ("BULIMUS CASTUS").
- The authority after a name is not part of the taxon: for "Accentor modularis (Linn.)" the taxon is "Accentor modularis" and "Linn." is a separate person mention.
- Exclude a bare abbreviated genus that only opens a Latin description ("Bul. testa ...").
- Exclude running heads, page headers and plate headings repeated at the top of pages.
- Exclude vernacular (English) names such as "Hedge-Sparrow" or "THE CHASTE BULIMUS".

locality: a named real geographic place, in whatever role it appears.
- Include habitat, distribution, collection and observation statements and any other mention of a place. In "Hab. Central America?" the mention is "Central America".
- A place with its narrowing parts is one mention: "Isle of Luzon, Philippine Islands"; "north coast of Norfolk". Different places are separate mentions: "Cornwall and Devon" is two.
- Exclude a leading preposition or relative word: in "near Dover" the mention is "Dover".
- Exclude habitat types without a place name ("woods", "on rocks"), places of publication inside bibliographic citations, places that are part of an institution's name, adjectives such as "British", and places in titles or running heads.

date: when an occurrence happened (collected, observed, shot, nested, arrived).
- Include the whole date expression as printed: "3rd May, 1890", "May 1890", "1890", "1880-85".
- Exclude publication years in citations ("Pro. Zool. Soc., 1846"), seasons or months without a year that only describe general behaviour ("in spring", "arrives in April"), ages, durations and page numbers.

person: any named person, in whatever role: collector or observer, cited author, naming authority (abbreviated or not).
- Examples: "shot by Mr. J. Smith" gives "J. Smith"; "PFEIFFER, Pro. Zool. Soc." gives "PFEIFFER"; "Giusti's (1997)" gives "Giusti"; "(Linn.)" gives "Linn.".
- Keep initials, drop honorifics ("Mr.", "Dr.", "Capt.").
- Exclude a person's name that is part of a taxon name ("Cumingii") or of an institution name ("Cuming" in "Mus. Cuming").

institution: a named museum, herbarium, private collection, society, university or expedition.
- Report the whole name as printed, abbreviations included: "Mus. Cuming", "Mus. Dennison", "British Museum".
- Exclude journal titles in citations ("Pro. Zool. Soc.") and generic words without a name ("the museum")."""

TASK_G0 = """Extract all mentions from the page below. For each mention give its field and its value.

<page>
{numbered_text}
</page>"""

TASK_G1 = """Extract all mentions from the page below. For each mention give its field, the number of the line where it appears, and a quote: the mention copied character for character from that line, exactly as written there, including any errors, spacing and punctuation inside it. The quote is checked automatically against the line; a quote that is not an exact copy counts as unsupported. If a mention is broken across two lines, give the first line and quote only the part on that line.

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
