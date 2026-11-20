# API 说"成功"，其实失败了：两个项目里的静默故障

*一次是 Gemini 的批处理接口悄悄丢掉了格式要求，一次是 Gemini Live 把服务端错误说成了模型的话。两次看起来都像"模型的行为"，两次都差点被当成研究结果。*

[English version below](#when-success-is-a-failure-silent-platform-failures-in-two-projects)

## 第一次：格式要求消失了（BioEvidenceBench，2026 年 11 月）

BioEvidenceBench 要求模型按固定的 JSON 格式回答：外层一个对象，里面一个叫 `mentions` 的列表，每条有字段、行号和原文引语。调用 Gemini 时，我们把这份格式说明（JSON schema）一起发过去。Google 的"结构化输出"会在生成时强制模型遵守它，正常情况下不可能出现别的形状。

为了省钱，开发集的一轮运行用了 Batch API（打包提交、排队处理，价格减半）。48 个回答里，**44 个格式不对**：只有里面的列表，没有外层对象（我们叫它"裸数组"）；另有 3 个是其他错误形状。任务状态是"成功"，每个回答的结束原因都是正常的 `STOP`，没有任何报错。

如果代码不自己检查格式，这些回答要么解析失败被当成"模型什么也没找到"，要么被悄悄丢掉。我们之所以发现，是因为每个回答都会经过代码校验（`check_shape`）。

### 怎么确认不是模型的问题

把**完全相同的请求**分两种方式发出去（`src/gemini_batch_schema_check.py`，3 个开发页）：

| 发送方式 | 格式字段 | 符合格式 | 输入 token（三页） |
|---|---|---|---|
| 同步 | `response_json_schema`（新写法） | 3 / 3 | 2981 · 3016 · 2687 |
| Batch | `response_json_schema`（新写法） | **0 / 3**（全是裸数组） | 2814 · 2849 · 2520 |
| 同步 | `response_schema`（旧写法） | 3 / 3 | 2973 · 3008 · 2679 |
| Batch | `response_schema`（旧写法） | **3 / 3** | 2973 · 3008 · 2679 |

三点：

1. 用新写法时，batch 的输入 token 每页都**正好少 167 个**，三页长短不同，差值却一样，说明少了一块固定大小的东西。
2. 换成旧写法，batch 的回答全部符合格式，输入 token 和同步完全一致。
3. SDK（google-genai 3.6.1）确实把新写法的字段放进了每个 batch 请求。

所以结论是：**Batch API 丢掉了 `response_json_schema` 这个较新的字段，旧的 `response_schema` 则正常执行。** 丢掉的具体位置在 Google 服务端，我们看不到，这一部分是推断；但"新字段在 batch 里不生效、旧字段生效"是直接测到的。两次检查一共花了约 $0.28。

## 第二次：错误说给了模型，没告诉我们（LiveLab，2026 年 9 月）

在另一个项目 [LiveLab](https://github.com/dekunsun/livelab) 里，我测试 Gemini 3.8 Live 的 Extended Thinking 版本会不会在信息不足时放弃作答。用的是免费额度。

跑了几个小时，越来越多的题目没有调用答题工具：按时间分四段，没有回答的比例是 1/12、2/12、6/12、9/12。服务端每一轮都正常结束（`generation_complete`、`turn_complete`），只是模型说了一句：

> "I apologize, but a system error occurred."

**错误被告诉了模型，没有告诉客户端。** 第一版程序把这些记成了"模型拒绝回答"。更危险的是，这个研究恰好在测"模型会不会放弃"，按旧的计分方式，这一晚的故障会被当成支持研究结论的证据。

### 怎么确认不是模型的问题

同一道题、同一个 key、同一分钟，换成标准版 `gemini-3.8-live`：1.3 秒就正常答题了。所以不是账户额度用完了，而是这个模型的这条路径出了问题。

当时的假设是"按 token 计量的配额耗尽了"，并做了登记的检验：把同一道失败的题裁到原来的六分之一，照样失败，而对照模型三道都答了。**假设被推翻，机制始终没有查清。** 开通付费后，缺的两组数据 20 分钟、约 $0.20 就收齐了。

（详见 LiveLab 的 `docs/probe_preregistration.md` 第 7 条偏差。）

## 对照：一次"我们自己没看"的失败

LiveLab 里还有一次，Claude 的回答被我们自己设的 1,024 token 上限截断，128 个回答缺了后面的字段。但这一次 API **给了信号**：`stop_reason = "max_tokens"`。是我们的程序没把它存下来。静默发生在我们这边，不在平台。

| | Gemini Batch 丢格式 | Gemini Live 错误给了模型 | Claude 被截断 |
|---|---|---|---|
| API 报告 | 正常 `STOP`，任务成功 | 正常结束，模型说"system error" | `max_tokens` |
| 看起来像 | 模型不守格式 | 模型拒绝回答 | 模型漏字段 |
| 谁该负责 | 平台 | 平台 | 我们没存结束原因 |
| 怎么发现 | 同一请求，同步对照 | 同一请求，标准模型对照 | 回答长度全部等于 1,024 |

两次平台故障都发生在**更便宜或次要的路径**上（半价的 batch、免费额度）；同样的请求走标准的付费同步路径就正常，出错时也会正常报错。这只是两个案例，不是规律。

## 学到的

1. **API 说"成功"，不等于请求按你发的样子被处理了。** 存下每次调用的完整请求、结束原因和用量。
2. **平台故障会伪装成模型行为，而且可能恰好支持你的假设。** 用代码校验每个回答；没回答和格式错误单独计数，不要算成模型的选择；每个比率旁边报告覆盖率。
3. **最有力的检验，是把同一个请求换一条路径再发一次。** 同步代替 batch，标准模型代替变体，付费代替免费。
4. **调用方式是配置的一部分。** 和模型一起冻结：SDK 版本、接口、额度类型都要记录，一次比较里不要混用。
5. **诊断本身也会扰动被测对象。** LiveLab 里第二个测试紧接着第一个开始，结果测到的是第一个测试留下的"故障窗口"。诊断之间要拉开间隔，一次只改一个变量。

---

# When "Success" Is a Failure: Silent Platform Failures in Two Projects

*Once, Gemini's batch interface quietly dropped our output format. Once, Gemini Live told the model about a server error instead of telling us. Both looked like the model's behaviour; both nearly became results.*

## One: the format requirement vanished (BioEvidenceBench, November 2026)

BioEvidenceBench asks the model to answer in a fixed JSON shape: an object holding a list called `mentions`, each item with a field, a line number and a verbatim quote. With Gemini we send that shape as a JSON schema, and Google's structured output enforces it during generation; no other shape should be possible.

To save money, one dev run used the Batch API (queued, half price). Of 48 answers, **44 had the wrong shape**: the inner list without the outer object (a "bare array"); 3 more were other wrong shapes. The job "succeeded"; every answer finished with a normal `STOP`; no error anywhere.

Without our own check, these answers would have failed to parse and been scored as "the model found nothing", or been dropped silently. We caught them because every answer goes through a shape check in code (`check_shape`).

### How we knew it was not the model

We sent **identical requests** two ways (`src/gemini_batch_schema_check.py`, 3 dev pages):

| Mode | Schema field | Followed the schema | Prompt tokens (three pages) |
|---|---|---|---|
| sync | `response_json_schema` (newer) | 3 / 3 | 2981 · 3016 · 2687 |
| batch | `response_json_schema` (newer) | **0 / 3** (all bare arrays) | 2814 · 2849 · 2520 |
| sync | `response_schema` (older) | 3 / 3 | 2973 · 3008 · 2679 |
| batch | `response_schema` (older) | **3 / 3** | 2973 · 3008 · 2679 |

Three observations:

1. With the newer field, batch prompt counts were **exactly 167 lower** on every page; the pages differ in length but the gap does not, so something of fixed size was missing.
2. With the older field, every batch answer followed the schema and the prompt counts matched sync exactly.
3. The SDK (google-genai 3.6.1) does put the newer field into each batch request.

Conclusion: **the Batch API drops the newer `response_json_schema` field; the older `response_schema` is enforced.** Where it is dropped inside Google is invisible to us, so that part is inference; that the newer field fails in batch and the older one works was measured directly. Both checks together cost about $0.28.

## Two: the error went to the model, not to us (LiveLab, September 2026)

In another project, [LiveLab](https://github.com/dekunsun/livelab), I tested whether Gemini 3.8 Live with Extended Thinking would abstain when evidence was missing. It ran on the free tier.

Over a few hours, more and more items ended with no answer-tool call: by quarter of the run, 1/12, 2/12, 6/12, 9/12. The server ended every turn normally (`generation_complete`, `turn_complete`); the model simply said:

> "I apologize, but a system error occurred."

**The error was reported to the model, not to the client.** The first version of the harness recorded these as "the model declined to answer". Worse, the study was measuring whether models abstain; scored the old way, a night of outages would have read as evidence for the study's own conclusion.

### How we knew it was not the model

Same item, same key, same minute, the standard `gemini-3.8-live` answered in 1.3 s. So it was not the account's quota but this model's path.

The working hypothesis was a token-metered quota. A registered test cut the failing item to a sixth of its length: it failed the same way, while the control answered all three. **The hypothesis was refuted, and the mechanism was never found.** With billing on, the missing data took 20 minutes and about $0.20.

(Details: LiveLab, `docs/probe_preregistration.md`, deviation 7.)

## A contrast: a failure we did not look at

In LiveLab, Claude answers were also cut off by our own 1,024-token output cap, and 128 answers lost their later fields. That time the API **did** signal it, `stop_reason = "max_tokens"`; our runner did not save it. The silence was ours, not the platform's.

| | Gemini Batch drops the format | Gemini Live tells the model | Claude is truncated |
|---|---|---|---|
| API reports | normal `STOP`, job succeeded | normal end; model says "system error" | `max_tokens` |
| Looks like | a model ignoring the format | a model declining | a model omitting fields |
| Whose failure | the platform's | the platform's | ours: the stop reason was not saved |
| Found by | same request, sync control | same request, standard-model control | every cut answer exactly 1,024 tokens |

Both platform failures happened on a **cheaper or secondary path** (half-price batch, the free tier); the same request on the standard paid synchronous path worked and raised its errors. Two cases, not a rule.

## What it taught

1. **"Success" from an API is not evidence the request was processed as sent.** Save the full request, the finish reason and the usage of every call.
2. **A platform failure can pass for model behaviour, and may even favour your hypothesis.** Validate every answer in code; count non-answers and malformed answers separately, never as the model's choice; report coverage beside every rate.
3. **The strongest test is the identical request by another path**: sync instead of batch, the standard model instead of the variant, paid instead of free.
4. **The call path is part of the configuration.** Freeze it with the model; record SDK version, endpoint and tier; do not mix paths within one comparison.
5. **Diagnostics can disturb what they measure.** In LiveLab a second test, started right after the first, measured the first one's failure window. Space diagnostics out and change one thing at a time.
