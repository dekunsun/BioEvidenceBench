# 手绘植物插图：特征清单（草稿，待作者确认）

用途：大英图书馆两件资料（Or 7364《本草綱目》植物名錄；IOR/H/375 pp. 243–61 Hemp and flax plants）里的手绘图，
作为「证据分步给出」案例中的一层证据。探索性，单独报告，不并入两本英文书的结果。

原则：

- 标注者记录**图上看得见的东西**，不做物种鉴定；鉴定交给植物学专家，未确认的标 `expert_pending`。
- 先由作者独立标注并存档，之后才让模型按同一清单填写（与金标准规则相同）。
- 看不清或图上没有画的，填 `not_shown`，不要猜。
- 照片在使用许可确认之前不进仓库。

## A. 图与文字的对应（不需要植物学知识）

| 字段 | 取值 | 说明 |
| --- | --- | --- |
| `item` | `Or7364` / `IOR_H_375` | 馆藏 |
| `folio` | 如 `f012r`、`p255` | 图所在页 |
| `figure_id` | 图上的编号或字母，没有则 `none` | |
| `caption_text` | 图上的题字或图注，逐字照录 | 看不清的字用 `□` |
| `linked_entry` | 对应正文条目的页码和名称 | 依据写在 `link_evidence` |
| `link_evidence` | `figure_number` / `caption` / `text_reference` / `position_only` / `none` | 凭什么判断对应关系 |
| `same_hand` | `yes` / `no` / `unsure` | 图注与正文是否同一笔迹、同一种墨 |

## B. 看得见的形态特征

| 字段 | 取值 |
| --- | --- |
| `habit` | `herb` / `shrub` / `tree` / `climber` / `not_shown` |
| `leaf_type` | `simple` / `compound` / `not_shown` |
| `compound_kind` | `palmate` / `pinnate` / `trifoliate` / `n/a` / `not_shown` |
| `leaflet_count` | 数字或范围，如 `5-7`；不适用填 `n/a` |
| `leaf_shape` | `linear` / `lanceolate` / `ovate` / `lobed` / `other` / `not_shown` |
| `leaf_margin` | `entire` / `toothed` / `not_shown` |
| `leaf_arrangement` | `alternate` / `opposite` / `whorled` / `not_shown` |
| `flower_shown` | `yes` / `no`；有则在 `flower_notes` 简述颜色、花瓣数 |
| `fruit_or_seed_shown` | `yes` / `no`；有则在 `fruit_notes` 简述 |
| `dissection_shown` | `yes` / `no`（花或果的剖面、放大的部件） |
| `root_shown` | `yes` / `no` |
| `colour` | `ink_only` / `coloured` |
| `style` | `naturalistic` / `schematic`（写实或程式化） |

## C. 证据状态（与证据分步设计一致）

| 字段 | 取值 |
| --- | --- |
| `step` | `name` / `name+text` / `name+text+drawing` |
| `candidates` | 按当前可见证据仍说得通的候选，分号分隔 |
| `evidence_status` | `sufficient` / `ambiguous` / `conflicting` / `insufficient` / `unresolved` |
| `expected_action` | `accept` / `search_context` / `investigate` / `check_source` / `defer` |
| `notes` | 理由；标注者只按当时可见的证据判断，不用事后知道的答案 |

## 模型测试（标注存档之后）

1. 模型按 B 部分逐项填写，和作者的记录逐字段比较。
2. 遮挡探针：遮住图上的题字和标注字母后重问，看答案是否改变（检验模型是看图还是读字）。
3. 输入对比：只给图 / 只给文字 / 图加文字。
4. 不让模型在图上画框；证据区域用整幅图或人工裁剪的区域。
