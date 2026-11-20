# BioEvidenceBench: product summary

What the evaluation implies for a literature-to-data pipeline on BHL. It is a design built from the
results, not a deployed product. Numbers marked *(pre-registered)* come from the frozen test run;
everything else is exploratory (`DEVIATIONS.md`).

[中文版](#中文版)

## On one page

| Item | Content |
| --- | --- |
| Product | A pipeline that turns scanned historical biodiversity literature into structured records (taxon, person, place, institution, date), each traceable to the page |
| Users | Data curators at a library or museum (BHL, NHM, a natural-history collection) who publish occurrence data to GBIF or a knowledge base; downstream, researchers who cite it |
| Job | *"Give me records I can publish, show me where each one came from, and tell me which ones a person must check."* |
| The evaluation | Six steps from page to record; for each, how much reliability is lost and what it costs to win back. Gold labelled before any model output; frozen before the test pages ran |
| What it found | OCR is the first and largest loss on these books, and modern OCR removes most of it; after that, entity resolution and the definition of a datum limit trust, not the extraction model |
| Status | Pilot on two English books (1849, 1907) plus 8 botany pages; whole-book run on 682 pages; not deployed |

## The pipeline, step by step

| Step | What happens | Evidence | Decision |
| --- | --- | --- | --- |
| 1. Page → text | Re-OCR with a modern open model (or LLM repair, or reading the image) | Legacy OCR: value F1 0.60 / 0.64; modern 0.95 / 0.98 *(pre-registered)*. Name preservation predicts extraction, page error rate does not | Keep investing in OCR, accepted per material type on whether names survive |
| 2. Text → mentions | LLM returns line + verbatim quote; code slices the value | Haiku 0.94 / 0.95, Opus 0.95 / 0.98 on modern OCR; Haiku about 1/15 of the cost | Use the cheapest model that is good enough |
| 3. Mentions → evidence | Quote checked character by character; image coordinates from OCR word boxes | No accuracy cost *(pre-registered)*; vision-model boxes hit the right word only 67% / 40% | Keep line + quote on every value; take image coordinates from OCR |
| 4. Mentions → entities | LLM proposes today's accepted name, then a GBIF / MolluscaBase lookup | Plain lookup loses 14 of 34 names *(pre-registered)*; LLM linker recall 0.59 → 0.91; Opus 0.91 vs Haiku 0.76 | Fund as its own workstream; a curator owns the taxonomy policy |
| 5. Scope | A written definition of what counts as a datum | Five boundary conventions move botany F1 0.83 → 0.94; index pages were 16% of output | Write the scope before scaling; filter BHL `Index` pages |
| 6. Review | Random-sample QA plus targeted checks | Agreement is not correctness (50 / 75 flagged errors on legacy OCR, *pre-registered*); spot-check 25 / 25 correct on modern OCR; about 30 s per item | Route by text quality; never skip review because models agree |

## Same accuracy is not the same evidence

| Route | Value F1 | Where the value comes from | What an auditor must do |
| --- | --- | --- | --- |
| Modern OCR + quote-checked extraction | 0.95 / 0.98 | Sliced from the OCR text | Open the scan only to catch OCR misreads |
| Legacy OCR + LLM repair | 0.96 / 0.91 | The model's reading; about 30% differ from the OCR text | Check every repaired value (about 1 in 12 is wrong) |
| Page image only | 0.96 / 0.98 (value-bag scoring) | The model's transcription | Find every value on the scan by hand |

Where records go to GBIF or into a citable dataset, only the first route gives every value a
mechanical trail back to the page.

## Cost

Per 1,000 page-passes, extraction only: Haiku 5.5 about $0.6 (batch), Opus 5.5 about $11 (batch).
The whole-book run (682 pages) took 7.5 minutes per batch. A rough extrapolation to all of BHL's 64
million pages (LLM calls only, these books' page length, not verified on other books): about $40,000
with Haiku, $700,000 with Opus. The real cost in this pilot was people: labelling, linking, review.

## What is not known yet

- Other languages, layouts, print eras, tables, plates and handwriting.
- Mollusc name linking (deferred), a review-time study, audit metrics for evidence.
- Whether repair and image reading hold on material outside the models' training data.

---

## 中文版

这一页说的是：评测结果对"把 BHL 文献变成数据"的流程意味着什么。它是根据结果推出来的设计，不是已经上线的产品。标"预注册"的数字来自冻结后的测试运行，其余都是探索性的（`DEVIATIONS.md`）。

| 项目 | 内容 |
| --- | --- |
| 产品 | 把扫描的历史生物多样性文献变成结构化记录（学名、人名、地名、机构、日期），每条都能追溯回原页 |
| 用户 | 图书馆或博物馆的数据管理员（BHL、NHM、自然史收藏机构），他们把数据发布到 GBIF 或知识库；下游是引用这些数据的研究者 |
| 要完成的事 | "给我能发布的记录，告诉我每条从哪里来，哪些必须由人核查" |
| 评测 | 从扫描页到记录分六步，每一步测丢了多少可靠性、补回来要多少代价；金标准在看到任何模型输出之前标完，测试前冻结 |
| 发现 | 在这两本书上，OCR 是第一个、也是最大的损失，现代 OCR 补回了大部分；之后限制可信度的是实体解析和"什么算一条数据"的定义，不是抽取模型 |
| 状态 | 两本英文书（1849、1907）加 8 页植物学的试点；682 页整本书试跑；未上线 |

**逐步看**

| 步骤 | 做什么 | 证据 | 决定 |
| --- | --- | --- | --- |
| 1. 扫描页 → 文字 | 用现代开源模型重新 OCR（或 LLM 读正、直接读图） | 旧 OCR 值 F1 0.60 / 0.64，现代 OCR 0.95 / 0.98（预注册）；学名保留率能预测抽取效果，整页错字率不能 | 继续投 OCR，按材料类型用"学名是否完整保留"验收 |
| 2. 文字 → 提及 | LLM 给行号和原文引语，代码从原文切出值 | 现代 OCR 上 Haiku 0.94 / 0.95、Opus 0.95 / 0.98；Haiku 成本约为 Opus 的 1/15 | 用够用的最便宜模型 |
| 3. 提及 → 证据 | 引语逐字核对；图像坐标来自 OCR 词坐标 | 不降低准确率（预注册）；视觉模型画的框只有 67% / 40% 落在对的词上 | 每个值保留行号和引语；图像坐标从 OCR 来 |
| 4. 提及 → 实体 | LLM 先给出今天的接受名，再查 GBIF / MolluscaBase | 直接查 GBIF 丢 14/34（预注册）；LLM 关联器召回 0.59 → 0.91；Opus 0.91、Haiku 0.76 | 当成独立工作投入；分类学口径由馆员负责 |
| 5. 范围 | 写清"什么算一条数据" | 统一五条边界约定，植物学 F1 0.83 → 0.94；索引页占输出的 16% | 规模化前先写范围；排除 BHL 的 Index 页 |
| 6. 审核 | 随机抽样质检加定向检查 | 一致不等于正确（旧 OCR 上被标为一致的有 50 / 75 条错，预注册）；现代 OCR 抽检 25/25 全对；每条约 30 秒 | 按文字质量分流；不因模型一致而跳过审核 |

**准确率相同不等于证据相同。** 现代 OCR + 引语核对的抽取，值从 OCR 文字中切出，审核人只在排查 OCR 读错时看扫描页；旧 OCR + LLM 读正，约 30% 的值是模型改过的读法，每条都要人核，约 12 条有 1 条错；只看扫描图，没有文字证据，每个值都要人工在页上找。数据要进 GBIF 或成为可引用记录时，只有第一条路线能让每个值机械地追溯回原页。

**成本。** 每 1,000 页次只算抽取：Haiku 5.5 约 $0.6（批量），Opus 5.5 约 $11（批量）。整本书 682 页，每个批次 7.5 分钟。粗算到 BHL 全部 6400 万页（只算 LLM 调用，按这两本书的页长，未在其他书上核实）：Haiku 约 4 万美元，Opus 约 70 万美元。这次试点真正的成本是人：标注、学名关联、审核。

**还不知道的。** 其他语言、版式、印刷年代、表格、图版和手写材料；贝类学名关联（已推迟）、审核时间研究、衡量证据价值的审核指标；读正和读图在模型没见过的材料上是否还成立。
