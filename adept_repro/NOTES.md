# ADEPT 复现笔记（给 Gloria，2026-11-18）

> 目的：学习 NHM 团队如何**构建并评估**一个科学文本挖掘系统，而不是造新东西。
> 本文件中所有数字都来自 `adept_repro/outputs/` 里的脚本输出；标 **[未核实]** 的是我没能对照原始来源确认的说法。
> 没有调用任何付费 API；只用公开数据（BHL 开放数据 S3、Hugging Face、ADEPT 公开仓库）。没有使用任何 Cal Academy 内部数据。

---

## 0. 一页摘要

| 项目 | 发布值 | 我们复现的值 | 结论 |
|---|---|---|---|
| 描述分类器（幻灯片 BHL Day 2026） | 151 找到 / 13 漏掉 / 14 误报 / 1,014 正确排除 | **151 / 13 / 14 / 1,014**（阈值 0.5） | ✅ 完全复现，但用的是阈值 0.5；ADEPT 运行时实际用 0.9 |
| 描述分类器（HF meta.json） | description P=0.9304, R=0.8963 | **P=0.9304, R=0.8963**（阈值 0.9：147/17/11/1,017） | ✅ 完全复现 |
| 数值/测量 NER（HF 模型卡） | P=0.9736, R=0.9758, F=0.9747 | 验证集 **0.9736 / 0.9758 / 0.9747**；测试集 **0.9589 / 0.9692 / 0.9640** | ✅ 复现；发布的是**验证集**分数，留出测试集低约 1 个百分点 |
| 性状抽取（仓库内 evaluation notebook） | micro P=0.905, R=0.832, F1=0.867（50 条开发集描述） | **完全相同**（逐字段也相同） | ✅ 复现；作者自己注明是开发集、不是独立测试集 |
| README 例子 `adept traits --taxa "Leersia hexandra"` | — | 跑通，13 个 BHL 页面检出描述 → 1 行性状矩阵（17 个非空性状字段）+ 94 行出处记录 | ✅（eFloras 被 Cloudflare 拦截，见下） |
| README 例子 `adept descriptions --taxa "Achillea millefolium"` | — | 跑通：10,274 页 → 334 页 → 38 页 BHL 描述 + 1 条 EcoFlora（eFloras 被拦） | ✅ |
| ADEPT 自带单元测试 `test/` | — | 9 通过、5 失败、1 个收集错误（测试与代码 API 不同步：`Fields.to_template`、`config.App` 已不存在；单位格式 '1.0 cm' vs '10 mm'），见 `outputs/unit_tests.txt` | ⚠️ |

最重要的三条经验（详见 §6）：
1. **"发布的分数"要问清楚：哪个切分、哪个阈值、跟生产配置是否一致。** ADEPT 的两个模型的公开分数都能复现，但一个是验证集分数，一个用的阈值不是运行时阈值。
2. **"错误"和"空结果"要分开。** eFloras 返回 403 时，ADEPT 记一条 "No results"，luigi 汇总显示 "This progress looks :)"。被拦截的来源看起来和"这个物种没有描述"完全一样。
3. **漏斗式流水线：便宜的规则先过滤，贵的模型后上。** Leersia：866 页命中名字 → 80 页过关键词过滤 → 13 页检出描述。每一级都应该单独评估召回率；ADEPT 只评估了分类器那一级。

---

## 1. 我们做了什么 / 环境

- 仓库：<https://github.com/NaturalHistoryMuseum/ADEPT>，MIT（© Ben Hartley）。
  固定在 tag **v1.0.0 = commit `8c6cf4e8c5a25ff79a1364bdde3f5c22752e77ab`**（2026-09-29，也是当前 HEAD）。
- 独立环境：`adept_repro/.venv-adept`（Python 3.11.18，git-ignored）。依赖用 ADEPT 自己的 `uv.lock` 导出
  （`uv export --frozen`），只把 `torch==2.10.0` 换成 CPU 版本、去掉 nvidia/triton（省掉约 4 GB CUDA 包）。
  关键版本：spaCy 3.7.5、spacy-transformers 1.3.9、transformers 4.49.0、torch 2.10.0+cpu、taxonerd 1.5.4。
- 模型（Hugging Face，按代码里写死的 revision 下载）：
  - `benhartley/en_description_classifier` @ `d009096…`（spaCy TextCatBOW，ngram≤5，~1.2 GB 快照，含 576 MB wheel）
  - `benhartley/en_adept_ner_trf` @ `857dba1…`（spaCy transformer 流水线，~2.9 GB 快照，含 1.35 GB wheel）
  - 第三方 TaxoNERD `en_ner_eco_biobert` 1.1.0（lock 里有）
  - `en_core_web_trf` 3.7.3（**未声明依赖**，见 §1.1）

### 1.1 安装中遇到的问题和处理

| 问题 | 原因 | 处理 |
|---|---|---|
| `ModuleNotFoundError: adept.bhl.ocr` | v1.0.0 的 `adept/tasks/description/bhl/text.py` 导入 `adept.bhl.ocr.BHLOCR`，但这个文件**不在仓库里** | 写了一个最小桩 `patches/0001-add-missing-adept-bhl-ocr-stub.patch`：只实现被调用的 `get_page_ocr(page_id)`，请求 BHL 公共 page-text 接口。原实现未知 **[未核实]**。这是唯一的代码改动。 |
| `en_core_web_trf` 找不到 | `adept/components/anatomical.py` 用 `spacy.load("en_core_web_trf")`，但它不在 pyproject/uv.lock 里 | 手动安装 3.7.3 wheel（457 MB） |
| 代码里的 HF 仓库名是 `Benscott/...`，README 写 `benhartley/...` | 账号改名 | HF 自动重定向，revision SHA 一致，无需改动 |
| **两个模型下载到同一个目录** `adept/data/models/` | `classifier.py` 和 `pipeline.py` 都用 `snapshot_download(local_dir=MODEL_DIR)` | 未修改。实测：每次运行都会互相覆盖 `config.cfg`、`meta.json`、`vocab/*`（日志里每次都重新 "Fetching 13 files" / "Fetching 24 files"）。因为两个模型在同一进程里先后加载进内存，所以**碰巧能用**，但很脆弱，而且会多下载 ~1.9 GB wheel。 |
| 自带单元测试过时 | 5 failed / 9 passed / 1 collection error：测试调用的 `Fields.to_template`、`adept.config.App` 在 v1.0.0 已不存在 | 只记录，不修 |
| 模型训练时 spaCy 版本 `>=3.4.4,<3.5.0`，ADEPT 锁定 3.7.5 | 版本漂移 | 只有警告；分数仍能完全复现 |

### 1.2 数据资产和 Cloudflare

| 资产 | 大小 | 结果 |
|---|---|---|
| `adept assets bhl-names` → `www.biodiversitylibrary.org/data/hosted/data.zip` | 2.45 GB | 这个 URL **没有**被 Cloudflare 拦（HTTP 200）。但 `create_bhl_names_index` 用 pandas 读 `pagename.txt`（216,874,371 行），15 GB 内存、无 swap 装不下。 |
| 替代：BHL 开放数据 S3 `data/{pagename,page,item,title}.txt.gz` | 2.1 GB + 0.6 GB + 32 MB | 用 DuckDB 按 `assets.py` 同样的逻辑重建（`scripts/build_bhl_names_index.py`）：英文页 **137,999,451** 行、3,338,959 个不同名字、18,009,696 页。pagename 原始行数 216,874,371，与 FineBooks `bhl-metadata/page_name` 的条数一致。 |
| BHLSearchTask 在 import 时把整个索引读进 pandas | — | 同样装不下 → 为查询的物种生成**子集索引**（物种名 + WorldFlora 同物异名，和 `search()` 完全同一个过滤），对这些物种结果等价。 |
| `adept assets bhl-ocr`（Figshare OCR 全文导出） | 默认版本 2025-03-03：**44.5 GB**；当前 v24（2026-11-15）：**46.7 GB** | 超过 5 GB 上限，没下载。只用 HTTP Range 读了两个版本的前 3 MB，查看 tar 成员名（见下）。 |
| BHL API / pagetext | — | Cloudflare 403（`cf-mitigated: challenge`），而且 API 需要 key（返回 401）。 |
| BHL `pageimage/<id>`（Tesseract 路径用） | — | **能用**：302 跳转到 S3 上的 webp。但容器里没有 tesseract 可执行文件，没有跑 `--ocr TESSERACT`。 |
| eFloras（efloras.org） | — | Cloudflare 403 |
| EcoFlora（ecoflora.org.uk） | — | 200，可用 |

**文本怎么进去的**：ADEPT 的 `BHLTextTask.archive_get_text()` 读 `adept/.cache/bhl-ocr-archive/<ItemID:06>-<PageID:08>-<Seq:04>.txt`；
S3 的文件是 `ocr/item-<ItemID:06>/item-<ItemID:06>-<PageID:08>-<Seq:04>.txt`。只要改个名，**不用改 ADEPT 代码**。
`scripts/fetch_s3_ocr.py` 用 ADEPT 自己的 `BHLSearchTask.search()` 选页，从 S3 拉下来放进归档目录（Leersia 866 页、Achillea 10,274 页，全部 200）。

**顺带发现的格式漂移（数据工程教训）**：
- 2025-03-03 导出的 tar 成员名是 `bhl-ocr-20250303/000/000690/000690-00000863-0013.txt`，和 ADEPT 读取的文件名一致；
  但 `create_bhl_ocr_text_archive` 用 `name.split("-")[1]`（= `"00000863"`，补零的）去匹配 `str(PageID)`（= `"863"`，不补零的），
  所以 **PageID < 10,000,000 的页会被静默跳过**（推断自代码 + tar 头，没有跑完整解压）。
- 2026-11-15 导出改成 `item-295621-61016244-0039.txt`：`split("-")[1]` 变成 ItemID，保存的文件名多了 `item-` 前缀，ADEPT 会**完全找不到**。

---

## 2. ADEPT 流水线：每一级做什么

```
物种名 (binomial)
  │  WorldFlora (本地 parquet，142 万条) → 同物异名列表
  ▼
[1] 检索：BHL 名字索引 (TaxonFinder/GNRD 在旧 OCR 上自动识别的名字，页级)   ← 规则/查表
  │     Leersia: 1,355 次出现 / 866 页；Achillea: 11,864 次 / 10,274 页
  ▼
[2] 取文本：本地 OCR 归档 → 否则 BHL API（或 Tesseract 重新 OCR 页面图像）
  ▼
[3] 便宜过滤：SimpleTraitTextClassifier —— 页面 ≥2,500 字符且命中 ≥15 个性状词表术语   ← 规则
  │     Leersia: 80 页；Achillea: 334 页
  ▼
[4] 预处理 + TaxoNERD (BioBERT NER, 第三方) 找所有分类单元提及 → 按双换行切段落
  ▼
[5] 段落选择规则：段内分类单元必须全部匹配目标名/异名；跳过图注、标题；>50 tokens   ← 规则
  ▼
[6] 描述分类器 (spaCy BOW textcat，阈值 0.9)：这段是不是形态描述？                      ← 小模型
  │     Leersia: 13 页 / 25 段
  ▼
[7] 性状抽取 Pipeline：
  │   - en_adept_ner_trf：数值/测量 NER（MEASUREMENT, DIMENSION, CARDINAL, NUMERIC_CADJ）  ← 小模型
  │   - en_core_web_trf 依存句法 + 解剖部位 EntityRuler（796 条模式）→ 找句子主语部位       ← 规则
  │   - 性状词表 3,632 条 (traits.parquet：term→character→trait→part) 做 Matcher           ← 规则
  │   - 单位换算 (pint)、范围解析、倍性/基数自定义规则                                      ← 规则
  ▼
[8] 字段模板 fields.tpl.yml 把内部字段映射到 81 个输出性状列（被子植物）
  ▼
[9] 输出：每来源一张表 + 合并表 + provenance 表（trait, value, verbatim, source_url=BHL 页面）
```

数据来源除了 BHL，还有 eFloras（北美、中国、巴基斯坦植物志）和 EcoFlora——这些是**现代、结构化**的描述，质量远好于 BHL OCR。

### 为什么是"分类器 + NER + 规则"，而不是通用 LLM？

仓库和模型卡里**没有**写明理由，下面是我从代码和时间线推断的 **[推断，未核实]**：
- **时间**：两个模型都是 2024-10 发布到 HF 的，训练用 spaCy 3.4；这条路线早于便宜可靠的 LLM 抽取。
- **规模和成本**：幻灯片说处理了 106,433 段描述、59,360 个物种 **[来自 Gloria 已核对的幻灯片]**。BOW 分类器在 CPU 上处理 1,192 段只要几秒（本次实测），LLM 按 token 计费会贵很多。
- **可控和可追溯**：性状值来自一个人工维护的词表（3,632 条），输出必须落在这个受控词表里；provenance 表保留 `verbatim` 原文词和来源页。LLM 会自由改写（这正是 BioEvidenceBench 的 "silent correction" 风险）。
- **任务本身很"窄"**：植物描述是高度格式化的电报体（"Leaves opposite, ovate, 3–5 cm"），规则 + 词表就能覆盖大部分；数字和单位用专门的 NER + pint 解析，比 LLM 做算术更稳。
- 代价：召回受词表限制（例如 `indumentum` R=0.48、`inflorescence arrangement` R=0.31，见 `outputs/traits_eval/per_field_metrics.csv`），并且整个 [1] 检索依赖旧 OCR 上的名字识别——OCR 把名字认错了，那页就永远进不了流水线。

---

## 3. 运行结果

### 3.1 `adept traits --taxa "Leersia hexandra" --group angiosperm`

`outputs/traits_leersia_hexandra/`（`run.json` 含命令、commit、时间、名字索引 sha256、漏斗计数）

- 漏斗：1,355 次名字出现 → 866 页 → 80 页过关键词过滤 → **13 页检出描述（25 段）**
- 输出：`traits_bhl.csv`（13 行）、`traits_combined.csv`（1 行，17 个非空性状字段）、`traits_provenance.csv`（94 条 trait/value/verbatim/页面 URL）
- eFloras：403 → "No results"，任务状态 DONE；EcoFlora：没有该物种（它是英国植物志，Leersia hexandra 不在英国，预期如此）
- 日志里有很多 `Error parsing range "4.5-- 9.5 cm"` 一类的错误：OCR 或排版造成的双连字符，范围解析失败 → 这些测量值直接丢失（召回损失，不是错误值）
- 用时：2 分 23 秒（CPU，4 核）

### 3.2 `adept descriptions --taxa "Achillea millefolium"`

`outputs/descriptions_achillea_millefolium/`（`descriptions.csv` 是 ADEPT 的输出；`run.json` 有漏斗）

- 漏斗：11,864 次名字出现（物种名 + 67 个 WorldFlora 异名）→ 10,274 页 → 334 页过关键词过滤 → **38 页检出描述**；EcoFlora 1 条；eFloras 403。
- 用时 15 分 13 秒（CPU）；luigi 调度了 10,284 个任务，汇总仍然是 "This progress looks :)"。
- 我对 38 条 BHL 描述的**人工浏览**（不是金标准，只是检查）：
  - 文本确实都是形态描述（精确率看起来很高）。
  - **11/38 只匹配到异名**，没有出现 "millefolium"：例如 *Achillea borealis*、*A. setacea*、*A. eradiata*、*A. subalpina*。
    这些在 WorldFlora 里被并入 *A. millefolium*，但历史作者把它们当作不同的种来描述。这正是**实体解析**层的问题：名字匹配 ≠ 指的是同一个分类概念。
  - **重复**：按前 60 个字母去重后只有 26 种不同文本。同一段 Gray's Manual 文字 "1. A. millefolium, L. Stems (1° high) simple…" 出现在 5 个页面（不同版本/重印），每次 OCR 错误不同（"bipinnatifld"、"corynd)s"、"1° lilj^h"）。
    → 对 BioEvidenceBench 是个**白送的自然实验**：同一段文字、不同 OCR 噪声。
  - 有 1 条（page 8010590）几乎全是 OCR 乱码，但仍被判为描述。
- 注意：`adept descriptions` 的输出文件名是固定的 `bhl.descriptions.csv`，不含物种名，第二次运行会覆盖。

---

## 4. 每一级是怎么评估的（以及我们能否复现）

### 4.1 描述分类器 —— 可以完全复现

- 数据：`adept/data/assets/train-classifier.csv`，5,960 段，818 正例（13.7%）。
- 切分：`train/classifier/scripts/convert.py`，`train_test_split(test_size=0.2, random_state=0, stratify=is_desc)`。
  我们重新切分，**和仓库里的 `train/classifier/corpus/test.spacy` 逐条、同顺序完全一致**（1,192 段，164 正例）。
- 结果（`outputs/classifier_eval/`）：

| 阈值 | TP | FN | FP | TN | P | R | F1 |
|---|---|---|---|---|---|---|---|
| 0.5 | 151 | 13 | 14 | 1,014 | 0.915 | 0.921 | 0.918 |
| **0.9（ADEPT 运行时）** | 147 | 17 | 11 | 1,017 | 0.930 | 0.896 | 0.913 |

  - 幻灯片的 151/13/14/1,014 = 阈值在 0.483–0.542 之间（实际上就是 argmax/0.5）。
  - HF meta.json 的 P/R = 阈值 0.9（spaCy 的 textcat scorer 用组件配置里的 threshold=0.9）。
  - 两个发布数字都对，但**描述的是不同的工作点**；生产里用的是 0.9，比幻灯片多漏 4 段。
- 我们发现的评估问题：
  1. **测试集同时被当作开发集**：`train/classifier/project.yml` 的 train 命令是 `--paths.dev ${vars.file.spacy.test}`，spaCy 用它挑 `model-best`。所以这个"测试"分数有乐观偏差。
  2. **重复/泄漏**：CSV 里有 213 条完全重复的文本；1,192 条测试文本中有 **64 条**也出现在训练集里。
  3. 测试集是"段落"粒度、分布是训练数据的分布；**没有**在真实 BHL OCR 流水线输入上（经过 TaxoNERD 切段、名字匹配后）的端到端召回评估。
  4. 只有一个切分、没有置信区间。164 个正例时，召回 0.92 的 95% 区间大约是 ±0.04。

### 4.2 数值/测量 NER —— 可以复现，发现发布的是验证集分数

- 先澄清：README 把 `en_adept_ner_trf` 叫 "Taxonomic named-entity recognition model"，但它的标签是
  `MEASUREMENT, DIMENSION, CARDINAL, NUMERIC_CADJ`——**它是测量/数值 NER，不是分类单元 NER**。分类单元识别用的是第三方 TaxoNERD。（任务说明里"taxonomic NER"的说法来自 README，应更正。）
- 数据：`adept/data/assets/train-numeric.json`，6,843 句；`train/ner/scripts/convert.py` 70/15/15 分层切分（random_state=0）。我们重切分和仓库里的 train/val/test `.spacy` 完全一致。
- 结果（`outputs/ner_eval/summary.json`，spaCy 自带 scorer）：

| 切分 | P | R | F |
|---|---|---|---|
| val（1,027 句） | **0.9736** | **0.9758** | **0.9747** ← 和模型卡完全一样 |
| test（1,026 句，1,300 个实体） | 0.9589 | 0.9692 | 0.9640 |

  - 模型卡（meta.json `performance`）报的是 **spaCy 训练时在 dev（val）集上的分数**，不是留出测试集。这是 spaCy 打包的默认行为，很容易被误读。
  - test/val 各有 41/38 句与训练集完全相同。
  - 这些句子是预先挑好的描述句，**不含 OCR 噪声**的评估 **[推断：抽查样例都是干净文本]**。

### 4.3 性状抽取 —— 可以复现，但是开发集

- `notebooks/adept_evaluation/`：50 条描述（49 个物种；BHL 3、eFloras 35、EcoFlora 12），81 个性状字段，人工参考答案 vs 系统输出。
  我们原样执行 notebook 的校验/匹配/打分单元（只把作者本机路径换成仓库里的 CSV；CSV 的 sha256 与 `results/evaluation_settings.json` 一致）：
  **micro P=0.905, R=0.832, F1=0.867**，逐字段表也完全相同（`outputs/traits_eval/comparison.json`）。
- 值得学的地方：
  - 匹配规则写得非常明确：小写、去空格、逗号拆分去重；**不合并同义词、不做模糊匹配、不给数值容差**；单位冲突直接报错。
  - 对齐用唯一 key（taxon|source|page），**不按行号**；缺 key/多 key/重复 key 直接停止。
  - 自动导出 `discrepancies.csv`（每个错的单元格的多出值/漏掉值）——这就是错误分析的原材料。
  - 作者在 README 和 notebook 里**主动声明**："这是开发材料上的评估，不是留出测试"，而且 4 个看不清的单元格被当作负例。
- 局限：只有 3 条 BHL 描述，其余 47 条来自现代植物志 → **这个 0.867 基本不代表 BHL OCR 上的表现**。

### 4.4 没有被评估的环节（缺什么）

| 环节 | 有没有评估数据 | 缺什么 |
|---|---|---|
| [1] 名字索引检索 | 没有 | 一个"哪些页确实描述了这个物种"的金标准页列表 |
| [3] 关键词过滤（15 词 / 2,500 字符） | 没有 | 过滤掉的 786 页（Leersia）里有没有描述？ |
| [4]–[5] TaxoNERD + 段落切分 + 名字匹配 | 没有 | 段落边界的金标准；TaxoNERD 在旧 OCR 上的召回 |
| [6] 分类器在真实 OCR 段落上 | 没有（只有 CSV 测试集） | 流水线内的段落级标注 |
| 端到端（物种 → 性状矩阵） | 50 条开发集，大部分不是 BHL | 一个留出的、以 BHL 为主的测试集 |
| OCR 质量的影响 | 没有 | 同一页的旧 OCR vs Tesseract vs 人工转录对照（**这正是 BioEvidenceBench 的 RQ1**） |
| ADEPT 论文 | 没找到 | README 说"accompanies the ADEPT research paper"，但没有链接，Citation 一节写 "once published"。我搜索后没找到已发表版本 **[未核实]**。 |

---

## 5. PCAS 植物学外部案例（可选步骤 6）

**找到的条目**（BHL 元数据，S3 导出 2026-06-06）：TitleID 12931 "Proceedings of the California Academy of Sciences. 3rd ser., Botany"；
v.1 (1897–1900) 有两份扫描：ItemID **48989**（`proceedingsof01cali`，CopyrightStatus = NOT_IN_COPYRIGHT）和 ItemID 87048（`s3botproceedings01cali`，版权状态"Not provided"）。
我们用 48989（574 页，全部从 S3 取到 OCR）。Eastwood (1898) "Studies in the herbarium and the field No. 2" 从 seq 113（PCAS 第 89 页）开始，第一节就是 "Notes on the plants of San Nicolas Island"。

**选了 5 页**（`scripts/run_pcas_pages.py`，没有金标准）：

| PageID | 内容 | ADEPT 结果 |
|---|---|---|
| 13793662 (p.94) | San Nicolas 禾本科名录（短条目） | 没有 >50 token 的段落 → 无描述（符合预期） |
| 13793669 (p.101) | San Nicolas 名录 + *Medicago sativa* 的一段岛屿型描述 | 检出 1 段，归给 *Medicago sativa*（✔ 归属正确），10 个性状字段 |
| 13793689 (p.121) | 新种 *Cnicus bipinnatus* sp. nov. 与 *C. diffusus* sp. nov. | 检出 *C. bipinnatus* 的描述，但**归给了 "Cnicus Drummondii"**（因为上一行是 "Cnicus Drummondii var. bipinnatus Eastwood"，段落归属取最近的名字行）；*C. diffusus* 的描述以 "Similar to the above…" 开头，分类器只给 0.045 → **漏掉**（比较式描述） |
| 13793690 (p.122) | *C. diffusus* 续 + *Cnicus hesperius* sp. nov. | 检出 *C. hesperius*（✔），22 个字段；*C. diffusus* 续段得分 0.976，但没有可匹配的名字，所以没被收 |
| 13793698 (p.130) | *Eriodictyon* 新种描述 | 检出，名字带着逗号 "Eriodictyon niveum,"（名字规范化问题），28 个字段 |

**重要观察：推断出来的性状**。每条描述都输出 `habitat = terrestrial`、`habit = erect leafy`、`clonality = solitary plant`、`perennial organ = stem`，而 `verbatim` 只是 "Stem"。
原因：性状词表 `traits.parquet` 里 term "stem" 被映射到这 4 个性状值。这是设计选择（"有茎 → 陆生、直立"），但**证据（verbatim）并不支持这个值**。
Leersia 的结果里 `habitat` 同时出现 "aquatic, terrestrial"，也是这个规则造成的。
→ 对 BioEvidenceBench：要区分"原文陈述的值"和"由规则推断的值"；verbatim/引用存在 ≠ 值有依据（我们的 *unsupported claim rate* 正是测这个）。

（PCAS 是 Cal Academy 的公开出版物，这里只用了 BHL 的公开 OCR，没有使用任何 Cal Academy 内部数据。）

---

## 6. BioEvidenceBench 应该借鉴的 8 件事

1. **报告分数时写清楚"切分 + 阈值 + 是否等于生产配置"。** ADEPT 的两个模型分数都能复现到小数点后 4 位，但一个是 dev 分数、一个不是运行时阈值。我们的 `PREREGISTRATION.md` 应该为每个指标写明：哪个 split（dev / locked test）、哪个阈值、哪个 prompt 版本。
2. **在锁定测试集上做模型选择是最常见的泄漏。** ADEPT 的分类器用 test 当 dev 挑 checkpoint。我们已经有 `data/sample_split.csv` 和 sealed outputs，要坚持：prompt、检查规则、阈值只在 dev 上调。
3. **做去重/泄漏检查，并写进报告。** ADEPT 测试集 5% 的文本在训练集里出现过。我们的对应风险是**预训练污染**（BHL、IMPACT 转录都是公开的）——用 CLAUDE.md 已计划的"公开披露"处理，最好再加一个简单探针（例如让模型续写一段转录，看是否逐字背出）。
4. **把"错误"和"空结果"在数据结构上区分开。** eFloras 403 → "No results" → 绿色笑脸。我们每条抽取结果应该有状态字段：`ok / empty / api_error / parse_error / unaligned`，并且在汇总里单独计数（我们已经有 unaligned 和 silent correction 的设计，这里推广到所有失败）。
5. **漏斗的每一级都要有召回评估，而不只是最后一级。** ADEPT 866 → 80 → 13，只有中间一个分类器有分数。BioEvidenceBench 的"OCR 是不是瓶颈"问题本质上就是问漏斗里哪一级丢得最多——要分别测 OCR 后的**实体保留率**、抽取召回、证据定位成功率，而不只是最终 F1。
6. **学他们的打分 notebook：严格、明确、可审计。** 唯一 key 对齐、显式的归一化规则、不做模糊匹配（或者把 lenient 作为单独一列）、自动导出 discrepancies、记录输入文件 sha256。我们的 scorer 应该照这个标准输出同样的 `evaluation_settings.json` 和 `discrepancies.csv`。
7. **出处粒度：ADEPT 停在"页面 + verbatim 词"（我们的 Level 1 + 部分 Level 2），而且 verbatim 不等于证据。** provenance 表有 `verbatim` 和页面 URL，但没有字符位置；更关键的是 "Stem" 这个 verbatim 会产出 `habitat = terrestrial`（§5）。我们的 G1（行号 + 原文引用 → 代码切片）要再加一条检查：引用的文字是否**真的支持**这个字段值（区分"陈述"和"推断"）。
8. **"开发集 vs 测试集"要诚实地写在结果旁边，而且要说明样本来源组成。** ADEPT 的 0.867 来自 50 条开发描述、只有 3 条来自 BHL。我们按书分开报告（Butler / Reeve），PCAS 单独报告——同一个原则。

额外的工程教训：固定 commit、固定模型 revision、记录 lock 文件；警惕**数据格式漂移**（OCR 导出的文件名在两个版本间变了，ADEPT 的资产脚本就失效了）；不要让两个模型共享一个缓存目录。

---

## 7. 文件索引

| 路径 | 内容 |
|---|---|
| `scripts/build_bhl_names_index.py` | 用 DuckDB 重建 ADEPT 名字索引（全量 + 查询子集） |
| `scripts/fetch_s3_ocr.py` | 从 BHL S3 拉页面 OCR 放进 ADEPT 本地归档（只改名） |
| `scripts/eval_classifier.py` | 描述分类器混淆矩阵、阈值扫描、切分一致性、泄漏检查 |
| `scripts/eval_ner.py` | 测量 NER 在 val/test 上的分数、切分一致性 |
| `scripts/eval_traits.py` | 原样执行 ADEPT 性状评估 notebook 并与其结果比对 |
| `scripts/export_run.py` | 把一次 CLI 运行的小输出 + run.json（命令、commit、时间、漏斗）导出 |
| `scripts/run_pcas_pages.py` | PCAS 页面上跑 ADEPT 描述检测 + 性状抽取 |
| `patches/0001-add-missing-adept-bhl-ocr-stub.patch` | 唯一的 ADEPT 代码改动（缺失模块的桩） |
| `outputs/classifier_eval/`, `outputs/ner_eval/`, `outputs/traits_eval/` | 三个评估复现 |
| `outputs/traits_leersia_hexandra/`, `outputs/descriptions_achillea_millefolium/` | 两个 README 例子 |
| `outputs/pcas/` | PCAS 外部案例（无金标准） |
| `outputs/s3_fetch/` | 每个从 S3 拉取的页面（PageID、S3 key、字节数、sha256） |
| `outputs/rights_check.csv`, `scripts/redact_texts.py` | 提交前的版权检查：51 个来源页中 16 个是 "In copyright"（CC BY-NC-SA）或 "Not provided"，它们的描述全文和 EcoFlora 文本在提交的文件里被替换为占位符（保留页号、长度、SHA-1） |

复现步骤（命令）见 `REPRODUCE.md`。

参考：ADEPT 仓库 <https://github.com/NaturalHistoryMuseum/ADEPT>；模型 <https://huggingface.co/benhartley/en_description_classifier>、<https://huggingface.co/benhartley/en_adept_ner_trf>；BHL OCR 导出 <https://doi.org/10.25573/data.21422193>；BHL 开放数据 <https://bhl-open-data.s3.amazonaws.com/README.md>；被子植物输出数据 <https://doi.org/10.5519/p3dm31kc>（未下载、未核对）。
