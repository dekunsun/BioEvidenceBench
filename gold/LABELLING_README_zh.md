# BioEvidenceBench 标注包（规范 v0.9）

## 包里有什么

| 文件 | 用途 |
|---|---|
| `ANNOTATION_GUIDE.md` | 标注规范 v0.9，中文版在文件后半部分 |
| `页面清单.csv` | 22 页的清单：顺序、页面编号、扫描图链接，最后一列可以打勾 |
| `1_开发集_6页/` | 6 页开发集的文字（专家转录），每行开头是这一行的起始字符位置 |
| `2_测试集_16页/` | 16 页测试集的文字，格式相同 |
| `表格模板/gold_mentions_gloria.csv` | **主要的标注表**：每个提及一行 |
| `表格模板/annotation_issues_gloria.csv` | 标注问题表：名字被无关文字隔开等情况（规范 2.0.3） |
| `表格模板/gold_links_gloria.csv` | 学名关联表：只做 Butler，等提及标完再做（规范第 3 节） |
| `表格模板/gold_changes.csv` | 解封之后如果要更正标签，记在这里（规范第 4 节） |

三个表格模板都只有表头，没有任何预填内容。

## 标注顺序

1. **先标 6 页开发集。** 这 6 页的模型输出已经被看过，用来写过规范，所以不算"盲标"。先标它们有两个用处：熟悉规范、发现规则没讲清的地方；并且有了它们，才能算开发集上的 F1 和重复运行的波动。
2. **规范如果要改，在这一步改完。** 遇到规则没覆盖的情况，按最佳判断标，在 `notes` 里写 `UNCLEAR:` 加原因。标完开发集后把这些情况发给 Claude，统一补进规范。
3. **再标 16 页测试集。** 每一页先自己独立标完并把文件发给 Claude 存档，之后才可以和 AI 助手或别人的标签对比；对比引起的每一处改动都要记录（规范第 4 节）。 测试页必须在看到任何模型输出之前标完。测试页还没有用新提示词跑过模型，旧的输出是封存的，不要打开 `results/` 下的 `sealed/` 文件。
4. **请一位朋友独立标 5 页测试页**（建议：Butler 8992379、8992643；Reeve 8966802、8967281、8967290），不看你的标签。
5. **Butler 的学名关联**（`gold_links_gloria.csv`）放在提及全部定稿之后。 评分脚本（`src/link_taxa.py`）要求每行都填 `printed_rank`；`resolution_status` 为 `resolved` 的行必须填 `accepted_usage_key`，否则脚本会停下来提示。`evidence_source` 请如实填：如果一个判断只靠在 gbif.org 上查到，就填 `GBIF`；另外查过 Avibase 或 IOC 就填它们。因为被评的关联方法本身就是查 GBIF，只靠 GBIF 定的金标准会让一致率偏高，报告里会按这一列分开列出。

## 每一页怎么标

1. 打开这一页的文字文件，同时打开 `页面清单.csv` 里的扫描图链接对照版式。
2. 在 `gold_mentions_gloria.csv` 里每个提及写一行。六种字段：`taxon`（学名）、`vernacular`（俗名）、`person`（人）、`locality`（地点）、`institution`（机构）、`date`（事件日期）。
3. **位置可以不填。** 只填 `page_id`、`field` 和 `text`（从文字文件里原样复制，不要改拼写），`start` 和 `end` 留空。检查脚本会自动算位置：这段文字在页面上只出现一次时直接给出位置；出现多次时会列出所有位置让你选。
   如果想自己填：位置 = 这一行开头的数字 + 这个词在行内的列号（从 0 开始数）。
4. 一页上一个提及都没有时，也写一行：`field` 填 `none`。
5. `guide_version` 填 `v0.9`（已经按更早版本标好的行不用改）。发现转录文件和扫描图不一致时：`text` 照转录文件抄，扫描图上的读法填进 `scan_text`，备注写 `TRANSCRIPTION-ERROR`。
6. 标完一页，在 `页面清单.csv` 最后一列打个勾。

## 标完以后

把填好的 CSV 发给 Claude（或放进仓库的 `gold/` 文件夹）。Claude 运行 `python src/check_gold.py gold/gold_mentions_gloria.csv` 检查位置和字段名，结果写在旁边的 `.checked.csv` 里，不会改你的文件。

## 几条最容易出错的规则

- 片段末尾的句点：缩写后面保留（`Linn.`），完整的词后面去掉（`Mus. Cuming`）。
- 头衔不算进人名：`Lord Lilford` 标 `Lilford`。
- `near Dover`：片段是 `Dover`，`near` 填进 `qualifier` 列。`valley of the Amoor` 整个算地点。
- 条目开头的标题要标；每页重复的页眉、`PLATE XLV.` 这种图版编号不标。
- 引用里的年份（`Pro. Zool. Soc., 1846`）不是 `date`；但 `PFEIFFER` 要标成 `person`。
- 跨行断开的名字标成一个片段；中间夹了别的文字的，不标，记到 `annotation_issues_gloria.csv`。
