# PCAS 植物学外部案例：标注说明

**这 8 页还没有跑过任何模型。** 请先标完、发回，我存档以后才跑模型（和测试集一样的规矩）。

## 是什么

Alice Eastwood (1898), *Studies in the Herbarium and the Field, No. 2*, 第一部分"Notes on the Plants of San
Nicolas Island"。来自 Proceedings of the California Academy of Sciences, 3rd series, Botany, vol. 1
（BHL 条目 48989，纽约植物园藏本，NOT_IN_COPYRIGHT）。全是公开数据，与 Cal Academy 内部数据无关。

这个案例只回答一个问题：主实验（鸟类、贝类）的结论，换到植物学文献上还成不成立。结果单独报告，不和主实验合并。

## 8 页

见 `pcas_pages.csv`：印刷页码 90、91、92（叙述）和 94、96、100、106、112（物种名录）。每页的 `bhl_url` 打开就是扫描图。

## 怎么标

这几页**没有专家转录**，所以和主实验不同：

1. **对着扫描图标**，不要对着 OCR 文字标（`legacy/` 里的旧 OCR 只是参考，错字很多）。
2. 表格只有四列：`page_id`、`field`、`text`、`notes`。**`text` 写扫描图上印的样子**（保留原来的拼写、大小写、缩写，例如 `Desv.`、`STEUD.`），不用填位置。
3. 字段和规则都按规范 v0.10：`taxon`、`vernacular`、`person`、`locality`、`institution`、`date`。植物学里常见的情况：
   - 学名后面的命名人（`Bromus Trinii Desv.` 里的 `Desv.`）是一个单独的 `person`，学名是 `Bromus Trinii`。
   - 编号（`1.`、`2.`）不算。
   - 科名标题（`GRAMINEÆ.`）是 `taxon`。
   - 岛名（`San Nicolas`、`Santa Cruz Island`）是 `locality`。
4. 拿不准的写 `UNCLEAR:` 加原因，和之前一样。

空白模板：`gold/gold_mentions_pcas_TEMPLATE.csv`。标完把文件发回即可。

## 标完以后跑什么

旧 OCR 上的 G1（冻结的提示词）、旧 OCR 上的 G2（LLM 读正）、直接读扫描图的 V1。按值比较（这几页没有专家转录，没有位置）。预计花费不到 1 美元。
