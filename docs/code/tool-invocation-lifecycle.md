# 工具调用链路

本文记录 DeepSeek Harness 中一次工具调用从注册到回灌的完整链路，以及工具缺失时的行为和模型侧的输出约束。分析基线为 commit [`4b399c39`](https://github.com/deepseek-ai/deepseek-harness/tree/4b399c39a6d1479cd84ca591b4d7c88e24d38a96)，版本 `0.2.3-alpha.2`。

源码落点链接到上游仓库固定 commit 的对应行，行号锁定在基线上。源码不在本库内，按[基线记录](../../meta/sources.md)的 commit 可复现。

## 链路总览

![工具调用链路的五个关键问题](tool-lifecycle-five-questions.png)

| 环节 | 机制 | 源码落点 |
|---|---|---|
| 注册 | 插件在 `apply(ctx)` 中注册，卸载即注销 | [`docs/cookbook/adding-a-tool.zh.md:18-39`](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/docs/cookbook/adding-a-tool.zh.md#L18-L39) |
| 清单 | 每步解析工具集，组装进系统提示词 | [`agent-loop/src/agent.ts:295-297`](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/core/agent-loop/src/agent.ts#L295-L297) |
| 闸门 | `pre-execute` waterfall 裁决，失败关闭 | [`tools/src/events.ts:14`](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/core/tools/src/events.ts#L14) |
| 执行 | 并行池加屏障，上限 10 路 | [`tools/src/batch.ts:3`](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/core/tools/src/batch.ts#L3)、[`constants.ts:5`](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/core/agent-loop/src/constants.ts#L5) |
| 回灌 | `request-error` waterfall 决定是否重试 | [`agent-loop/src/agent.ts:542-552`](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/core/agent-loop/src/agent.ts#L542-L552) |
| 延续 | 压缩与可重放日志 | [`docs/subsystems/compaction.zh.md`](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/docs/subsystems/compaction.zh.md)、[`tools/src/batch.ts:5`](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/core/tools/src/batch.ts#L5) |

链路上的钩子多数使用 waterfall。拦截、否决和加工都需要这种派发方式，详见[事件钩子](#事件钩子)。

## 工具注册与清单组装

工具由插件贡献，内核不内置工具。每一步按以下顺序把注册表投影成模型可见的清单。

| 环节 | 源码位置 | 行为 |
|---|---|---|
| 工具定义 | [`docs/cookbook/adding-a-tool.zh.md:18-36`](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/docs/cookbook/adding-a-tool.zh.md#L18-L36) | 插件在 `apply(ctx)` 里调用 `ctx.tools.register(defineTool({...}))`，声明 name、description、parameters 和 execute。 |
| 解析工具集 | [`agent-loop/src/agent.ts:295`](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/core/agent-loop/src/agent.ts#L295) | `tools.resolve({ agent, modelSelection, signal })` 返回当前可用的 `ResolvedToolSet`。 |
| 清单进提示词 | [`agent-loop/src/agent.ts:297`](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/core/agent-loop/src/agent.ts#L297) | `systemPrompt.assemble({..., toolSet})` 把工具 schema 写进系统提示词。 |
| 模型返回调用 | [`agent-loop/src/agent.ts:576`](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/core/agent-loop/src/agent.ts#L576) | 模型产出 `block.type === 'tool-call'` 的内容块。 |
| 执行 | [`agent-loop/src/agent.ts:578-583`](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/core/agent-loop/src/agent.ts#L578-L583) | `tools.execute({ calls: toolCalls, ... })` 按名字找到对应的 `execute` 函数。 |
| 结果回灌 | [`agent-loop/src/agent.ts:584-586`](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/core/agent-loop/src/agent.ts#L584-L586) | 结果写入 `next-step` inbox，循环回到模型。 |

两个细节影响工具的实际可用性。`description` 是模型选择工具的依据，上游文档称其为 "what the model sees"（[`adding-a-tool.zh.md:20`](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/docs/cookbook/adding-a-tool.zh.md#L20)）。工具名不参与模型的判断。注册是副作用，dispose 插件 fiber 即注销该工具（[`adding-a-tool.zh.md:39`](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/docs/cookbook/adding-a-tool.zh.md#L39)）。

工具包按能力命名。部分包包括 `tool-bash`、`tool-web`、`tool-fs`、`tool-lsp`、`tool-office` 和 `tool-todo`。加载哪个包，模型就多哪种能力。

## 工具缺失的三种情况

三种缺失对应不同的处理方和不同的行为。

| 缺什么 | 处理方 | 行为 |
|---|---|---|
| 缺某个具体能力 | 部署方加载工具插件 | 模型在提示词里看不到该工具，正常情况下不会请求调用。 |
| 工具已注册但没有执行器 | 部署配置 | [`tools/src/index.ts:358-367`](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/core/tools/src/index.ts#L358-L367) 的 `selectExecutor()` 抛 `ToolExecutorUnavailableError`，模型没有机会请求。 |
| 模型请求不存在的工具 | 模型自行纠正 | [`pipeline.ts:278,534,603`](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/core/tools/src/pipeline.ts#L278) 抛 `ToolNotFoundError`，code 为 `UNKNOWN_TOOL`（[`contracts.ts:292-307`](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/core/tools/src/contracts.ts#L292-L307)），作为结构化 `tool/result` 回灌。 |

第三种走正常回灌通道（[`agent.ts:584-586`](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/core/agent-loop/src/agent.ts#L584-L586)）进入 `next-step` inbox。模型在下一轮看到 unknown tool 的结果，可以改用现有工具或改用文本回答。错误也是一种数据，同样驱动下一轮。

执行器的选择有意保持不可用状态。`tools/src/index.ts:347` 的注释说明，卸载执行器后保留不可用的选择，不让程序落到另一个执行器上，避免工具看似能调用但运行在错误后端。模型无法自愈这种配置问题。

## 模型侧的输出约束

模型没有申请工具的动作。它的输出只有文本和清单内工具的 tool-call 两种。它不能创建新工具，也不能执行清单外的函数。

用户请求查天气但清单里没有天气工具时，有以下四条路径。

1. 用文本回答。模型说明自己无法获取实时天气。文本中没有 tool-call，第 3 讲的完成判定（[`agent.ts:576-577`](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/core/agent-loop/src/agent.ts#L576-L577)）记为 `completed`。这是最常见的结果。
2. 用现有工具间接满足。清单里有 `web_search` 时，模型可能用它搜索天气。模型读 description 判断能力，不依赖工具名。
3. 请求不存在的工具。框架回灌 `UNKNOWN_TOOL`，模型在下一轮纠正。这属于少数情况。
4. 执行器缺失。框架在 dispatch 前抛错，模型没有决策机会。

约束来自两侧。模型只看得到提示词里的工具 schema，提供方在每次组装时求值（[`system-prompt/README.zh.md:99-101`](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/core/system-prompt/README.zh.md#L99-L101)）。模型只能输出文本或清单内的 tool-call，没有第三种输出能表达添加工具的请求。

模型卡在重复调用时，`repeat-tool-reminder` 插件（[`packages/guard/repeat-tool-reminder/README.md:12,32`](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/guard/repeat-tool-reminder/README.md#L12)）在连续重复 3 次、5 次和 8 次时插入提醒，请模型检查上次结果、换方法或收尾。提醒是建议性的，不阻断合法重复调用。第 3 讲的取消是硬性中断，两者都不替模型决策。

## 工具的定位方式

本地源码和运行时使用不同的定位方式。

查本地源码按三层顺序。先查[工具目录](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/docs/tool-catalog.zh.md)。这张表由生成器启动每个工具插件、读取 `ctx.tools.schemas()` 得到（`:3-9`），并有 glob 匹配 `packages/*/tool-*` 的完整性守卫，漏一个包就构建失败。再按 `tool-<能力>` 的命名进目录，联网搜索在 `packages/web/tool-web/`，文件读写在 `packages/fs/tool-fs/`，命令行在 `packages/shell/tool-bash/`。最后用全文搜索兜底，搜 `fetch|search|http` 这类能力词，不猜工具名。本次基线中搜索 `weather|天气`，产品工具零命中，只有 examples 里的 `token-weather` 演示插件。

运行时不检索工具。每步 `tools.resolve()` 解析工具集，`systemPrompt.assemble()` 把清单全量写进提示词，模型读 description 自行判断。schema token 在每次请求中重复（[`system-prompt/README.zh.md:189-193`](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/core/system-prompt/README.zh.md#L189-L193)）。检索只发生在专门的元数据工具上。

| 工具 | 检索对象 | 工具目录位置 |
|---|---|---|
| `cordis_inspect` | 运行时的 provider 和方法 | [`docs/tool-catalog.zh.md:34`](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/docs/tool-catalog.zh.md#L34) |
| `plugin_market` | 可安装的插件 | [`docs/tool-catalog.zh.md:24`](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/docs/tool-catalog.zh.md#L24) |
| `glob`、`grep` | 文件系统里的文件和内容 | [`docs/tool-catalog.zh.md:39`](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/docs/tool-catalog.zh.md#L39) |
| `session_event_search`、`session_search` | 历史事件和会话 | [`docs/tool-catalog.zh.md:48`](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/docs/tool-catalog.zh.md#L48) |

`cordis_inspect` 查系统已有的能力，`plugin_market` 查还能安装的能力。模型先查目录，再决定是否安装插件，工具在插件安装后才进入提示词。

## 执行与调度

一次返回多个 tool-call 时，调度器按两种模式分流（[`tools/src/batch.ts:3`](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/core/tools/src/batch.ts#L3)）。`parallel` 调用进入有界滚动池，`exclusive` 调用作为屏障，必须等当前池排空才开始。默认上限为 10 路并发，常量为 `DEFAULT_MAX_PARALLEL_TOOL_CALLS`（[`agent-loop/src/constants.ts:5`](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/core/agent-loop/src/constants.ts#L5)）。

三个细节决定调度行为。执行可以乱序，结果按模型顺序提交（[`batch.ts:4`](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/core/tools/src/batch.ts#L4)）。每个调用启动前重新判定模式（[`batch.ts:76`](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/core/tools/src/batch.ts#L76)），注册表在半路修改策略会影响尚未启动的调用。取消时停止新启动、排空已启动的调用，并为被跳过的调用写入合成错误结果（[`batch.ts:5-7`](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/core/tools/src/batch.ts#L5-L7)），使 replay 保持有效。

## 事件钩子

工具执行路径暴露三条 waterfall 钩子（[`tools/src/events.ts`](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/core/tools/src/events.ts)）。

| 事件 | 位置 | 作用 |
|---|---|---|
| `tools/pre-execute` | [`events.ts:14`](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/core/tools/src/events.ts#L14) | dispatch 前裁决 allow、deny、cancel 或 ask。 |
| `tools/execute` | [`events.ts:20`](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/core/tools/src/events.ts#L20) | 围绕 dispatch 的瀑布，用于 timeout、retry 和 metrics。 |
| `tools/post-execute` | [`events.ts:30`](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/core/tools/src/events.ts#L30) 起 | 接受、替换、加工或阻断归一化后的结果。 |

审批走 `approval/request` waterfall，应答者可以是 UI 通道或 ACP 自动化桥接。`ApprovalOutcome` 有 `allowed-once`、`rejected`、`cancelled` 和 `unavailable` 四种，其中只有 `allowed-once` 放行，且只授权当次操作。缺失的应答者、不负责该请求的应答者和抛异常的应答者都产生 `unavailable`。会话级策略 `never` 确定性拒绝所有请求，用于无人值守场景（[`docs/subsystems/approval.zh.md`](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/docs/subsystems/approval.zh.md)）。

`approval/request` 使用 waterfall 而非 serial，因为需要第一个能给出裁决的应答者认领，后续应答者仍可加工或否决。

## 失败、压缩与重放

模型请求失败不触发内置重试。[`agent.ts:542`](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/core/agent-loop/src/agent.ts#L542) 抛 `agent/request-error` waterfall。插件返回 `{ kind: 'retry' }` 时循环 `continue` 重跑这一步（[`agent.ts:550-552`](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/core/agent-loop/src/agent.ts#L550-L552)），否则转成 `LlmError` 抛出。重试策略由插件提供，循环本身不实现它。

上下文过长由压缩 seam 处理，包为 `packages/compaction/`。上游文档将其标记为可选能力，不属于 agent loop 主干。压缩分为 Service Definition（`ctx.compaction`）、Service Provider（如 `compaction-basic` 后端）和 Consumer（如 `command-compact`）三段。`compaction/start`、`compaction/summary` 和 `compaction/end` 三个事件只写日志。真正进入模型上下文的是一条带 `surfaceOp: replace` 的 `user/message`，摘要替换掉被遮蔽的历史区间（[`docs/subsystems/compaction.zh.md`](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/docs/subsystems/compaction.zh.md)）。锁覆盖整个操作，中途崩溃留下有 start 无 end 的遗留锁，可被检测。

取消或崩溃后的重放不会重复执行工具。abort 时给被跳过的调用写入合成错误结果（[`batch.ts:5-7`](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/core/tools/src/batch.ts#L5-L7)），重放时每个调用都有确定结果。第 3 讲的 durable 日志在每次 claim 和每个 turn 或 step 边界写盘。状态不存快照，靠日志重算。

## 上游做法与约束

下表记录上游在各环节的做法和相应约束，供平台设计时对照。

| 环节 | 上游做法 | 约束 |
|---|---|---|
| 工具接入 | 插件注册，卸载自动注销 | 能力可独立装卸，模型每步看到实时清单。 |
| 多个调用 | 并行池加屏障，按模型顺序回结果 | 有并发上限。结果顺序稳定，模型不会错乱。 |
| 危险操作 | waterfall 裁决，失败关闭 | 默认拒绝，不默认放行。 |
| 失败重试 | 插件决定，内核不管 | 换策略不需要改循环。 |
| 上下文过长 | 压缩 seam，摘要替换历史 | 可选能力，不影响简单场景。 |
| 取消恢复 | 日志加合成结果，可重放 | 崩溃和取消共用可重放语义。 |

五种事件派发在工具链路上都有落点。`emit` 用于通知，`parallel` 用于汇总，`serial` 用于顺序认领，`bail` 用于同步短路，`waterfall` 用于拦截和加工。工具链路出现频率最高的是最后一种。

## 事实边界

- 源码行号来自 commit `4b399c39`。压缩与审批部分依据子系统文档和源码注释，设计意图类表述未逐行追踪全部执行分支。
- 工具目录的包数量为本次基线的实测统计，随上游版本变化。
- 没有产品级天气工具是本次基线的检索结论，不排除后续版本新增。
- 教学用的 mini-harness 不含真实工具执行链路。第 3 讲的 `weather`、`map` 和 `fx` 是脚本中的占位符，用来演示循环转动。
- 配图是脱敏后的技术示意图，只含机制名称和源码文件名。
