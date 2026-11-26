# DeepSeek Harness 学习资料库

记录 DeepSeek Harness（DSH）的产品功能、代码原理与版本演进，并保存边学边搭的 mini-harness 课程代码。研究文档与课程代码都入库，不存上游源码。

## 课程目标

课程主线是边学边搭一个能跑的最小 Agent 骨架，称为 mini-harness。DSH 只作参照实现，不是照抄目标。每学一个机制，就往自己的骨架里加一块。骨架代码放在 `mini-harness/`，与讲义一同入库，可下载运行。课程结束时有两份产出。一份是对 DSH 设计取舍的理解，另一份是自己写出的、能跑通的 Agent 骨架。

课程分三层，目标是第三层。

| 层 | 能力 | 验收方式 |
|---|---|---|
| L1 能复述 | 说得出架构分层和机制 | 不看文档讲出流程 |
| L2 能定位 | 给功能名能找到源码文件与行号 | 小测指向代码位置 |
| L3 能改造 | 能替换实现，能移植到自己的平台 | 自己写的骨架跑通一个任务 |

课程从零基础起点展开。每讲从概念解决的问题讲起，再看 DSH 怎么实现，最后决定自己的平台要不要采用。源码行号只作证据，不作起点。

完整大纲见 [10 讲：边学边搭自己的 Agent 骨架](docs/course/ten-lectures-outline.md)。

## 资料范围

| 类别 | 内容 | 位置 |
|---|---|---|
| 产品功能 | 界面截图整理的功能地图，含界面字段与源码位置对照 | `docs/product/` |
| 子模块索引 | 按用户能力域划分的鱼骨大纲，功能到机制的映射 | `docs/product/` |
| 技术架构 | 五层架构与源码文件行号的逐层对应，含版本漂移 | `docs/code/` |
| 课程讲义 | 从零搭建 Agent 骨架的课程大纲与逐讲讲义 | `docs/course/` |
| 课程代码 | 边学边搭的 mini-harness，按讲序号分目录，可离线运行 | `mini-harness/` |
| 源码基线 | 研究时对应的上游 commit 与复现命令 | `meta/sources.md` |
| 版本记录 | 每次同步的变更与标签 | `CHANGELOG.md` |

上游源码不入库。需要核对代码时，按 `meta/sources.md` 的 commit 重新拉取。

## 资料索引

只列出已入库文档。

| 文档 | 内容 |
|---|---|
| [产品功能地图](docs/product/feature-map.md) | Web 端截图整理的功能清单。含新会话控件、模式、斜杠指令、权限、插件页、自动化任务字段与源码位置对照。 |
| [子模块鱼骨大纲](docs/product/module-fishbone.md) | 按六个用户能力域划分的功能索引。每个功能标注机制锚点或挂靠功能、复用机制与源码位置。 |
| [技术架构与源码对应](docs/code/architecture-source-mapping.md) | 配置层、运行时层、调度层、能力层、边界层的逐层源码对应。含三条不变量、版本漂移表和复现命令。 |
| [工具调用链路：五个关键问题](docs/code/tool-invocation-lifecycle.md) | 代码原理专题。工具从注册到回灌的完整链路，工具从哪来、缺工具怎么办、模型决策逻辑、检索方法，以及并发、审批、重试、压缩、重放五个关键问题与 waterfall 主线。 |
| [10 讲：边学边搭自己的 Agent 骨架](docs/course/ten-lectures-outline.md) | 课程大纲。三段 10 讲的目标、内容、时间估算、每讲节奏和验收标准。 |
| [第 0 讲：一次 LLM 调用的本质](docs/course/lecture-0-llm-call.md) | 第一讲讲义。裸调用、messages 三种角色、tool_calls、Agent 循环的差别，附可运行请求脚本和小测。 |
| [第 0 讲：实践篇](docs/course/lecture-0-practice.md) | 实测记录。用 OpenRouter 免费模型跑通一次调用，逐字段解读原始返回，含责任链路图与小测批改。 |
| [第 1 讲：从单次调用到 Agent 循环](docs/course/lecture-1-agent-loop.md) | 第二讲讲义。循环五步、tools 清单、tool_calls 返回，附可离线运行的假模型脚本与真 API 对照。 |
| [第 1 讲：实践篇](docs/course/lecture-1-practice.md) | 实测记录。三阶段脚本从假模型到真 I/O 再到真 API，含两轮报文、tool_call_id 配对图、小测批改与验收。代码与报文样本的链接见该篇开头。 |
| [第 2 讲：插件化，一切皆插件](docs/course/lecture-2-plugin.md) | 第三段机制篇第一讲。插件三形态、ctx 与 fiber、effect 与 disposer、五种事件派发的使用场景与配图、上游源码落点与平台取舍。 |
| [第 2 讲：实践篇](docs/course/lecture-2-practice.md) | 实测记录。任务 1-3 与选做的实测输出、effect 逆序清理的两层验证、waterfall 吞链三场景对照、小测批改与验收。任务代码链接见该篇开头。 |
| [第 3 讲：Agent 循环与状态机，长任务怎么被驱动、怎么停](docs/course/lecture-3-agent-loop.md) | 第三段机制篇第二讲。三层嵌套循环、数据判定的终止条件、max-tokens 粘性、日志投影与取消语义、上游源码落点与平台取舍。 |
| [第 3 讲：实践篇](docs/course/lecture-3-practice.md) | 实测记录。最小会话驱动器四场景输出、工具调用与多轮驱动的层级验证、取消清空 inbox、粘性终态、小测批改与验收。代码链接见该篇开头。 |
| [第 4 讲：上下文与 Session 日志，记忆只存一份怎么保证不乱](docs/course/lecture-4-session-log.md) | 第三段机制篇第三讲。append-only 日志是唯一真源、双投影、surfaceOp 的 append 与 replace、模型可见 ⟺ 已记录不变量、重放即重算、上游源码落点与平台取舍。 |
| [第 4 讲：实践篇](docs/course/lecture-4-practice.md) | 实测记录。最小日志与双投影四场景输出、遮蔽式压缩不删事件、不写事件不进模型视图、崩溃补记走同一 fold 路径、小测批改与验收。代码链接见该篇开头。 |
| [第 5 讲：工具调用，一次请求怎么穿过闸门](docs/course/lecture-5-agent-tools.md) | 第三段机制篇第四讲。工具由插件注册、每步写进提示词、模型无申请新工具的动作、执行前裁决闸门、并行与屏障调度、按序回灌，含源码落点与平台取舍。 |
| [第 5 讲：实践篇](docs/course/lecture-5-practice.md) | 链路走查与实测记录。三张脱敏图逐环节核对工具注册、审批闸门与调度回灌，五道小测的作答判定，四个场景的实测输出与验收。代码链接见该篇开头。 |
| [第 6 讲：能力 seam，换实现不改接口，怎么切](docs/course/lecture-6-capability-seam.md) | 第三段机制篇第五讲。约定、实现与消费方三种变化，Service Definition、Service Provider 与 Consumer 三角色，shell 三件套落地，不预防性拆分与权限能力的区分，含源码落点与平台取舍。 |
| [第 6 讲：实践篇](docs/course/lecture-6-practice.md) | 作答判定与实测记录。五道小测的逐题批改，四个场景的实测输出与解读，服务键装配、重复注册拒绝、换实现不改 Consumer、约定断言与反例。代码链接见该篇开头。 |
| [源码基线与复现](meta/sources.md) | 上游地址、界面版本、分析基线 commit、复现命令、API 一手文档链接。 |
| [版本记录](CHANGELOG.md) | 每次同步的版本、日期与变更条目。 |

## 学习交流

本库已公开，用于一起学习和交流。群里讨论课程内容、源码原理和平台移植，也接受补充材料。

![DeepSeek Harness 学习群二维码](docs/community/wechat-group-qr.png)

二维码是微信群邀请码，有效期至 2026-11-30。过期后需要更新群二维码，更新时替换 `docs/community/wechat-group-qr.png`。

## 证据基线速查

三个版本并存。核对代码前先对齐版本。

| 来源 | 版本 | commit |
|---|---|---|
| 界面截图 | `0.2.2-rc.5` | 无对应 commit |
| 分析基线 A | `0.2.2-rc.1` | `fcc0ad4` |
| 分析基线 B | `0.2.3-alpha.2` | `4b399c39a6d1479cd84ca591b4d7c88e24d38a96` |

界面字段到源码行号的映射，先 checkout 与 `0.2.2-rc.5` 对应的 commit。

## 文档约定

所有入库文档必须脱敏。脱敏清单和提交格式见 `AGENTS.md`。

文档标注两类事实：

- 界面实测。截图中直接可见的内容，保留原文。
- 源码位置。按界面术语定位到的包或目录，属查找入口，不承诺行号精确。

界面版本与源码版本可能不同。界面截图为 `0.2.2-rc.5`。做行号级核对前，先 checkout 对应 tag。

## 同步

本地工作区产出文档后，按 `AGENTS.md` 的规则脱敏、提交、打标签。同步由助手执行，用户验收。
