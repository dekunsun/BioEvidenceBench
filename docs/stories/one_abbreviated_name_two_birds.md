# 一个缩写的鸟名，两种鸟：我如何从一本百年前的鸟书中追查分类学谜题

*从 BHL 历史原文、Avibase 数据库，到 1883 年和 1890 年的两本原著：一个看似简单的鸟类学名，为什么会指向两种不同的鸟？*

[English version below](#one-abbreviated-name-two-birds-tracing-a-taxonomic-mystery-across-more-than-a-century)

最近，我在做一个叫 **BioEvidenceBench** 的项目：让 AI 从历史自然科学文献中识别物种名称，再把这些旧名字关联到今天的生物分类数据库。

这件事听起来不复杂。比如一本旧书写着 *Muscicapa parva*，我可以先找到这个名称，再去 Avibase 查询它今天是否仍被使用，或者已经改成其他学名。

这个故事是我自己做标注时撞上的。给 Butler 书中 29 个历史鸟名逐个填写现代接受名（BioEvidenceBench 的学名关联金标准）时，我遇到了一个让我停下来的名字：

**`M. hyperythra`**

它出现在英国鸟类学家 Arthur Gardiner Butler 的一篇 Red-breasted Flycatcher（红胸姬鹟）介绍中。原本只需要填写一个现代接受名的工作，最后却变成了一次跨越一百多年的文献调查。

## 一、先弄清楚旧书到底写了什么

我的起点是 [Biodiversity Heritage Library（BHL）第 8992379 页](https://www.biodiversitylibrary.org/page/8992379)。BHL 是一个大型数字图书馆，收藏了大量历史自然科学书籍、期刊和插图。

这页的标题是 *The Red-breasted Flycatcher*。在专家转录的正文中，Butler 写道，他很欣赏鸟类学家 Henry Seebohm 对这种鸟的描述，因此要把它全文引用（"I shall quote it in full"）。

原文写的是 `M. hyperythra`，而不是完整的 *Muscicapa hyperythra*。19 世纪科学文献经常这样写学名：第一次使用时写出完整属名，后面只保留第一个字母。结合物种章节和当时使用的分类名称，这里的 `M.` 指的是 **Muscicapa**：

`M. hyperythra` → `Muscicapa hyperythra`

但这仅仅是**还原了作者所写的名字**，并没有证明它对应哪一种现代鸟。这两个问题看似相同，实际上完全不同。

## 二、查 Avibase，出现了两个答案

Avibase 是一个鸟类分类数据库，可以检索现代学名、历史异名、命名作者，以及不同分类体系对同一种鸟的处理方式。查 *Muscicapa hyperythra*，会找到两种鸟。

**候选一：Snowy-browed Flycatcher，现代学名 *Ficedula hyperythra***。橙色胸部、深色头背、醒目的白色眉纹。原始名称 *Muscicapa hyperythra*，命名者 Edward Blyth（Avibase 记作 1843 年；Oates 1890 年印作 1842 年）。来源：[Avibase](https://avibase.bsc-eoc.org/species.jsp?avibaseid=0EEEF8C218D58EC2&lang=EN)

**候选二：Kashmir Flycatcher，现代学名 *Ficedula subrubra***。雄鸟也有红褐色胸部，但没有白眉。它的历史名称包括 *Siphia hyperythra* Cabanis, 1866；后来的组合 *Muscicapa hyperythra*（归于 Cabanis）；以及 *Muscicapa parva subrubra* Hartert & Steinbacher, 1934。来源：[Avibase](https://avibase.bsc-eoc.org/species.jsp?avibaseid=BFB564AA7168EB81)

| 对比 | 第一种鸟 | 第二种鸟 |
|---|---|---|
| 英文名 | Snowy-browed Flycatcher | Kashmir Flycatcher |
| 现代学名 | *Ficedula hyperythra* | *Ficedula subrubra* |
| 历史命名者 | Blyth, 1842/1843 | Cabanis, 1866 |
| 历史名称 | *Muscicapa hyperythra* | *Siphia hyperythra*，也曾组合为 *Muscicapa hyperythra* |

**历史文献里几乎完全一样的名称，可能代表两种不同的鸟。** 关键不只是学名，还有学名后面的命名者和年份：*Muscicapa hyperythra* Blyth 与 *Muscicapa hyperythra* (Cabanis) 文字几乎相同，却指向不同的命名记录。分类数据库里学名后面跟着的人名和年份不是装饰，而是追溯名称身份的线索。

## 三、回到 Butler 的原文，找到上下文

`M. hyperythra` 不是孤立出现的。Butler 正在引用 Seebohm 对 Red-breasted Flycatcher 羽色变化的描述：雄鸟随着年龄增长，喉部和胸部的栗红色逐渐扩大。原文把四个名称排成一个年龄顺序：

| 年龄阶段 | 原文名称 | 羽色变化 |
|---|---|---|
| 第一年 | `M. minuta` | 年轻雄鸟的羽色与雌鸟相似 |
| 第二年 | `M. leucura` | 喉部出现栗红色 |
| 第三年 | `M. parva` | 栗红色扩展到上胸 |
| 第四年 | `M. hyperythra` | 栗红色扩展到下胸 |

在这种解释里，四个名字不一定代表四种鸟，而可能是人们把同一种鸟不同年龄的羽色当成了不同物种。Butler 接受了这种解释，并举了其他鸟类的例子。

这改变了问题。我最初问的是"*Muscicapa hyperythra* 今天叫什么？"，现在要问的是：**Butler 引用 Seebohm 时，这里的 hyperythra 是谁命名的那一种，Seebohm 又用它指什么？**

这里的羽色变化是历史作者的解释，不是今天确认的生物学事实。今天通常分别承认 Red-breasted Flycatcher（*Ficedula parva*）、Taiga Flycatcher（*Ficedula albicilla*）和 Kashmir Flycatcher（*Ficedula subrubra*）。

还有一个细节：在专家转录里，`(M. hyperythra)` 落在**引号外面**：`…lower breast” (M. hyperythra). “Young in first plumage…`。前三个名字在引文里面，第四个却在外面。这说明 Butler 在这里对 Seebohm 的原句做了改动。要知道改了什么，只能去读 Seebohm 的原书。

## 四、从 Butler 追到 Seebohm：缺失的那半句话

Henry Seebohm 的 *A History of British Birds* 第一卷（1883）在 Internet Archive 上有扫描本（[archive.org/details/historyofbritish01seeb](https://archive.org/details/historyofbritish01seeb)，Smithsonian Libraries 扫描，已进入公有领域）。Red-breasted Flycatcher（*Muscicapa parva*）一节从第 332 页开始。

第 336 页，Seebohm 的原句是：

> "…in the third year the chestnut appears on the upper breast (M. parva); and in the fourth year it extends also onto the lower breast, **in which plumage they are the M. hyperythra of Cabanis apud Brooks**."

Butler 引用时删去了 "in which plumage they are the … of Cabanis apud Brooks"，只在引号外留下 `(M. hyperythra)`。被删掉的恰好是**命名者**。

所以第一个问题有了直接答案：**Seebohm 说的 hyperythra 是 Cabanis 命名的那个名称**，不是 Blyth 的。按名称追溯，它对应今天的 Kashmir Flycatcher（*Ficedula subrubra*）。

但这半句话还有后三个字：**"apud Brooks"**，意思是"按 Brooks 的用法"。Seebohm 说的不是 Cabanis 的鸟本身，而是印度鸟类学家 W. E. Brooks 叫作 hyperythra 的那些标本。在同一节第 333–334 页，Seebohm 写道，他手里胸部栗红色最多的印度标本"被标作 M. hyperythra"，但真正的 hyperythra "很容易区分"：栗红色延伸到两胁和尾下覆羽，胸部的栗红色和颈部的灰色之间有一条近黑色的线；他还说，Brooks 认为这条黑线冬天会消失，但锡兰（斯里兰卡）一、二月采到的标本证明并不消失。

按我对这段 OCR 文字的理解（还需要对照扫描页逐字复核）：Seebohm 认为 Brooks 把一些成年 parva 误标成了 hyperythra，而 Cabanis 的真 hyperythra 是另一种有黑线的鸟。今天的 Kashmir Flycatcher 恰好在斯里兰卡越冬，雄鸟栗红色胸部的边缘也有深色线。

于是，这个名字有了两层身份：

| 问题 | 答案 | 证据 |
|---|---|---|
| 这个**名称**是谁命名的？ | Cabanis, 1866 | Seebohm 1883，第 336 页："of Cabanis" |
| Seebohm 用它指**哪些鸟**？ | Brooks 标作 hyperythra 的印度标本，Seebohm 认为是成年 parva | 同页 "apud Brooks"；第 333–334 页 |
| 名称今天对应哪个物种？ | *Ficedula subrubra*（Kashmir Flycatcher） | Oates 1890；Avibase |
| 那些鸟今天是哪个物种？ | 无法从文字判断，要看 Brooks 的标本 | 尚无 |

## 五、Oates 1890：两种 hyperythra 被分进了不同条目

Eugene W. Oates 的 *The Fauna of British India, Including Ceylon and Burma*, Birds, Vol. II（1890）也在 Internet Archive 上（[archive.org/details/faunaofbritishin02euge](https://archive.org/details/faunaofbritishin02euge)；另见 [faunaofindia.nic.in 的扫描件](https://faunaofindia.nic.in/PDFVolumes/fbi/002/index.pdf)）。

**第 9 页**，在 *Siphia parva* 的分布一段，Oates 写道，这种鹟"被许多鸟类学家与下一种混淆，**Seebohm 甚至把 *S. parva*、*S. albicilla* 和 *S. hyperythra* 合并为一个物种**"。Oates 自己分列三条：561 *Siphia parva*（European Red-breasted Flycatcher）、562 *Siphia albicilla*（Eastern Red-breasted Flycatcher）、563 *Siphia hyperythra*（Indian Red-breasted Flycatcher）。

**第 10–11 页**，563 号条目把名称归于 *Siphia hyperythra*, Cabanis, J. f. Orn. 1866, p. 391，异名中列出 *Muscicapa hyperythra* (Cab.), Sharpe, Cat. B. M. iv, p. 163。

**第 15 页**，566 号条目 *Cyornis hyperythrus*（Rufous-breasted Blue Flycatcher）的异名中列出 *Muscicapa hyperythra*, Blyth, J. A. S. B. xi, p. 885 (1842)，对应今天的 Snowy-browed Flycatcher。

| Oates 的条目 | 历史命名者 | 今天所关联的物种 |
|---|---|---|
| 563. *Siphia hyperythra* | Cabanis, 1866 | Kashmir Flycatcher，*Ficedula subrubra* |
| 566. *Cyornis hyperythrus* | Blyth, 1842 | Snowy-browed Flycatcher，*Ficedula hyperythra* |

同一本书在 1890 年就把两个 *Muscicapa hyperythra* 分开了，而 Cabanis 的那一个正好出现在 Oates 讨论 Seebohm 合并观点的地方。

一个小张力值得记下：Oates 说 Seebohm 合并了三者，而 Seebohm 1883 第 333–334 页又说真 hyperythra "很容易区分"。可能 Oates 指的是 Seebohm 的其他著作，也可能是我对 OCR 文字的理解有偏差。这一点我没有查清。

## 六、为什么 Cabanis 的鸟今天不再叫 hyperythra？

Cabanis 在 1866 年使用 *hyperythra* 时，Blyth 的较早名称已经存在。当这些鸟被放进同一个属，两个名称就发生冲突（同名）。1934 年，Hartert 与 Steinbacher 引入替代名 *subrubra*，形式是 *Muscicapa parva subrubra*。后来这种鸟被单独承认为 Kashmir Flycatcher，*Ficedula subrubra*。

*Siphia hyperythra* Cabanis, 1866 → 1934 年替代种加词 *subrubra* → *Ficedula subrubra*

Blyth 的鸟保留了种加词，只换了属：*Muscicapa hyperythra* Blyth → *Ficedula hyperythra*。

## 七、证据链

1. **Butler 1907**（BHL 8992379）：`(M. hyperythra)`，在引号外，是对 Seebohm 原句的缩写。
2. **Seebohm 1883**（第 336 页）：原句是 "the M. hyperythra of Cabanis apud Brooks"。命名者是 Cabanis，指的是 Brooks 用这个名字称呼的标本。
3. **Seebohm 1883**（第 333–334 页）：Seebohm 认为真 hyperythra 可以区分（黑线），Brooks 的标签不可靠。
4. **Oates 1890**（第 9–11 页、第 15 页）：Cabanis 的 *hyperythra*（563）与 Blyth 的 *hyperythra*（566）是两个条目。
5. **Avibase**：Cabanis 的名称 → *Ficedula subrubra*；Blyth 的名称 → *Ficedula hyperythra*。

所以：

- **按名称**，Butler 的 `M. hyperythra` 是 Cabanis 的名称，今天的 *Ficedula subrubra*。把它直接对到 *Ficedula hyperythra*（Blyth）是错的。
- **按所指**，Seebohm 用它指 Brooks 标作 hyperythra 的鸟，并认为那是成年 Red-breasted Flycatcher。那些鸟今天是哪一种，文字证据回答不了。

## 八、为什么 Gold 仍然标 `ambiguous`

BioEvidenceBench 的 Gold Links 是用来给 AI 打分的。如果把一个推断写成确定答案，评测时就可能把模型正确的谨慎判断算成错误。

调查之前，`ambiguous` 的理由是"不知道是 Blyth 还是 Cabanis"。现在这个问题有了原文答案（Cabanis），但出现了一个更根本的理由：**名称和所指分开了**。这里的 hyperythra 是"Cabanis 的名称，Brooks 的用法，Seebohm 的解读"，一个现代接受名无法同时表达这三层。

| 字段 | 当前判断 |
|---|---|
| 历史原文 | `M. hyperythra` |
| 根据上下文展开 | *Muscicapa hyperythra* (Cabanis) |
| 名称对应的现代物种 | *Ficedula subrubra* |
| 容易误连的同名 | *Ficedula hyperythra*（Blyth） |
| 关键证据 | Seebohm 1883，第 333–336 页；Oates 1890，第 9–11、15 页 |
| 状态 | `ambiguous`：名称已追到 Cabanis；所指是 "apud Brooks"，即 Brooks 的用法 |

还没做的：对照 Seebohm 第 333–336 页的扫描图逐字复核（上面引用的是 Internet Archive 的 OCR 文字）；查 Brooks 的原始发表和标本；核对 Cabanis 1866（J. f. Orn. p. 391）的原始描述。

## 九、这件事让我重新理解了 AI 如何帮助科学研究

历史物种名称识别其实包含三个难度不同的任务：

1. **找到文字**：从扫描页或转录中准确识别出 `M. hyperythra`。这考验 OCR 和实体抽取。
2. **理解历史语境**：知道 `M.` 是什么；知道 Butler 在引用 Seebohm；注意到名称落在引号外，说明引文被改过。
3. **寻找现代身份**：在两个同名之间判断命名者，再区分"名称是谁的"和"作者用它指什么"。

一个只靠字符串相似度的系统会返回 `Muscicapa hyperythra → Ficedula hyperythra`。属名变了，种加词不变，看起来非常合理，但很可能把两种鸟混在了一起。BioEvidenceBench 里，只按名字查 GBIF 的关联方法在 34 个正确抽出的学名中丢了 14 个；这个例子说明，即使是"看起来能对上"的名字，也可能是错的。

所以评估科学 AI，除了看答案对不对，还要看：

- 它是否找到了原始文献中的直接证据？
- 它是否能区分历史作者的观点与现代分类结论？
- 它是否保留了从旧名称到现代名称的完整证据链？
- 证据不足时，它是否愿意说"不确定"，而不是编造一个确定结果？

**一个好的科学 AI，不应该只是快速找到答案，还应该能告诉我们：这个答案从哪里来，为什么可信，以及哪些部分仍然没有得到证实。**

这次调查最终仍然没有得到一个"确定"的 Gold Link，但它找到了缺失的那半句话。两个单词的历史鸟名背后，是一百多年的观察、争论、误标、重新分类与命名修正。这正是历史科学文献值得被重新连接、重新理解的原因。

### 主要参考资料

1. [Butler 1907 — BHL 第 8992379 页，*The Red-breasted Flycatcher*](https://www.biodiversitylibrary.org/page/8992379)
2. Henry Seebohm, *A History of British Birds*, vol. 1 (1883)，第 332–336 页：[Internet Archive](https://archive.org/details/historyofbritish01seeb) · [BHL 书目](https://www.biodiversitylibrary.org/bibliography/54484)
3. E. W. Oates, *The Fauna of British India*, Birds, vol. II (1890)，第 9–11、15 页：[Internet Archive](https://archive.org/details/faunaofbritishin02euge) · [faunaofindia.nic.in](https://faunaofindia.nic.in/PDFVolumes/fbi/002/index.pdf)
4. [Avibase — Snowy-browed Flycatcher](https://avibase.bsc-eoc.org/species.jsp?avibaseid=0EEEF8C218D58EC2&lang=EN)
5. [Avibase — Kashmir Flycatcher](https://avibase.bsc-eoc.org/species.jsp?avibaseid=BFB564AA7168EB81)
6. 照片：[BirdLife — Snowy-browed Flycatcher](https://datazone.birdlife.org/species/factsheet/snowy-browed-flycatcher-ficedula-hyperythra) · [Cornell — Kashmir Flycatcher](https://birdsoftheworld.org/bow/species/kasfly1/cur/multimedia?media=photos) · [Cornell — Red-breasted Flycatcher](https://birdsoftheworld.org/bow/species/rebfly/cur/multimedia?media=photos)

*核对说明：Seebohm 和 Oates 的引文核对了 Internet Archive 的 OCR 文字（2026-11-20），还没有逐字对照扫描图；Avibase 页面拒绝了我们的自动访问，其内容按作者查阅时的记录引用。*

---

# One Abbreviated Name, Two Birds: Tracing a Taxonomic Mystery Across More Than a Century

*From a page in the Biodiversity Heritage Library to Avibase and two original books from 1883 and 1890: why did one scientific name point to two different birds?*

I have been working on BioEvidenceBench, a project that uses AI to find species names in historical scientific literature and link them to modern biodiversity databases. The workflow looked simple: find a name in an old book, look it up in a database such as Avibase, record the modern accepted name.

I ran into this while labelling. Filling in the modern accepted name for each of 29 historical bird names in Butler's book (the project's gold standard for name linking), one abbreviated name turned a lookup into an investigation:

**M. hyperythra**

It appears in Arthur Gardiner Butler's account of the Red-breasted Flycatcher (1907).

## 1. Start with the page

The starting point was [BHL page 8992379](https://www.biodiversitylibrary.org/page/8992379), *The Red-breasted Flycatcher*. Butler says he finds Henry Seebohm's description of the bird so satisfactory that he will "quote it in full".

Butler printed `M. hyperythra`, not *Muscicapa hyperythra*: nineteenth-century authors abbreviated a genus after first use. From context, `M.` is **Muscicapa**. But reconstructing the printed name does not say which modern species is meant. Those are two different questions.

## 2. Avibase gives two answers

**Candidate 1: Snowy-browed Flycatcher, *Ficedula hyperythra*.** Orange breast, dark upperparts, a bold white eyebrow. Original name *Muscicapa hyperythra* Blyth (Avibase gives 1843; Oates in 1890 printed 1842). [Avibase](https://avibase.bsc-eoc.org/species.jsp?avibaseid=0EEEF8C218D58EC2&lang=EN)

**Candidate 2: Kashmir Flycatcher, *Ficedula subrubra*.** Also a rich orange breast, no white eyebrow. Historical names include *Siphia hyperythra* Cabanis, 1866; the later combination *Muscicapa hyperythra* (Cabanis); and *Muscicapa parva subrubra* Hartert & Steinbacher, 1934. [Avibase](https://avibase.bsc-eoc.org/species.jsp?avibaseid=BFB564AA7168EB81)

Two biological species, two almost identical historical names. The author and year after a name are not decoration: *Muscicapa hyperythra* Blyth and *Muscicapa hyperythra* (Cabanis) are different nomenclatural records.

## 3. Read the passage around the name

Butler is quoting Seebohm on age-related plumage. Four names are set out as stages:

| Stage | Name | Plumage |
|---|---|---|
| First year | *M. minuta* | Young males resemble females |
| Second year | *M. leucura* | Chestnut on the throat |
| Third year | *M. parva* | Chestnut on the upper breast |
| Fourth year | *M. hyperythra* | Chestnut on the lower breast |

On this reading, the four names may be one bird at four ages, mistaken for four species. That is a historical interpretation; today the Red-breasted (*Ficedula parva*), Taiga (*F. albicilla*) and Kashmir (*F. subrubra*) Flycatchers are generally treated as distinct species.

One detail in the expert transcription: `(M. hyperythra)` sits **outside** the closing quotation mark (`…lower breast” (M. hyperythra). “Young in first plumage…`), while the first three names are inside. Butler changed Seebohm's sentence here. Only Seebohm's book can show what was changed.

## 4. Seebohm: the missing half-sentence

Volume 1 of Seebohm's *A History of British Birds* (1883) is on the Internet Archive ([historyofbritish01seeb](https://archive.org/details/historyofbritish01seeb), scanned by Smithsonian Libraries, public domain). The Red-breasted Flycatcher (*Muscicapa parva*) begins on page 332. On page 336 Seebohm wrote:

> "…in the third year the chestnut appears on the upper breast (M. parva); and in the fourth year it extends also onto the lower breast, **in which plumage they are the M. hyperythra of Cabanis apud Brooks**."

Butler cut "in which plumage they are the … of Cabanis apud Brooks" and left `(M. hyperythra)` outside the quotation. What he cut was the **naming authority**.

So the first question has a direct answer: **Seebohm's hyperythra is Cabanis's name**, not Blyth's. Followed as a name, it leads to today's Kashmir Flycatcher, *Ficedula subrubra*.

But the half-sentence ends with **"apud Brooks"**: "as used by Brooks". Seebohm means the specimens the Indian ornithologist W. E. Brooks called hyperythra. On pages 333–334 Seebohm says his Indian skins with the most chestnut "are labelled M. hyperythra", but that the true hyperythra "may easily be distinguished" by chestnut on the flanks and under tail-coverts and a nearly black line between the chestnut breast and the grey neck; Brooks thought the line was lost in winter, which birds shot in Ceylon in January and February disprove.

My reading of that OCR text (still to be checked word by word against the scans): Seebohm thought Brooks had labelled some adult *parva* as hyperythra, while Cabanis's true hyperythra was a different bird with a dark line. Today's Kashmir Flycatcher winters in Sri Lanka, and the male's chestnut breast is bordered by a dark line.

The name now has two identities:

| Question | Answer | Evidence |
|---|---|---|
| Whose **name** is it? | Cabanis, 1866 | Seebohm 1883, p. 336: "of Cabanis" |
| Which **birds** did Seebohm mean? | The Indian skins Brooks labelled hyperythra, which Seebohm took for adult *parva* | "apud Brooks", p. 336; pp. 333–334 |
| Today's species for the name | *Ficedula subrubra* (Kashmir Flycatcher) | Oates 1890; Avibase |
| Today's species for those birds | Cannot be told from the text; it would need Brooks's specimens | none yet |

## 5. Oates, 1890: two hyperythras in two entries

E. W. Oates, *The Fauna of British India, Including Ceylon and Burma*, Birds, Vol. II (1890), is also on the Internet Archive ([faunaofbritishin02euge](https://archive.org/details/faunaofbritishin02euge); scan also at [faunaofindia.nic.in](https://faunaofindia.nic.in/PDFVolumes/fbi/002/index.pdf)).

- **Page 9**, under *Siphia parva*: the bird "has been confounded with the next by many ornithologists, **Seebohm going so far as to unite S. parva, S. albicilla, and S. hyperythra into one species**." Oates keeps three entries: 561 *Siphia parva* (European Red-breasted Flycatcher), 562 *Siphia albicilla* (Eastern Red-breasted Flycatcher), 563 *Siphia hyperythra* (Indian Red-breasted Flycatcher).
- **Pages 10–11**, entry 563: *Siphia hyperythra*, Cabanis, J. f. Orn. 1866, p. 391; synonymy includes *Muscicapa hyperythra* (Cab.), Sharpe, Cat. B. M. iv, p. 163.
- **Page 15**, entry 566 *Cyornis hyperythrus* (Rufous-breasted Blue Flycatcher): synonymy includes *Muscicapa hyperythra*, Blyth, J. A. S. B. xi, p. 885 (1842): today's Snowy-browed Flycatcher.

The same book separated the two *Muscicapa hyperythra* in 1890, and Cabanis's name sits exactly where Oates discusses Seebohm's grouping.

A tension worth recording: Oates says Seebohm united the three, while Seebohm 1883 (pp. 333–334) says the true hyperythra is easy to tell apart. Oates may mean another of Seebohm's works, or my reading of the OCR may be off. I have not resolved it.

## 6. Why Cabanis's bird is now *subrubra*

Blyth's *hyperythra* was older than Cabanis's. Once the two birds were placed in the same genus, the names collided. In 1934 Hartert and Steinbacher introduced the replacement epithet *subrubra* (*Muscicapa parva subrubra*); the Kashmir Flycatcher is now *Ficedula subrubra*. Blyth's bird kept its epithet: *Muscicapa hyperythra* Blyth → *Ficedula hyperythra*.

## 7. The evidence chain

1. **Butler 1907** (BHL 8992379): `(M. hyperythra)`, outside the quotation, a shortening of Seebohm's sentence.
2. **Seebohm 1883**, p. 336: "the M. hyperythra of Cabanis apud Brooks": Cabanis's name, Brooks's usage.
3. **Seebohm 1883**, pp. 333–334: the true hyperythra can be told apart (the dark line); Brooks's labels are not reliable.
4. **Oates 1890**, pp. 9–11 and 15: Cabanis's *hyperythra* (563) and Blyth's (566) are different entries.
5. **Avibase**: Cabanis's name → *Ficedula subrubra*; Blyth's → *Ficedula hyperythra*.

So: **as a name**, Butler's `M. hyperythra` is Cabanis's, today *Ficedula subrubra*; linking it to *Ficedula hyperythra* (Blyth) is wrong. **As a reference**, Seebohm used it for Brooks's birds, which he took to be adult Red-breasted Flycatchers; what those birds are today, the texts cannot say.

## 8. Why the gold link stays `ambiguous`

BioEvidenceBench's gold links score AI systems. Writing an inference as a certain answer would mark a model's justified caution as an error.

Before this search, `ambiguous` meant "Blyth or Cabanis?". That question now has a primary-source answer (Cabanis). A more basic reason replaced it: **the name and the reference have come apart**. This hyperythra is "Cabanis's name, Brooks's usage, Seebohm's interpretation", and one modern accepted name cannot carry all three.

| Field | Working value |
|---|---|
| Printed mention | `M. hyperythra` |
| Contextual expansion | *Muscicapa hyperythra* (Cabanis) |
| Modern species of the name | *Ficedula subrubra* |
| Easily confused homonym | *Ficedula hyperythra* (Blyth) |
| Key evidence | Seebohm 1883, pp. 333–336; Oates 1890, pp. 9–11, 15 |
| Status | `ambiguous`: the name is traced to Cabanis; the reference is "apud Brooks", Brooks's usage |

Still to do: check Seebohm pp. 333–336 word by word against the scans (the quotations above are from the Internet Archive's OCR); find Brooks's publications and specimens; read Cabanis 1866 (J. f. Orn. p. 391).

## 9. What this says about scientific AI

There are three tasks here, of rising difficulty:

1. **Finding the text**: reading `M. hyperythra` correctly from a scan or transcription.
2. **Reading the context**: expanding `M.`, seeing that Butler quotes Seebohm, noticing that the name sits outside the quotation marks.
3. **Resolving the identity**: choosing between homonyms by authority, then separating whose name it is from what the author meant by it.

A string-matching linker returns `Muscicapa hyperythra → Ficedula hyperythra`. Only the genus changes; it looks right, and it probably joins two different birds. In BioEvidenceBench a plain GBIF name lookup lost 14 of 34 correctly extracted names; this case shows that even a name that does match can be wrong.

So beyond whether an answer is right, a scientific AI should be judged on whether it finds the direct evidence in the original source, separates a historical author's view from a modern conclusion, keeps the chain from printed name to accepted name, and says "uncertain" when the evidence stops.

**Good scientific AI should not only produce answers. It should show where an answer comes from, why it is credible, and which parts are not yet confirmed.**

This search still did not produce a "certain" gold link. It did find the missing half-sentence. Behind two abbreviated Latin words are more than a century of observation, argument, mislabelling, reclassification and renaming, which is why historical scientific literature is worth reconnecting and rereading.

### Sources

1. [Butler 1907 — BHL page 8992379](https://www.biodiversitylibrary.org/page/8992379)
2. Henry Seebohm, *A History of British Birds*, vol. 1 (1883), pp. 332–336: [Internet Archive](https://archive.org/details/historyofbritish01seeb) · [BHL record](https://www.biodiversitylibrary.org/bibliography/54484)
3. E. W. Oates, *The Fauna of British India*, Birds, vol. II (1890), pp. 9–11, 15: [Internet Archive](https://archive.org/details/faunaofbritishin02euge) · [faunaofindia.nic.in](https://faunaofindia.nic.in/PDFVolumes/fbi/002/index.pdf)
4. [Avibase — Snowy-browed Flycatcher](https://avibase.bsc-eoc.org/species.jsp?avibaseid=0EEEF8C218D58EC2&lang=EN)
5. [Avibase — Kashmir Flycatcher](https://avibase.bsc-eoc.org/species.jsp?avibaseid=BFB564AA7168EB81)
6. Photos: [BirdLife — Snowy-browed Flycatcher](https://datazone.birdlife.org/species/factsheet/snowy-browed-flycatcher-ficedula-hyperythra) · [Cornell — Kashmir Flycatcher](https://birdsoftheworld.org/bow/species/kasfly1/cur/multimedia?media=photos) · [Cornell — Red-breasted Flycatcher](https://birdsoftheworld.org/bow/species/rebfly/cur/multimedia?media=photos)

*Checking note: the Seebohm and Oates quotations were checked against the Internet Archive's OCR text (2026-11-20), not yet word by word against the scans. Avibase refused our automated access; its content is cited as the author recorded it.*
