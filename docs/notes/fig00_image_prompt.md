# Prompt for the README header image (fig00)

Short version (the author, 2026-11-24: describe the process, not the styling). Two real images are pasted
into the result afterwards, so the tool must leave room for them and must not draw them:

- `docs/assets/overview/reeve_plate17_fig102.png`: the shell *Bulimus chilensis*, figure 102 of Reeve,
  *Conchologia iconica* vol. 5 (1849), plate XVII (Internet Archive `conchologiaiconi05reev`, image n77;
  public domain by age).
- `docs/assets/overview/fig00_scan_crop.png`: the printed page with the values boxed (Butler 1907, BHL page
  8992647; bhl-impact-gt, CC BY 3.0).

Check the four data values in the result letter by letter; image tools often misspell names.

## English

An elegant, uncluttered infographic in the style of a natural-history book illustration (cream paper,
muted teal, a touch of red for errors, botanical line drawings as decoration). It shows how one entry in a
historical book becomes a checked database record, in five steps from left to right:

1. **OCR**: the printed page is turned into text, and the date comes out misread.
2. **Extract**: the AI picks out the species name, the place and the date, copying them as printed.
3. **Evidence**: every value is tied to the exact line of the page it came from.
4. **Link**: the name is looked up in a biodiversity database; the lookup finds only the genus.
5. **Review**: a curator checks the page and settles the record.

On the left, leave an empty rounded frame for a real page scan, and next to it an empty frame for a real
shell drawing (do not draw either). On the right, end with a small record card holding four values:
*Motacilla flava* · GBIF 9701857 · Rottingdean, Sussex · April 20th, 1898.
Mark steps 1 and 4 with a small red cross and the others with a small teal tick. Keep text to the step
names, a few words under each, and the record card. Title: "One record, five steps".

## 中文

一张简洁、有设计感的信息图，风格像自然史古籍插画（米色纸张、柔和的青绿色、少量红色表示错误、线描植物
做装饰）。展示古书里的一条记载，怎样经过五个环节变成一条可核查的数据库记录，从左到右：

1. **OCR**：书页变成文字，日期被读错。
2. **抽取**：AI 按原文抽出学名、地点和日期。
3. **证据**：每个值都对应到书页上的具体哪一行。
4. **关联**：拿学名去生物多样性数据库查，只查到属。
5. **审核**：人工对照书页，确定最终记录。

左边留一个空白圆角框放真实书页扫描，旁边再留一个空白框放真实的贝壳插图（两者都不要画）。右边以一张
小记录卡收尾，写四个值：*Motacilla flava* · GBIF 9701857 · Rottingdean, Sussex · April 20th, 1898。
第 1、4 步标小红叉，其余标小青绿色勾。文字只保留步骤名、每步下面几个字和记录卡。标题：「一条记录，
五个环节」。

## Values to check (from the project files)

| Value | Source |
| --- | --- |
| *Motacilla flava*, 9701857 | `gold/gold_links_gloria.csv` |
| Rottingdean, Sussex | `data/sample/legacy/8992647.txt` |
| April 20th, 1898 | `gold/gold_mentions_gloria_test.csv` (`scan_text`) |
| misread date `April 2otli, 1898` (if shown) | `data/sample/legacy/8992647.txt` |
