# BioEvidenceBench: product summary

Part 1 is the one-page decision memo; part 2 is the product design built from the results. It is a
design, not a deployed product. Numbers marked *(pre-registered)* come from the frozen test run on
16 locked pages; everything else is exploratory ([`DEVIATIONS.md`](../DEVIATIONS.md)). Full numbers:
[results](results.md) · [evaluation settings](eval_settings.md).

[中文版](#中文版)

## Part 1. Decision memo

**Question.** Turning historical biodiversity literature into trustworthy data (names, people,
places, institutions, dates) runs through six steps: OCR, extraction, evidence, entity resolution,
scope, review. Where is reliability lost, and where should the next unit of effort go?

**Evidence.** Two books from the Biodiversity Heritage Library, Butler 1907 (birds) and Reeve 1849
(shells), each page read as legacy OCR, modern open OCR and an expert transcription; gold labelled
by hand before any model output; plan frozen before the test pages ran. Plus 8 botany pages
(PCAS 1898) and a whole-book run on 682 pages.

**Bottom line.** On these English printed books, **OCR was the first and largest loss, and modern
OCR removed most of it** (value F1 0.60 / 0.64 → 0.95 / 0.98, *pre-registered*). **After that, trust
was limited by entity resolution and by the definition of a datum, not by the extraction model**: a
plain GBIF lookup lost 14 of 34 correctly extracted bird names (*pre-registered*), and five
boundary conventions moved botany F1 from 0.83 to 0.94. This does not mean OCR is done: other
languages, layouts, eras, tables, plates and handwriting were not tested.

**Same accuracy is not the same evidence.** Modern OCR with quote-checked extraction, an LLM that
repairs legacy OCR, and reading the page image all reach value F1 of about 0.91–0.98. Only the first
gives every value a mechanical trail back to the page; the others need a person for every repaired
or unanchored value. Requiring evidence did not change accuracy, which says accuracy does not
measure what evidence is for, not that evidence has no value.

**Recommendations**

1. **Keep investing in OCR, accepted on whether names survive**, per kind of material, not on page
   error rate (name preservation predicts extraction almost exactly; page CER does not).
2. **Fund entity resolution as its own workstream.** An LLM linker lifts link recall from 0.59 to
   0.91; the rest is a taxonomy policy for curators.
3. **Write the scope down before scaling.** Ruling BHL index pages out of scope cut the review queue
   by 60%.
4. **Choose routes on evidence, not on F1 alone**, and measure evidence with audit metrics: share
   of values traceable to the page, reviewer time per value, errors caught.
5. **Review by sampling, with evidence attached.** Never skip review because models agree: on legacy
   OCR, 50 (Butler) and 75 (Reeve) errors sat inside the "both models agree" set (*pre-registered*).
6. **Do not buy a bigger extraction model.** Haiku 5.5 is within a few points of Opus 5.5 at about
   1/15 of the cost; spend the difference on 2–5.

**What this does not show.** A pilot on two books and 16 test pages, not a rule for BHL; other
material may fail OCR differently; the books are public, so pre-training exposure cannot be ruled
out (a probe found no sign of page memory); follow-ups designed after unsealing need a fresh test.

## Part 2. Product design

### The user and the job

| User | Situation | What v1 gives them |
| --- | --- | --- |
| **Data curator** (primary) at a library or museum (BHL, NHM, a natural-history collection) | Publishes occurrence data to GBIF or a knowledge base; is accountable for every record | Records with a quote and a page reference each, and a short list of the ones a person must check |
| **Taxonomic editor** | Decides which checklist and species concept the data follow | The names the linker could not settle, with the candidates |
| **Researcher** (downstream) | Cites the data | A trail from each record back to the printed page |

Job: *"Give me records I can publish, show me where each one came from, and tell me which ones a
person must check."*

### The pipeline, step by step

| Step | What happens | Evidence | Decision |
| --- | --- | --- | --- |
| 1. Page → text | Re-OCR with a modern open model (or LLM repair, or reading the image) | Legacy OCR value F1 0.60 / 0.64; modern 0.95 / 0.98 *(pre-registered)*. Name preservation predicts extraction (Spearman 0.95 / 1.00), page CER does not | Keep investing in OCR, accepted per material type on name preservation |
| 2. Text → mentions | The LLM returns a line + verbatim quote; code slices the value | Haiku 0.94 / 0.95, Opus 0.95 / 0.98 on modern OCR | The cheapest model that is good enough |
| 3. Mentions → evidence | Quote checked character by character; image coordinates from OCR word boxes | No accuracy cost *(pre-registered)*; vision-model boxes hit the right word only 67% / 40% | Line + quote on every value; image coordinates from OCR |
| 4. Mentions → entities | The LLM proposes today's accepted name, then a GBIF / MolluscaBase lookup | Plain lookup loses 14 of 34 *(pre-registered)*; LLM linker 0.59 → 0.91; Opus 0.91 vs Haiku 0.76 | Its own workstream; a curator owns the taxonomy policy |
| 5. Scope | A written definition of what counts as a datum | Botany F1 0.83 → 0.94 from five conventions; index pages were 16% of output | Write the scope first; filter BHL `Index` pages |
| 6. Review | Random-sample QA plus targeted checks | Spot-check 25 / 25 correct on modern OCR; a second model found 10 real misses of 14; about 30 s per item | Route by text quality; never skip review on agreement |

### Three routes, three audit costs

| Route | Value F1 (Butler / Reeve) | Where the value comes from | What an auditor must do |
| --- | --- | --- | --- |
| Modern OCR + quote-checked extraction | 0.95 / 0.98 | Sliced from the OCR text | Open the scan only to catch OCR misreads |
| Legacy OCR + LLM repair | 0.96 / 0.91 | The model's reading; about 30% differ from the OCR text | Check every repaired value (about 1 in 12 is wrong) |
| Page image only | 0.96 / 0.98 (value-bag scoring) | The model's transcription | Find every value on the scan by hand |

Where records go to GBIF or into a citable dataset, only the first route gives every value a
mechanical trail back to the page.

### Review routing

- **Route by text quality first.** On legacy OCR, two cheap checks (OCR-junk characters; no exact
  GBIF match for a taxon) catch 55% of errors while flagging 25% of outputs.
- **On clean text, sample.** Errors are rare and single-item signals stop working; estimate quality
  with a random sample and use a second model to find misses.
- **Repaired values are their own queue.** Every value an LLM changed is flagged and checked.

### Model choice and cost

| Model | Value F1 on modern OCR (Butler / Reeve) | Link recall (Butler, expert text) | Cost per 1,000 page-passes, extraction |
| --- | --- | --- | --- |
| Haiku 5.5 | 0.94 / 0.95 | 0.76 | about $0.6 (batch) |
| Sonnet 5.5 | 0.93 / 0.97 | 0.79 | about $10 (sync) |
| Opus 5.5 | 0.95 / 0.98 | 0.91 | about $11 (batch) |
| Fable 5.2 | 0.96 / 0.98 | 0.88 | about $43 (sync) |

Extraction with Haiku, linking with Opus or Fable: linking is one call per distinct name, far fewer
than pages. A rough extrapolation to BHL's 64 million pages (LLM calls only, these books' page
length, not verified elsewhere): about $40,000 with Haiku, $700,000 with Opus. The real cost in the
pilot was people: labelling, linking, review.

### Can a cheap model do the repair? (training follow-up)

A separate study trained a small open model (Qwen3-0.6B) to repair legacy OCR line by line, with a
pre-registered locked test ([RL results](rl_results.md)).

| Question | Answer | Evidence |
| --- | --- | --- |
| Does supervised training on expert transcriptions work? | Partly | Damaged words repaired 4% → 40% on held-out lines of the training books, 21% on an unseen French book; names 1% → 36–44% |
| Does reinforcement learning (GRPO) add anything? | No | From the base model it learns to copy the OCR; after supervised training it repairs no more words and only breaks about a quarter fewer correct ones |
| Can it replace the API repair step? | Not yet | It still changes about 1.8% of correct words; whether its output raises extraction F1 is untested |
| What did it cost? | Little | About $5.86 of GPU for every run, failures included; one supervised run about $0.10 |

Product reading: for this task the money goes into expert examples, not reward engineering; and a
reward must be checked for what "do nothing" scores before any training. The supervised checkpoint
is [published as a research model](https://github.com/dekunsun/BioEvidenceBench/releases/tag/rl-sft-ocr-repair-v1), not for automatic replacement of library text.

### Not known yet

- Other languages, layouts, print eras, tables, plates and handwriting.
- Mollusc name linking (deferred), a review-time study, audit metrics for evidence.
- Whether repair and image reading hold on material outside the models' training data.
- NHM's exact OCR setting. Mistral OCR through OpenRouter (version not reported) was tested: value F1 0.95 Butler, 0.92 Reeve (exploratory).
- Whether the small repair model helps extraction inside the pipeline.

---

## 中文版

第一部分是一页决策备忘录，第二部分是根据结果推出的产品设计。这是设计，不是已上线的产品。标"预注册"的数字来自冻结后在 16 个锁定测试页上的运行，其余都是探索性的（[`DEVIATIONS.md`](../DEVIATIONS.md)）。完整数字见 [results](results.md) 和 [evaluation settings](eval_settings.md)。

### 第一部分 决策备忘录

**问题。** 把历史生物多样性文献变成可信的数据（学名、人名、地名、机构、日期），要经过六步：OCR、抽取、证据、实体解析、范围定义、审核。可靠性丢在哪里？下一笔资源该投在哪里？

**证据。** 生物多样性遗产图书馆的两本书：Butler 1907（鸟类）和 Reeve 1849（贝类）。每页有旧 OCR、现代开源 OCR、专家转录三个版本；金标准在看到任何模型输出之前手工标完；测试页运行前冻结计划。另有 8 页植物学（PCAS 1898）和 682 页的整本书试跑。

**结论。** 在这两本英文印刷书上，可靠性损失最大的一环是 OCR，而现代 OCR 补回了大部分损失（值 F1 0.60 / 0.64 → 0.95 / 0.98，预注册）。OCR 的问题解决之后，拖后腿的不再是抽取模型，而是两件事：一是学名关联，直接查 GBIF，34 个已经正确抽出的鸟类学名里有 14 个没能关联到正确的物种（预注册）；二是"什么算一条数据"没有定义清楚，统一五条边界约定后，植物学 F1 就从 0.83 升到 0.94。这不等于 OCR 已经不用再投：其他语言、版式、年代、表格、图版和手写材料都没测过。

**准确率相同，不等于证据相同。** 现代 OCR + 引语核对的抽取、LLM 读正旧 OCR、直接读扫描图，值 F1 都在约 0.91–0.98。只有第一条路线能让每个值机械地追溯回原页；另外两条，凡是读正过或没有锚点的值都要人来核。要求给证据没有改变准确率，这说明准确率衡量不到证据的用途，而不是证据没有价值。

**建议**

1. **继续投 OCR，按"学名是否完整保留"验收**，按材料类型分别测，不看整页错字率（学名保留率几乎完全预测抽取效果，整页错字率不能）。
2. **把实体解析当成独立的工作来投入。** LLM 关联器把关联召回率从 0.59 提到 0.91；剩下的是馆员要定的分类学口径。
3. **规模化之前先把范围写下来。** 把 BHL 索引页定为范围外，审核量少了 60%。
4. **按证据选路线，不只看 F1**，并用审核指标衡量证据：能追溯到原页的值占多少、每个值的审核时间、能抓到多少错误。
5. **基于抽样审核，并附带证据。** 不要因为模型一致就跳过审核：旧 OCR 上，"两个模型一致"的那组里 Butler 有 50 条、Reeve 有 75 条是错的（预注册）。
6. **不要买更大的抽取模型。** Haiku 5.5 只比 Opus 5.5 低几个百分点，成本约为 1/15；把差价花在第 2–5 条上。

**这份结果说明不了什么。** 只是两本书、16 个测试页的试点，不是适用于整个 BHL 的规律；其他材料的 OCR 出错方式可能不同；这些书是公开的，不能排除模型预训练时见过（记忆探针没有发现记住页面的迹象）；解封后才设计的后续实验需要新的测试集。

### 第二部分 产品设计

**用户和要完成的事**

| 用户 | 处境 | 第一版给他们什么 |
| --- | --- | --- |
| **数据管理员**（主要用户），在图书馆或博物馆（BHL、NHM、自然史收藏机构） | 把数据发布到 GBIF 或知识库，对每条记录负责 | 每条记录都带引语和页码，外加一份必须由人核查的短名单 |
| **分类学编辑** | 决定数据采用哪份名录、哪种物种概念 | 关联器定不了的名字，连同候选 |
| **研究者**（下游） | 引用这些数据 | 每条记录都能追溯回印刷页 |

要完成的事：*"给我能发布的记录，告诉我每条从哪里来，哪些必须由人核查。"*

**逐步看**

| 步骤 | 做什么 | 证据 | 决定 |
| --- | --- | --- | --- |
| 1. 扫描页 → 文字 | 用现代开源模型重新 OCR（或 LLM 读正、直接读图） | 旧 OCR 值 F1 0.60 / 0.64，现代 OCR 0.95 / 0.98（预注册）；学名保留率能预测抽取（Spearman 0.95 / 1.00），整页错字率不能 | 继续投 OCR，按材料类型用学名保留率验收 |
| 2. 文字 → 提及 | LLM 给行号和原文引语，代码切出值 | 现代 OCR 上 Haiku 0.94 / 0.95、Opus 0.95 / 0.98 | 用够用的最便宜模型 |
| 3. 提及 → 证据 | 引语逐字核对；图像坐标来自 OCR 词坐标 | 不降低准确率（预注册）；视觉模型画的框只有 67% / 40% 落在对的词上 | 每个值带行号和引语；图像坐标从 OCR 来 |
| 4. 提及 → 实体 | LLM 先给出今天的接受名，再查 GBIF / MolluscaBase | 直接查丢 14/34（预注册）；LLM 关联器 0.59 → 0.91；Opus 0.91、Haiku 0.76 | 独立的工作；分类学口径由馆员负责 |
| 5. 范围 | 写清"什么算一条数据" | 五条约定让植物学 F1 0.83 → 0.94；索引页占输出的 16% | 先写范围；排除 BHL 的 Index 页 |
| 6. 审核 | 随机抽样质检加定向检查 | 现代 OCR 上抽检 25/25 全对；第二个模型找出 14 条里 10 条真漏抽；每条约 30 秒 | 按文字质量分流；不因模型一致而跳过 |

**三条路线，三种审核成本**

| 路线 | 值 F1（Butler / Reeve） | 值从哪里来 | 审核人要做什么 |
| --- | --- | --- | --- |
| 现代 OCR + 引语核对的抽取 | 0.95 / 0.98 | 从 OCR 文字中切出 | 只在排查 OCR 读错时看扫描页 |
| 旧 OCR + LLM 读正 | 0.96 / 0.91 | 模型的读法，约 30% 与 OCR 原文不同 | 每条读正过的值都要核（约 12 条有 1 条错） |
| 只看扫描图 | 0.96 / 0.98（按值集合计分） | 模型的转录 | 每个值都要人工在页上找 |

数据要进 GBIF 或成为可引用记录时，只有第一条路线能让每个值机械地追溯回原页。

**审核分流**

- **先按文字质量分流。** 旧 OCR 上两条便宜检查（值里有 OCR 乱码字符；学名在 GBIF 没有精确匹配）只标出 25% 的输出，就能抓到 55% 的错误。
- **干净文字上做抽样。** 错误很少，单条信号失效；用随机抽样估计质量，用第二个模型找漏。
- **读正过的值单独排队。** LLM 改过的每个值都标出来，逐条核。

**模型选择和成本**

| 模型 | 现代 OCR 上值 F1（Butler / Reeve） | 关联召回（Butler，专家转录） | 每千页次抽取成本 |
| --- | --- | --- | --- |
| Haiku 5.5 | 0.94 / 0.95 | 0.76 | 约 $0.6（批量） |
| Sonnet 5.5 | 0.93 / 0.97 | 0.79 | 约 $10（同步） |
| Opus 5.5 | 0.95 / 0.98 | 0.91 | 约 $11（批量） |
| Fable 5.2 | 0.96 / 0.98 | 0.88 | 约 $43（同步） |

抽取用 Haiku，关联用 Opus 或 Fable：关联按不同的名字调用，次数远少于页数。粗算到 BHL 全部 6400 万页（只算 LLM 调用，按这两本书的页长，未在其他书上核实）：Haiku 约 4 万美元，Opus 约 70 万美元。这次试点真正的成本是人：标注、学名关联、审核。

**便宜的小模型能不能做修复？（训练后续研究）**

另一项研究训练了一个开源小模型（Qwen3-0.6B）逐行修复旧 OCR，测试集事先锁定、只跑一次（[RL 结果](rl_results.md)）。

| 问题 | 答案 | 依据 |
| --- | --- | --- |
| 用专家转录做监督训练有用吗？ | 部分有用 | 训练书的未见行上，受损词修复率 4% → 40%；没见过的法语书上 21%；学名 1% → 36–44% |
| 强化学习（GRPO）能再加分吗？ | 不能 | 从原模型出发学会了照抄 OCR；在监督训练之后也没有多修一个词，只是改坏的正确词少了约四分之一 |
| 能替代 API 修复这一步吗？ | 暂时不能 | 仍会改坏约 1.8% 的正确词；修复后能否提高抽取 F1 还没测 |
| 花了多少钱？ | 很少 | GPU 共约 $5.86，包括失败的运行；一次监督训练约 $0.10 |

产品上的读法：这个任务的钱应该花在专家示范上，而不是奖励设计上；用奖励训练前，先算"什么都不改"能得多少分。监督训练的检查点已[作为研究模型公开](https://github.com/dekunsun/BioEvidenceBench/releases/tag/rl-sft-ocr-repair-v1)，不能用于自动替换原文。

**还不知道的**

- 其他语言、版式、印刷年代、表格、图版和手写材料。
- 贝类学名关联（已推迟）、审核时间研究、衡量证据价值的审核指标。
- 读正和读图在模型没见过的材料上是否还成立。
- NHM 实际使用的 OCR 设置。通过 OpenRouter 调用的 Mistral OCR（未报告版本）已测：值 F1 Butler 0.95、Reeve 0.92（探索性）。
- 小修复模型放进流程后能否提高抽取效果。
