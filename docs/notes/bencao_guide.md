# 本草綱目 case: annotation guide v0.1

*v0.1, 2026-11-23: the proposals of the v0 draft adopted by the author ("按你的建议"); the two points
the draft left open (6, 7) take the defaults stated below. No page has been labelled yet. Examples come from
half-leaves 036-1a, 036-2a and 036-2b, which are **not** among the six pilot pages, so nothing here
pre-fills a label on a pilot page.*

## What stays as in the main guide (ANNOTATION_GUIDE v0.10)

- A mention is a character span in the reference text plus a field.
- The reference text is the Kanripo transcription of a `scan_verified` half-leaf, with Kanripo markup
  removed (`data/bencao/kanripo_plain/`): one manuscript column per line, small two-column notes joined
  right column first.
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
   a fixed variant table (宻→密, 𢎞→弘, …), reported with and without folding, like `norm_value` in the
   main scorer. Kanripo gaps (two spaces, e.g. 036-2b `芫  甘遂`, probably 芫花) are filled from the scan
   during verification and logged in an errata file. **Decided as written.**
9. **Book titles inside quotations.** 沈括筆談云本草註引爾雅: 筆談 and 爾雅 cited; 本草註 a generic
   reference. Label generic references? **Decided: no.**

## Linking (later)

Taxon mentions link to a modern taxon through a scholarly identification chosen by the author per
name; the linker under test queries GBIF / Catalogue of Life China by name. Persons and cited works may
link to authority lists (for example DILA or CBDB for persons), out of scope for the pilot.
