# 第 6 讲：能力 seam，换实现不改接口，怎么切

第 5 讲讲清一次工具调用经过哪些关卡。这一讲回答下一个问题。底层实现要换，比如把本地命令执行换成沙箱执行，怎么让上层的工具和模型完全不动。

先给结论。把一项能力拆成三个角色。定义约定的是一个角色，提供实现的是一个角色，使用能力的是第三个角色。三者各自独立，换实现只动中间那个。三个角色合起来才叫一个 seam。这是 DSH 处理可替换能力的基本方式，源码里有明确的笔记和范例。

## 一个能力涉及三种变化

一项可替换的能力牵涉三件事，它们变化的原因和节奏都不一样。

第一件是约定。这项能力是什么，对外承诺什么行为。比如命令执行要能跑前台命令、能拿后台句柄、能读有界输出。

第二件是实现。这件事具体怎么跑。用本机子进程跑，还是放进沙箱跑，还是发到远程跑。

第三件是消费方 API。模型看到的工具 schema，以及插件调用的入口。比如模型调用 `bash` 工具时填什么参数。

把三件事放在一个包里，它们的发布时间就被绑在一起。换一个执行实现，模型看到的工具 schema 也跟着变动，尽管面向模型的约定根本没变。这就是要拆开的原因（实测：[`2026-06-13-capability-seams.zh.md:9`](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/.agents/notes/implemented/architecture/2026-06-13-capability-seams.zh.md#L9)）。

这里要分清一个容易混的问题。Cordis 已经解决了「谁在运行时提供、谁需要」的问题，办法是服务加 `inject`。提供方注册 `ctx.shell`，消费方声明注入 `shell`，它的 fiber 会挂起直到服务出现。这个机制决定运行时怎么连，但不决定代码的包怎么分。这一讲讲的是包的边界，是另一回事（实测：[`2026-06-13-capability-seams.zh.md:11`](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/.agents/notes/implemented/architecture/2026-06-13-capability-seams.zh.md#L11)）。

## 三个角色各自是什么

DSH 把三个角色分别命名，写进架构笔记和术语表，作为全仓统一叫法（实测：[`2026-06-13-capability-seams.zh.md:15`](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/.agents/notes/implemented/architecture/2026-06-13-capability-seams.zh.md#L15)）。

| 角色 | 职责 | 在 shell 能力里 |
|---|---|---|
| Service Definition | 拥有 `ctx.<key>` 的 Cordis `Service` 和词汇类型，只依赖约定需要的类型 | `dsh-shell` 定义 `ctx.shell` 和 `ShellExecutor` |
| Service Provider | 提供或注册实现的插件 | `dsh-bash-local`、`dsh-bash-sandbox` 注册 `ctx.shell` |
| Consumer | 模型和插件编程面向的东西，注入服务键，不导入提供方特有类型 | `dsh-tool-bash` 定义 `bash` 工具 |

三个角色有四条规定。

Service Definition 是 Cordis 的 `Service`，不是 TypeScript 的 `interface`。它可以是抽象类，也可以是具体的注册表服务。约束是必须能拥有一个 `ctx.<key>` 服务键，`interface` 做不到这件事（实测：[`2026-06-13-capability-seams.zh.md:17`](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/.agents/notes/implemented/architecture/2026-06-13-capability-seams.zh.md#L17)）。

Consumer 只注入服务键，不导入提供方的类型。它依赖的是约定，不是某个具体实现（实测：[`2026-06-13-capability-seams.zh.md:19`](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/.agents/notes/implemented/architecture/2026-06-13-capability-seams.zh.md#L19)）。

Provider 和 Consumer 独立演进。换成沙箱执行器时，不用碰任何工具 schema（实测：[`2026-06-13-capability-seams.zh.md:23`](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/.agents/notes/implemented/architecture/2026-06-13-capability-seams.zh.md#L23)）。

seam 指三个角色的组合，不指其中任何一个。单个角色不是 seam。要说清楚其中一部分，就按它的角色、类、服务、约定或扩展点来叫（实测：[`2026-06-13-capability-seams.zh.md:29`](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/.agents/notes/implemented/architecture/2026-06-13-capability-seams.zh.md#L29)）。术语表把这条定为规范条目（实测：[`glossary.zh.md:7`](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/docs/glossary.zh.md#L7)）。

## shell 三件套怎么落地

shell 能力是规范范例。三个角色分在三个包里，源码可以直接对上（实测：[`packages/shell/README.zh.md:26`](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/shell/README.zh.md#L26)）。

Service Definition 是 `dsh-shell`。它声明 `Context` 上有 `shell` 这个键，并导出一整套词汇类型，`ShellExecutor`、`ShellRunResult`、`ShellProcess` 等（实测：[`shell/src/index.ts:1`](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/shell/shell/src/index.ts#L1)）。核心是一个抽象类 `ShellExecutor extends Service`，构造函数用 `super(ctx, 'shell')` 把自己挂到那个键上（实测：[`shell/src/index.ts:64`](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/shell/shell/src/index.ts#L64)）。类注释写明一个 context 只装一个实现，装第二个会按 Cordis 的标准重复服务行为在加载期报错（实测：[`shell/src/index.ts:36`](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/shell/shell/src/index.ts#L36)）。

Service Provider 是 `dsh-bash-local`。它定义 `LocalBashExecutor extends ShellExecutor`，在 POSIX 上用全新的 `bash -c` 进程跑命令（实测：[`bash-local/src/index.ts:97`](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/shell/bash-local/src/index.ts#L97)）。兄弟包 `dsh-bash-sandbox` 依据同一约定实现沙箱版，两者可互换（实测：[`packages/shell/README.zh.md:26`](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/shell/README.zh.md#L26)）。

Consumer 是 `dsh-tool-bash`。它是面向模型的 `bash` 工具，顶部声明 `inject` 包含 `tools`、`shell`、`systemPrompt` 等键（实测：[`tool-bash/src/index.ts:36`](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/shell/tool-bash/src/index.ts#L36)）。执行时用 `ctx.shell.execute(spec)` 拿结果（实测：[`tool-bash/src/index.ts:571`](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/shell/tool-bash/src/index.ts#L571)）。它注入的是 `shell` 这个键，从头到尾不 import `LocalBashExecutor`。这正是换实现不动工具的前提。

profile 层恰好选择一个执行器实现，同时挂两个会因服务重复注册而在加载期失败（实测：[`packages/shell/README.zh.md:36`](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/shell/README.zh.md#L36)）。选择权在部署方，不在工具代码里。

## 不是所有能力都要拆成三包

分工有代价。拆三个包就多三份 `package.json`、`tsconfig`、README 和注入接线。笔记给出的规则是，角色独立演进时才分开，确实属于同一个关注点时可以合并（实测：[`2026-06-13-capability-seams.zh.md:25`](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/.agents/notes/implemented/architecture/2026-06-13-capability-seams.zh.md#L25)）。

LLM 能力是合并的例子。它把 Service Definition 和 Consumer 合进 `dsh-llm`，因为 Consumer 就是 agent loop 本身，不是一个可替换的 schema 接口。各家模型服务作为 Service Provider 包接进来。笔记特别提醒不要预防性地拆分，一种实现加一个消费者就保持一个包，等第二个出现再拆（实测：[`2026-06-13-capability-seams.zh.md:25`](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/.agents/notes/implemented/architecture/2026-06-13-capability-seams.zh.md#L25)）。

还有一个易混点。Cordis 的 `@cordisjs/plugin-capability` 不是这里的机制。那是权限安全服务，用具名权限加继承，针对会话做检测，是权限和沙箱工作的候选方案。把两个「能力」搞混正是笔记点名的陷阱（实测：[`2026-06-13-capability-seams.zh.md:34`](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/.agents/notes/implemented/architecture/2026-06-13-capability-seams.zh.md#L34)）。

## 上游源码落点

本节事实来自本地源码副本（alpha.2，commit `4b399c39`）。

| 事实 | 位置 |
|---|---|
| 三件事耦合的问题陈述 | [`2026-06-13-capability-seams.zh.md:9`](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/.agents/notes/implemented/architecture/2026-06-13-capability-seams.zh.md#L9) |
| 服务加 inject 与本讲问题的区分 | 同文件 `:11` |
| 三个角色定义 | 同文件 `:15` |
| Definition 是 Service 不是 interface | 同文件 `:17` |
| Consumer 只注入服务键 | 同文件 `:19` |
| Provider 与 Consumer 独立演进 | 同文件 `:23` |
| 不预防性拆分，LLM 合并的情形 | 同文件 `:25` |
| seam 指三者组合 | 同文件 `:29` |
| 与 plugin-capability 的区分 | 同文件 `:34` |
| glossary 规范条目 | [`glossary.zh.md:7`](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/docs/glossary.zh.md#L7) |
| shell 包职责与 ctx key 表 | [`shell/README.zh.md:26`](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/shell/README.zh.md#L26) |
| 恰好选择一个执行器 | 同文件 `:36` |
| `ctx.shell` 声明与词汇类型 | [`shell/src/index.ts:1`](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/shell/shell/src/index.ts#L1) |
| `ShellExecutor extends Service` | 同文件 `:64` |
| 一个 context 只装一个实现 | 同文件 `:36` |
| `LocalBashExecutor extends ShellExecutor` | [`bash-local/src/index.ts:97`](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/shell/bash-local/src/index.ts#L97) |
| Consumer 的 inject 声明 | [`tool-bash/src/index.ts:36`](https://github.com/deepseek-ai/deepseek-harness/blob/4b399c39a6d1479cd84ca591b4d7c88e24d38a96/packages/shell/tool-bash/src/index.ts#L36) |
| Consumer 调用执行器 | 同文件 `:571` |

## 移植到骨架

本讲代码做一个最小的 seam 实现。定义一个执行器约定，挂两个实现，再写一个只依赖约定的消费方。目标是换掉实现时消费方一行不改。代码与实测见[第 6 讲实践篇](lecture-6-practice.md)，本篇先不写实践内容。

设计上保留三件事。约定是一个有服务键的抽象类，不是接口。实现方继承或注册到这个键，同一时刻只装一个。消费方只声明依赖的键，不认识具体实现。省略的是 Cordis 的 fiber 挂起与多服务键接线，骨架用一个极简的注册表模拟。

## 要不要这样做

拆 seam 的收益是有前提的。只有当一个能力确实存在多种实现，或者将来大概率会换实现时，拆开才划算。代价是多出来的包、样板文件和接线。

对比另一条路。把约定、实现和消费方写进一个模块，读写都直接，文件也少。适合只有一种实现、也没有替换计划的能力。风险是将来真要换时，改动会顺着调用链扩散到消费方。

对要建的平台，建议对命令执行、模型接入这类明显会换后端的能力保留 seam。判断标准沿用笔记那条，不要预防性拆分，等第二个实现真的出现再切。

## 动手任务

代码放在 `mini-harness/lecture-6/`，全部离线运行。下面四条任务对应的场景与输出见[第 6 讲实践篇](lecture-6-practice.md)。

1. 写一个执行器抽象类作为 Service Definition，带一个服务键和抽象方法。
2. 写两个 Service Provider 实现同一个约定，注册到服务键，确认重复注册被拒绝。
3. 写一个 Consumer，只声明依赖服务键，调用约定里的方法，确认换实现时它不用改。
4. 选做：让 Consumer 在断言里检查拿到的实现确实是约定类型，观察直接依赖具体实现会怎样破坏替换。

## 本讲小测

1. 一项可替换能力涉及哪三种变化？把它们放在一个包里会出什么问题？
2. Service Definition 为什么必须是 Cordis `Service`，不能是 TypeScript `interface`？
3. shell seam 里三个角色分别是哪个包？Consumer 凭什么能在换实现时一行不改？
4. 一个能力只有一个实现时，该不该拆成三个包？给出判断标准和理由。
5. 平台取舍题。你的 mini-harness 要接本地命令和沙箱命令两种执行器，工具 schema 只有一份。你会怎么切这几个角色，代价是什么？

批改见[第 6 讲实践篇](lecture-6-practice.md)。

## 事实边界

三个角色的定义、包边界规则、不预防性拆分、与权限能力的区分均来自本地源码副本的架构笔记与术语表，commit `4b399c39`。shell 三件套的包名、类名、服务键和行号来自同批次的包源码。要不要给某项能力拆 seam 属于设计取舍，不是源码事实。动手任务尚未执行，本篇不含实测输出。
