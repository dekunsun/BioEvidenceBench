# Attribution and licence

The files in `expert/` and `expert_view/` are expert transcriptions of 22 pages from:

- Butler, A. G. (1907). *Birds of Great Britain and Ireland*, vol. 2. BHL item 35947.
- Reeve, L. A. (1849). *Conchologia iconica*, vol. 5. BHL item 35904.

They come from the **IMPACT-BHL ground truth**, produced by the IMPACT Centre of Competence and
BHL-Europe (2011–2012), <https://github.com/impactcentre/groundtruth-bhl>, as redistributed by
FineBooks in [`finebooks/bhl-impact-gt`](https://huggingface.co/datasets/finebooks/bhl-impact-gt).

Licence: **CC-BY 3.0**, <https://creativecommons.org/licenses/by/3.0/>.
Attribution: IMPACT / Biodiversity Heritage Library.

The text is unchanged from the dataset's `text` field (checked by SHA-256 in `manifest.csv`).
The `expert_view/` files add only a line-offset prefix for labelling. Page scans:
<https://www.biodiversitylibrary.org/page/{PageID}>. Both books are public domain
(`NOT_IN_COPYRIGHT` in the BHL item table).
