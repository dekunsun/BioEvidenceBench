# Prompt for the README header image (fig00), for an image-generation tool

Use with the same tool that made `docs/assets/overview/cover_illustration.png`. The scan must stay the
real scan: the tool draws an empty page frame, and the real crop `docs/assets/overview/fig00_scan_crop.png`
(BHL page 8992647, CC BY 3.0) is pasted into it afterwards. Check every text string in the result letter
by letter against the list at the end; image tools often misspell.

## English version

Create a clean, elegant infographic, 16:9, in the same visual style as a scientific-heritage illustration:
warm cream background (#fffdf8), muted teal (#1f8683) as the main colour, soft brick red (#b23b3b) for
errors, navy (#1b2a3a) for headings, thin rounded cards with light grey borders, plenty of white space,
a few delicate botanical line-drawn leaves in one corner. Sans-serif headings, monospaced type for the data
values. Very little text.

Layout, top to bottom:

1. Title, top left, large serif: "One record, five steps". Small grey subtitle under it:
   "Butler, Birds of Great Britain and Ireland (1907) · BHL page 8992647".

2. Left half of the upper area: an EMPTY rectangle shaped like an open book page, ratio 3.8 : 1 (wide),
   with a soft shadow and a thin border. Leave it completely blank inside (a real scan will be pasted in).
   From the lower edge of this page, a smooth curved teal arrow sweeps down into step 1 below.

3. Right half of the upper area: a white rounded card titled "Final record", a small table of four rows,
   each row with a small teal line icon on the left, a grey label and a bold teal monospaced value:
   - leaf icon · "accepted taxon" · "Motacilla flava"
   - # icon · "GBIF key" · "9701857"
   - map-pin icon · "locality" · "Rottingdean, Sussex"
   - calendar icon · "date" · "April 20th, 1898"
   A curved teal arrow comes up into this card from step 5.

4. Bottom: five equal rounded cards in a row, joined by small teal arrows. Each card has a coloured strip
   on top (red for steps 1 and 4, teal for 2, 3, 5), a round icon badge, a bold step name, one value in a
   tinted pill (monospaced), one short grey caption, and a small ✓ or ✗ in the top-right corner:
   - 1 "OCR" · scanner-bracket icon · red pill "April 2otli, 1898" · caption "date misread" · ✗
   - 2 "Extract" · tag icon · teal pill "Motacilla beema" · caption "copied as printed" · ✓
   - 3 "Evidence" · quotation-mark icon · teal pill "line 35" · caption "quote found in text" · ✓
   - 4 "Link" · three-node network icon · red pill "Motacilla" · caption "GBIF: genus only" · ✗
   - 5 "Review" · checkbox icon · teal pill "Motacilla flava" · caption "curator decides" · ✓

5. Very small grey italic line at the bottom: "Scan: Biodiversity Heritage Library via IMPACT ground truth
   (finebooks/bhl-impact-gt), CC BY 3.0."

Do not draw any bird, shell or book page with invented text; do not add any other words, numbers or
species names; spell every value exactly as given (note "2otli" with a lowercase o and l, not "20th").

## 中文版（同样的版式，标签换成中文）

制作一张简洁、有设计感的信息图，16:9，风格与科学古籍插画一致：暖米白底色（#fffdf8），主色为柔和的
青绿色（#1f8683），错误用砖红色（#b23b3b），标题用深蓝（#1b2a3a）；细边圆角卡片，大量留白，一角有几片
淡雅的线描树叶。标题用无衬线字体，数据值用等宽字体。文字尽量少。

版式从上到下：

1. 左上大标题：「一条记录，五个环节」。下面一行灰色小字：
   「Butler《Birds of Great Britain and Ireland》（1907）· BHL 第 8992647 页」。

2. 上半部分左侧：一个**空白**的书页形状矩形，宽高比 3.8 : 1，带柔和阴影和细边框，里面完全留空（之后
   贴入真实扫描图）。从书页下边缘画一条青绿色弧形箭头，流向下方第 1 步。

3. 上半部分右侧：白色圆角卡片，标题「最终记录」，四行小表格，每行左边一个青绿色线条小图标、灰色标签、
   加粗青绿色等宽字体的值：
   - 叶子图标 ·「有效学名」·「Motacilla flava」
   - # 图标 ·「GBIF 编号」·「9701857」
   - 定位针图标 ·「地点」·「Rottingdean, Sussex」
   - 日历图标 ·「日期」·「April 20th, 1898」
   从第 5 步画一条青绿色弧形箭头向上指进这张卡片。

4. 下方：五张等宽圆角卡片排成一行，之间用青绿色小箭头连接。每张卡片顶部一条色带（第 1、4 步红色，
   第 2、3、5 步青绿色），一个圆形图标徽章，加粗步骤名，一个浅色底胶囊里的值（等宽字体），一行灰色
   短说明，右上角一个小 ✓ 或 ✗：
   - 1「OCR」· 扫描框图标 · 红色胶囊「April 2otli, 1898」· 说明「日期读错」· ✗
   - 2「抽取」· 标签图标 · 青绿胶囊「Motacilla beema」· 说明「按原文抽出」· ✓
   - 3「证据」· 引号图标 · 青绿胶囊「第 35 行」· 说明「引文在原文中找到」· ✓
   - 4「关联」· 三节点网络图标 · 红色胶囊「Motacilla」· 说明「GBIF 只到属」· ✗
   - 5「审核」· 勾选框图标 · 青绿胶囊「Motacilla flava」· 说明「人工核定」· ✓

5. 最底部一行很小的灰色斜体：「扫描图：Biodiversity Heritage Library，经 IMPACT 专家转录集
   （finebooks/bhl-impact-gt），CC BY 3.0。」

不要画鸟、贝壳或带编造文字的书页；不要加任何其他文字、数字或物种名；每个值严格按上面拼写
（注意「2otli」是小写 o 和 l，不是「20th」）。

## Strings to check in the result (all copied from the project files)

| Where | Exact text | Source |
| --- | --- | --- |
| step 1 | `April 2otli, 1898` | `data/sample/legacy/8992647.txt` |
| step 2 | `Motacilla beema` | `results/20261119-2052_claude-opus-5-5_test_batch/test_mentions.csv` (legacy, G1) |
| step 3 | line `35` | same file, `line` column |
| step 4 | `Motacilla` (genus only) | `results/linking_test/link_outcomes.csv` (`gbif_name` Motacilla Linnaeus, 1758; HIGHERRANK) |
| step 5, record | `Motacilla flava`, `9701857` | `gold/gold_links_gloria.csv` |
| record | `Rottingdean, Sussex` | `data/sample/legacy/8992647.txt` |
| record | `April 20th, 1898` | `gold/gold_mentions_gloria_test.csv`, `scan_text` |
| scan to paste | `docs/assets/overview/fig00_scan_crop.png` | bhl-impact-gt, CC BY 3.0 |
