"""Build the labelling pack for the second labeller (agreement check, ANNOTATION_GUIDE section 4).

    python src/make_labeller_pack.py OUT_DIR

The pack holds only what an independent labeller needs: the guide, the five page texts,
a page list with scan links, and empty templates. It holds nothing of Gloria's labels and no
model output.

The guide in the pack is a **labeller copy** of the current guide. The rules are the same,
word for word. Two things are changed, because they come from the very pages the second
labeller is asked to label and would tell her the answer there:
  - two worked examples taken from those pages are replaced by invented examples
    (`"Foreign Finches in Captivity"` from 8992379, `B. rugiferus and Darwinii` from 8966802);
  - the changelog is left out (it says on which test page each later rule was decided).
Every replacement must match exactly once, so a later edit of the guide makes this script stop
instead of silently shipping a copy with the original example in it.
"""
from __future__ import annotations

import csv
import hashlib
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGES = [("Butler", 8992379), ("Butler", 8992643), ("Reeve", 8966802), ("Reeve", 8967281), ("Reeve", 8967290)]
LABELLER = "friend"

# (original, replacement) pairs; each original must occur exactly once in the guide.
SWAPS = [
    ('`"Foreign Finches in Captivity", p. 249` gives no `vernacular`;',
     '`"The Thrushes of the Hill Country", p. 31` gives no `vernacular` (invented example);'),
    ('`"Foreign Finches in Captivity", p. 249` 不标 `vernacular`；',
     '`"The Thrushes of the Hill Country", p. 31` 不标 `vernacular`（编造的例子）；'),
    ("  `the B. rugiferus and Darwinii` gives two `taxon` mentions, `B. rugiferus` and `Darwinii`; notes",
     "  `the A. pallida and Browni` (invented example) gives two `taxon` mentions, `A. pallida` and `Browni`; notes"),
    ("`the B. rugiferus and Darwinii` 标成两个 `taxon`，`B. rugiferus` 和 `Darwinii`，",
     "`the A. pallida and Browni`（编造的例子）标成两个 `taxon`，`A. pallida` 和 `Browni`，"),
]
COPY_NOTE_EN = ("**Labeller copy of guide v0.10.** The rules are those of v0.10, unchanged. Two worked "
                "examples were replaced by invented ones and the changelog is left out, so that nothing "
                "in this copy comes from the pages you are asked to label.\n")
COPY_NOTE_ZH = ("**规范 v0.10 标注员版。** 规则就是 v0.10 的规则，一字未改。有两个例子换成了编造的例子，"
                "变更记录也去掉了，这样这份规范里没有任何内容来自你要标的页面。\n")


def labeller_guide(text: str) -> str:
    for old, new in SWAPS:
        if text.count(old) != 1:
            sys.exit(f"Guide changed: expected exactly one {old!r}; update SWAPS before building the pack.")
        text = text.replace(old, new)
    # header paragraphs (they point to the changelog) -> one note each
    text, n_en = re.subn(r"\*\*Version v0\.10, .*?records the guide version of every row\.\n",
                         COPY_NOTE_EN, text, count=1, flags=re.S)
    text, n_zh = re.subn(r"\*\*版本 v0\.10，.*?\n", COPY_NOTE_ZH, text, count=1)
    # changelog sections: from the heading to the next horizontal rule or the end
    text, n_cl_en = re.subn(r"## Changelog\n.*?(?=\n---\n)", "", text, count=1, flags=re.S)
    text, n_cl_zh = re.subn(r"## 变更记录\n.*\Z", "", text, count=1, flags=re.S)
    if (n_en, n_zh, n_cl_en, n_cl_zh) != (1, 1, 1, 1):
        sys.exit(f"Guide layout changed (header/changelog matches {n_en, n_zh, n_cl_en, n_cl_zh}).")
    for leak in ("Foreign Finches", "rugiferus", "Darwinii", "8992379", "8992643", "8966802", "8967281", "8967290"):
        if leak in text:
            sys.exit(f"Labeller copy still contains {leak!r}.")
    return text.rstrip() + "\n"


def main(out: Path) -> None:
    if out.exists():
        shutil.rmtree(out)
    (out / "页面").mkdir(parents=True)
    (out / "表格").mkdir()
    guide = labeller_guide((ROOT / "ANNOTATION_GUIDE.md").read_text(encoding="utf-8"))
    (out / "ANNOTATION_GUIDE_标注员版_v0.10.md").write_text(guide, encoding="utf-8")
    rows = []
    for i, (book, pid) in enumerate(PAGES, 1):
        src = ROOT / "data" / "sample" / "expert_view" / f"{pid}.txt"
        name = f"{i:02d}_{book}_{pid}.txt"
        shutil.copy(src, out / "页面" / name)
        plain = (ROOT / "data" / "sample" / "expert" / f"{pid}.txt").read_text(encoding="utf-8")
        rows.append([i, book, pid, f"页面/{name}", len(plain), plain.count("\n") + 1,
                     f"https://www.biodiversitylibrary.org/page/{pid}", ""])
    with open(out / "页面清单.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["顺序", "书", "page_id", "文件", "字符数", "行数", "扫描图", "标完了吗"])
        w.writerows(rows)
    for tpl, name in (("gold_mentions_TEMPLATE.csv", f"gold_mentions_{LABELLER}.csv"),
                      ("annotation_issues_TEMPLATE.csv", f"annotation_issues_{LABELLER}.csv")):
        shutil.copy(ROOT / "gold" / tpl, out / "表格" / name)
    shutil.copy(ROOT / "gold" / "LABELLER_README_friend_zh.md", out / "先看这里.md")
    shutil.copy(ROOT / "data" / "sample" / "ATTRIBUTION.md", out / "ATTRIBUTION.md")
    digest = hashlib.sha256(guide.encode("utf-8")).hexdigest()
    print(f"pack written to {out}\nlabeller guide SHA-256 {digest}")


if __name__ == "__main__":
    main(Path(sys.argv[1]))
