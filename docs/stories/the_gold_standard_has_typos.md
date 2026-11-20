# 金标准也有错别字：21 个 OCR 都读对了，"标准答案"却错了

*在一份被当作 OCR 标准答案的专家转录里，我找到两处错字。几乎所有现代 OCR 都读对了，却都要因此被扣分。*

[English version below](#the-gold-standard-has-typos-21-ocr-models-got-it-right-and-the-answer-key-was-wrong)

## 一个对不上的鸟名

BioEvidenceBench 用 FineBooks 发布的 IMPACT 专家转录（`finebooks/bhl-impact-gt`）当"标准文本"：同一页书有三个版本（BHL 旧 OCR、现代 OCR、专家转录），专家转录被当作最接近原书的那一版。我在它上面标注实体，再用它去衡量 OCR 和 AI 抽取的好坏。

2026 年 11 月 19 日，我对着扫描图标注测试页 [8992489](https://www.biodiversitylibrary.org/page/8992489)（Butler 1907，The Brambling，燕雀）。专家转录里，这一节的学名写的是：

`Fringilla nontifringilla, LINN.`

扫描图上印的是 **montifringilla**。燕雀的学名是 *Fringilla montifringilla*（"山上的 fringilla"），`nontifringilla` 不是任何鸟的名字，是转录时把 m 打成了 n。

同一天，在测试页 [8992647](https://www.biodiversitylibrary.org/page/8992647) 又找到一处：转录写 `April 20th, I898`，扫描图是 **1898**，数字 1 被打成了大写字母 I。

## 21 个 OCR 都读对了

FineBooks 公开了 20 多个 OCR 模型在这些页上的输出。我把它们全部拿来对照：

| 文本版本 | 第 8992489 页的学名 | 第 8992647 页的年份 |
|---|---|---|
| 专家转录（"标准答案"） | `nontifringilla` ✗ | `I898` ✗ |
| BHL 旧 OCR | `Frinoii/d iiii>iitijriii<^illii` ✗ | `2otli, 1898`（年份对，日期错） |
| 22 个现代 OCR | 21 个读作 `montifringilla` ✓ | 21 个读作 `1898` ✓ |

也就是说，在这两个位置，几乎所有现代 OCR 都比"标准答案"更接近原书。如果按专家转录计算字符错误率，它们每一个都要在这里被扣分。读对的反而算错。

## 我们怎么处理

错字不能悄悄改掉：金标准里每个提及的位置（字符偏移）都是按专家转录算的，改了文本，所有位置都会错，也没有人能复现。也不能假装没看到：用错的学名去关联 GBIF，必然失败。

于是 ANNOTATION_GUIDE 升到 v0.9，规则是：

- 金标准的 `text` 和位置**继续跟随专家转录**，保持可复现；
- 新增一列 `scan_text`，记录**扫描图上的真实读法**（`Fringilla montifringilla`、`April 20th, 1898`）；
- 评分时两种读法都算对，学名关联用 `scan_text`；
- 已知的错字列在 [`data/transcription_errata.csv`](../../data/transcription_errata.csv)，写明谁发现、何时、怎么确认的。

## 一个意外的旁证

后来我们做了一个探索性实验：让 LLM 在引用原文的同时，给出一个"修正后的读法"（G2 条件）。在专家转录上，它只改了 4 个值，其中 3 个正是转录自己的错误：`nontifringilla`、`I898`，和一个被断开的词；另一个是连字（æ）的写法。

这说明两件事：一是"修复"有时修的是标准答案本身；二是如果只看 F1，模型在这里"改对了"反而会被记成错误。必须有人对着扫描图看过，才分得清。

## 学到的

- **"Ground truth" 也是人做的，会有错。** 专家转录是非常好的资源，但不是原书。原书是扫描图。
- **发现错误时，记录它，而不是悄悄改掉。** 保留原文和位置，另起一列写真实读法，列一份勘误表。
- **当很多独立系统一致地"错"在同一个地方，先怀疑答案。** 21 个 OCR 都读 `montifringilla`，这本身就是一个信号。
- **对 OCR 评测的影响**：如果排行榜的标准文本有错，所有模型在那里都被等量扣分，排名不变，但绝对分数被低估；如果某个模型恰好"复制"了标准文本的错误，它反而会被高估。这只是两处错字，影响很小，但同样的检查值得在更大的标准集上做。

我们把这两处错字记录在仓库里，也希望能反馈给 FineBooks 和 IMPACT 数据集的维护者。

---

# The Gold Standard Has Typos: 21 OCR Models Got It Right, and the Answer Key Was Wrong

*In an expert transcription used as the OCR answer key, I found two typos. Almost every modern OCR model read those spots correctly, and would be marked down for it.*

## A bird name that did not fit

BioEvidenceBench uses the IMPACT expert transcriptions published by FineBooks (`finebooks/bhl-impact-gt`) as its reference text. Each page exists in three versions (BHL's legacy OCR, a modern OCR, the expert transcription), and the transcription is treated as the one closest to the printed book. I label entities on it and score OCR and AI extraction against it.

On 2026-11-19, labelling test page [8992489](https://www.biodiversitylibrary.org/page/8992489) (Butler 1907, The Brambling) against the scan, I found this heading in the transcription:

`Fringilla nontifringilla, LINN.`

The scan says **montifringilla**. The Brambling is *Fringilla montifringilla* ("the mountain fringilla"); `nontifringilla` is no bird's name. An m was typed as an n.

A second one turned up on test page [8992647](https://www.biodiversitylibrary.org/page/8992647): the transcription has `April 20th, I898` where the scan has **1898**, the digit 1 typed as a capital I.

## 21 OCR models read it right

FineBooks publishes the output of more than 20 OCR models on these pages. I checked them all:

| Text version | Page 8992489, the name | Page 8992647, the year |
|---|---|---|
| Expert transcription ("answer key") | `nontifringilla` ✗ | `I898` ✗ |
| BHL legacy OCR | `Frinoii/d iiii>iitijriii<^illii` ✗ | `2otli, 1898` (year right, day wrong) |
| 22 modern OCR models | 21 read `montifringilla` ✓ | 21 read `1898` ✓ |

At these two spots almost every modern OCR model is closer to the book than the answer key. Scored by character error rate against the transcription, every one of them loses points here for being right.

## What we did

The typos could not be fixed silently: every gold mention's position (character offsets) is computed on the transcription, so editing the text would break every position and make the gold irreproducible. Nor could they be ignored: linking a misspelled name to GBIF is bound to fail.

So ANNOTATION_GUIDE went to v0.9:

- the gold `text` and offsets **keep following the transcription**, so they stay reproducible;
- a new column, `scan_text`, holds **what the scan actually says** (`Fringilla montifringilla`, `April 20th, 1898`);
- scoring accepts either reading, and name linking uses `scan_text`;
- known typos are listed in [`data/transcription_errata.csv`](../../data/transcription_errata.csv), with who found them, when, and how they were confirmed.

## An unexpected witness

Later, an exploratory condition asked the LLM to quote the text verbatim and give a separate "repaired reading" (condition G2). On the expert transcription it changed only 4 values, and 3 of them were the transcription's own errors: `nontifringilla`, `I898` and a broken word; the fourth was a ligature (æ).

Two things follow. A "repair" can fix the answer key itself. And judged by F1 alone, the model's correct fix here counts as an error. Only someone who looked at the scan can tell.

## What it taught

- **Ground truth is made by people and has errors.** An expert transcription is an excellent resource, but it is not the book. The book is the scan.
- **Record an error; do not silently fix it.** Keep the original text and positions, put the true reading in its own column, keep an errata list.
- **When many independent systems are "wrong" in the same place, suspect the answer key first.** Twenty-one OCR models reading `montifringilla` is a signal in itself.
- **For OCR benchmarks:** an error in the reference costs every model the same at that spot, so rankings hold but absolute scores are understated; a model that happened to reproduce the reference's error would be overrated. Two typos change little here, but the same check is worth running on a larger reference set.

The two typos are recorded in the repository, and we hope to report them to the maintainers of FineBooks and the IMPACT dataset.
