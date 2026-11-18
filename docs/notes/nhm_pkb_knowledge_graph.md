# 学习笔记：NHM Planetary Knowledge Base 的知识图谱（AWS 博客两篇）

读于 2026-11-18。来源：

- 第一篇：[Building NHM London's Planetary Knowledge Base with Amazon Neptune and the Registry of Open Data on AWS](https://aws.amazon.com/blogs/publicsector/building-nhm-londons-planetary-knowledge-base-with-amazon-neptune-and-the-registry-of-open-data-on-aws/)，2024-06-05，作者 Nishant Casey、Ilan Gleiser、Karsten Schroer、Sam Bydlon（AWS）。讲 PKB 的愿景和整体架构。
- 第二篇：[Hydrating the Natural History Museum's Planetary Knowledge Base with Amazon Neptune and Open Data on AWS](https://aws.amazon.com/blogs/publicsector/hydrating-the-natural-history-museums-planetary-knowledge-base-with-amazon-neptune-and-open-data-on-aws/)，2024-09-13，同一批作者。技术教程，本笔记主要讲这一篇。

**一句话：** 他们把 GBIF 的植物标本记录（演示用约 1,000 万条）连同 NHM 整理的机构表、采集人表放进 Neptune 图数据库，再训练一个图神经网络（R-GCN）预测标本缺失的属性（例子是采集国家）。目的是补全缺失值、发现错误鉴定和异常记录。

## 1. 先分清两个项目

| | AWS PKB（2024） | BHL 原型（2026，BHL Day 报告） |
|---|---|---|
| 主要数据 | GBIF 标本记录、NHM 整理的机构和采集人数据 | BHL 历史文献 |
| 核心任务 | 建知识图谱，用图神经网络补全和查错 | OCR → 实体抽取 → 知识图谱 → GraphRAG |
| 公开程度 | 两篇 AWS 博客，第二篇有示例代码 | 幻灯片和原型指标；完整代码未找到 |
| 人员 | 两篇都提到 Qianqian Gu、Ben Scott、Vincent Smith | Ben Hartley、Qianqian Hiris Gu、Vince Smith |

所以这两篇博客教的是**知识图谱这一层**怎么搭；**OCR 和信息抽取**那一层，BioEvidenceBench 用 FineBooks 和 BHL 的公开数据自己做。

## 2. 流程：六步

| 步骤 | 做什么 | 为什么这样做 |
|---|---|---|
| 1. 生成导入文件 | 用 AWS Glue（PySpark）读 S3 上的 GBIF Parquet，筛出植物，选 16 个字段，清洗后写成 Neptune 的节点 CSV 和边 CSV | GBIF 有 25 亿多条记录，需要分布式处理；Glue 不用自己管服务器 |
| 2. 导入图数据库 | 在 Neptune 笔记本里用 bulk loader 批量导入 | Neptune Serverless 按需伸缩，不用预估容量 |
| 3. 查询 | 用 Gremlin 查询并可视化（演示：查斐济的标本） | 研究者能沿着关系"走"图 |
| 4. 导出训练数据 | 用 Neptune-Export 把选定的节点、边和特征导出到 S3 | 训练图神经网络需要 DGL 格式 |
| 5. 训练和部署 | Neptune ML 自动做数据处理、超参数搜索（最多 20 组）、训练 R-GCN，部署到 SageMaker 端点 | 托管服务，少写训练代码 |
| 6. 推理 | 用带 `Neptune#ml` 参数的 Gremlin 查询，返回最可能的 3 个国家 | 预测和普通查询写法一样 |

## 3. 图的数据模型

导入格式是 Gremlin CSV：节点要有 `~id` 和 `~label`，边要有 `~from` 和 `~to`。他们选了属性图（Gremlin），没选 RDF，理由是好和 Python、Java 集成，遍历语法直观。

**节点**（训练导出配置里出现的）：

| 节点 | 例子 / 属性 |
|---|---|
| `specimen` 标本 | `~id` = `gbif<gbifid>`；属性有学名原文、经纬度、日、月、年、`recordedby`（采集人）、`identifiedby`（鉴定人）、机构代码、国家代码等 16 个字段 |
| `taxon` 分类单元 | `taxonrank`、`status` |
| `country` 国家 | `dependsfrom` |
| `institution` 机构 | 来自 NHM 整理的机构表 |
| `person` 人 | 博客说有一个"采集人及其所属机构"的统一数据集，但示例代码没展示 |

**边：** `discovering_institution`（标本 → 机构）、`determination`（鉴定）、`located_in`、`origing_country`（原文拼写如此）。

## 4. 实体关联是怎么做的

示例代码只展示了"标本 → 机构"这一种边：

- 用标本的 `institutioncode` 和机构表的 `code` 做**完全相等**的连接（先左连接，再丢掉没匹配上的）。
- 没有模糊匹配，没有置信分数，也不统计多少标本没连上机构。

他们公开的 [`planetary-knowledge-base`](https://github.com/NaturalHistoryMuseum/planetary-knowledge-base) 仓库里，机构表（来自 GRSciColl，8,135 行）有 `altCodes` 列，比如 NHM 的别名代码 `BM(NH)`。但博客的连接只用了 `code`，没用 `altCodes`。采集人那一侧，代码只是把 `recordedby` 当文本属性存进标本节点，没展示怎么连到"人"节点。仓库里有一个记录关联（record linkage）训练笔记本，可能就是做这件事的，但我还没细看。

## 5. 数据处理里值得注意的选择

这些选择本身合理，但每一个都会影响后续结果，评估时要知道：

1. **采集人和鉴定人只取第一个**（`getItem(0)`）：多人合作采集的标本，其他人就丢了。
2. **删掉所有逗号和双引号**：这是为了 CSV 格式安全，但 `Smith, J.` 会变成 `Smith J.`，后续做人名匹配时要考虑。
3. **演示子集是按 `gbifid` 排序后取前 1,000 万条**，不是随机抽样。ID 往往和数据集、导入时间相关，所以这个子集可能偏向某些数据集。
4. **`distinct()` 去重**：只去掉完全相同的行，同一标本在不同数据集里的重复记录去不掉。
5. **许可**：博客说 GBIF 数据是 CC-BY-NC。实际上 GBIF 的每个数据集有各自的许可，这句话是简化说法，我没有逐一核实。

## 6. 图神经网络任务和它的"评估"

- **任务：** 节点分类。目标是标本的 `countrycode`（国家）；特征是年份，按 1600–2100 年分成 12 段。模型是 DGL 的 R-GCN，由 Neptune ML 做超参数搜索。
- **演示：** 挑一个标本，确认它的国家属性和"标本—国家"边被人为去掉了，再让模型返回最可能的 3 个国家。
- **博客没有报告任何评估数字：** 没有留出集准确率，没有和简单基线比，也没有按地区或年代分层的结果。这是教程，不是研究报告，所以可以理解。但这正是我们要学着补上的部分。

## 7. 如果要评估这个图谱，该测什么

这一节是本笔记的重点：照着他们的流程，练习"每一层该怎么评估"。

| 层 | 该测什么 | 怎么测 |
|---|---|---|
| 节点 | 去重是否正确；清洗是否改坏了值 | 抽样核对清洗前后的人名、学名 |
| 边（实体关联） | **覆盖率**：多少标本连上了机构；**精确率**：连上的对不对；**歧义率**：一个代码对应几个机构 | 统计未匹配比例；抽 100 条人工核对；比较只用 `code` 和加上 `altCodes` 的差别 |
| 图神经网络 | 留出集的 top-1 和 top-3 准确率 | 和简单基线比（同一分类单元或同一机构最常见的国家）；按大陆和年代分层报告 |
| 数据泄露 | 同一次采集的重复标本不能同时出现在训练集和测试集 | 按采集人加日期分组划分，而不是随机划分 |
| 抽样 | 子集能不能代表全体 | 比较子集和全体在机构、年代、国家上的分布 |
| 来源 | 每个节点和边来自哪个数据集、哪个版本 | 记录 GBIF 快照日期（博客里是 2023-06-01）和每个数据集的许可 |

## 8. 对 BioEvidenceBench 的启发

1. **V2 知识图谱的数据模型可以照搬骨架**：节点是学名、人、地点、机构（正好是我们 v0.2 的字段），再加一个"文献页面"节点。
2. **每条边都要带证据**：这是 PKB 博客里没有、而我们最在意的部分。比如"页面 P 在第 L 行、字符位置 S–E 提到学名 T"。这对应我们的三层证据定位。
3. **实体关联要报告覆盖率、精确率和歧义率**，不能像示例代码那样把没匹配上的直接丢掉。我们的 Butler 学名消歧已经有 `none` 和 `ambiguous` 两类，就是为了这个。
4. **机构字段可以用他们公开的机构表做消歧参考**：GRSciColl 的数据，带别名代码。
5. **任何模型预测都要和简单基线比**，而且要按组划分防止泄露。
6. **规模**：22 页的数据不需要 Neptune 和 SageMaker，用 Python（networkx 或 DuckDB 表）就能搭一个小图谱。

## 9. 没核实或没覆盖的地方

- 博客里的代码片段有几处排版问题（比如一行注释少了 `#`、缩进不一致），不能直接运行，只适合当参考。
- 机构表和采集人表的来源，博客没写。这里的说法来自他们 GitHub 仓库的 README，不是博客。
- 第一篇只根据摘要整理，没有逐句细读；第二篇全文读过。
- 这两篇都不涉及 BHL、OCR、LLM 或 GraphRAG，所以不能用来推测 2026 年 BHL 原型的实现细节。
