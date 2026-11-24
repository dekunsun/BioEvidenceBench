# 本草綱目 case: annotation guide v0.3

*v0.3, 2026-11-24: rules 11–14 from the first labelled page (036-1b), adopted by the author on Claude's recommendation without her own research ("按照你的建议来，我没有相应的知识也没有research"); to be revisited with a domain expert. v0.2, 2026-11-23: rule 10 (historical forms and restoration) added on the author's decisions. v0.1, 2026-11-23: the proposals of the v0 draft adopted by the author ("按你的建议"); the two points
the draft left open (6, 7) take the defaults stated below. No page has been labelled yet. Examples come from
half-leaves 036-1a, 036-2a and 036-2b, which are **not** among the six pilot pages, so nothing here
pre-fills a label on a pilot page.*

## What stays as in the main guide (ANNOTATION_GUIDE v0.10)

- A mention is a character span in the reference text plus a field.
- The reference text is the Kanripo transcription of a `scan_verified` half-leaf, with Kanripo markup
  removed and the author's scan corrections applied (`data/bencao/verified_plain/`): one manuscript column
  per line, small two-column notes joined right column first. Labellers write `line` and `text`; a script
  fills `start`/`end` (first pilot page: `gold/labelling_bencao_036-1b.xlsx`).
- Running heads (欽定四庫全書, the volume title) are not mentions.
- Non-contiguous text goes to an issues file, not into gold.

## Proposed fields

| Field | What it covers | Example (from 036-1a / 2a / 2b) |
| --- | --- | --- |
| `taxon` | the name of a drug or organism: entry headings and names used for a substance in the text | 甘草 (heading); 槐 in 甘草枝葉悉如槐? |
| `person` | a named author or person cited | 𢎞景, 甄權, 沈括, 郭璞, 雷斆, 寇宗奭, 王好古 |
| `locality` | a place where something grows, is produced or is found | 河東, 安南 |
| `cited_work` (new) | a book cited as a source | 別録, 爾雅, 筆談, 衍義, 霏雪録 |
| `substance` (new, scored separately, not in the primary F1) | minerals, water, earth and other non-organic drugs | (金石部; rare in 草部) |
| `date`, `institution` | dropped: harvest months (二月八月除日采根) are practice, not dated events; institutions do not occur | — |

## Decisions (adopted 2026-11-23)

1. **Alternative names in 釋名.** 宻甘, 宻草, 美草, 蕗草, 靈通 are other names of 甘草; 國老 is an honorific
   ("national elder"). **Decided: every name listed under 釋名 is `taxon`, with `qualifier = alias`.**
2. **Source tags in small notes.** `宻甘(别/録)`: the 別録 attached to each alias says where the name comes
   from. **Decided: each is a `cited_work`; they are the evidence trail.**
3. **Short names of authors.** 𢎞景 for 陶弘景, 權 for 甄權, 頌 for 蘇頌, 時珍 for 李時珍, 寇氏. **Decided:
   label the short form as printed; resolving it to the full name is the linking step, scored
   separately, as abbreviated genera were for Butler.**
4. **Place phrases.** 河西川谷, 積沙山, 上郡, 汶山諸道: is 川谷 (river valley) part of the place? Is 河東蒲坂縣
   one span or two? **Decided: as in the main guide, a narrow-to-wide chain is one span; generic words such as
   川谷, 山谷 count only as part of a named place.**
5. **Comparison plants.** 葉如槐葉 ("leaves like the pagoda tree's"): is 槐 a `taxon` mention?
   **Decided: yes; it names an organism.**
6. **Ingredients in 附方.** Every drug in a prescription is a substance name. Label them all, or only
   the entry's own drug? **Decided: all of them. Organisms and products made from them (乾漆 from the
   lacquer tree) are `taxon`; minerals are `substance` (point 7).**
7. **Minerals and non-organisms.** 本草 covers minerals, water, fire and earth. A `taxon` field implies
   organisms. **Decided: minerals and other non-organic drugs are a separate field `substance`, scored
   separately like `vernacular` in the main guide.** (Matters little for 草部.)
8. **Variant and missing characters.** Spans follow Kanripo's characters (宻, 𢎞, 䖅). Value matching folds
   the fixed table `data/bencao/variant_table.csv` (宻→密, 𢎞→弘, …) only in the auxiliary metric; the
   primary scores compare forms as written (v0.2, rule 10). Kanripo gaps (two spaces, e.g. 036-2b `芫  甘遂`, probably 芫花) are filled from the scan
   during verification and logged in an errata file. **Decided as written.**
9. **Book titles inside quotations.** 沈括筆談云本草註引爾雅: 筆談 and 爾雅 cited; 本草註 a generic
   reference. Label generic references? **Decided: no.**

10. **Historical forms: taboo avoidance and restoration (v0.2, the author's decisions 2026-11-23).**
    The Siku copy avoids imperial names: 弘 (乾隆 弘曆) is written 𢎞 with the last stroke missing
    (卷十二上 21 times, 下 31 times, never 弘); 玄 (康熙 玄燁) is written 𤣥 (𤣥參 17 times in 卷十二下) or,
    in places, replaced by another character (元參, once in 卷十二下). Rules:
    - **As written.** Transcription and gold `text` keep what the scan shows, characters and forms
      (陶𢎞景, 𤣥參, 元參). Nothing in the source text is changed.
    - **Two different columns, never mixed.** `scan_text` keeps its meaning from the main guide: the
      scan's reading where the *transcription* is wrong (a transcription error). Historical forms go in
      three new gold columns:
      | Column | Content | Example |
      | --- | --- | --- |
      | `restored_form` | the standard form of the value, confirmed by the author | 陶弘景; 玄參; 枹罕 |
      | `normalization_type` | `glyph_variant` (same character, another form: 䍐→罕), `taboo_missing_stroke` (𢎞→弘, 𤣥→玄), `taboo_substitution` (another character put in by the copyist: 元→玄), `interchangeable_usage` (different characters for the same word: 暴/曝) | `taboo_missing_stroke` |
      | `restoration_evidence` | why: the rule, a parallel passage or a reference | 避乾隆諱，弘缺末筆; 同條標題作𤣥參 |
      Empty when the value is already standard. Gold file: `gold/gold_mentions_bencao_TEMPLATE.csv`.
    - **Scoring.** The primary scores compare forms as written, without folding. An auxiliary OCR
      metric folds the fixed table `data/bencao/variant_table.csv` (glyph variants and missing-stroke
      taboo forms only). Contextual substitutions (元/玄) are never folded; they get their own metric:
      at each gold mention with `normalization_type = taboo_substitution`, did the output keep the form
      as written, and does a separate restoration step reach `restored_form`.
    - **Linking** uses the confirmed `restored_form` (𤣥參 is looked up as 玄參), keeping `text` and
      `restoration_evidence` on the same row.
    - **OCR.** 𢎞 read as 弘 is a glyph fold in the auxiliary metric, not an error there; 元 read as 玄
      (or the reverse) is never folded.

11. **Book plus section (v0.3).** A cited book followed directly by a section of it, written without a
    break, is one `cited_work` span: `詩唐風` (《詩·唐風》, the Tang airs of the Book of Songs). Book and
    section are separated at the linking step, not in the span.
12. **Regional drug names (v0.3).** A place name joined to a drug name as one name for a regional kind of
    the drug is one `taxon` span: `枹䍐草` (licorice from 枹䍐). The place inside it is not labelled again;
    a separate mention of the place (`枹䍐乃西羌地名`) is a `locality` as usual.
13. **Peoples as territory (v0.3).** The name of a people used for the land they live in is a `locality`
    (`西羌地名`, "a place name in the land of the Western Qiang"). Used for the people themselves it is not
    labelled; `person` is for named individuals only.
14. **Names split by a line break.** As in the main guide (2.0.3): one span across the break, e.g. `上` at
    the end of one manuscript column and `郡` at the start of the next form one `locality` `上郡`.
    Expert questions that are about facts, not rules (is `蜀漢中` one place or two; is `大苦` a name of the
    plant in `䖅大苦`), stay `expert_pending` until a domain expert answers.

## Linking (later)

Taxon mentions link to a modern taxon through a scholarly identification chosen by the author per
name; the linker under test queries GBIF / Catalogue of Life China by name. Persons and cited works may
link to authority lists (for example DILA or CBDB for persons), out of scope for the pilot.
