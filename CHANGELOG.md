# 版本记录

格式遵循 Keep a Changelog。版本规则见 `AGENTS.md`。

## v0.8.13 — 2026-11-24

- 新增第 4 讲讲义 `lecture-4-session-log.md`：append-only 日志唯一真源、双投影（模型 surface 与人类 transcript）、surfaceOp 的 append/replace、模型可见 ⟺ 已记录不变量、重放即重算，含源码落点表与平台取舍。
- 新增第 4 讲实践篇 `lecture-4-practice.md`：四场景实测、小测四题逐题批改与自主复述记录、验收六项。
- 新增两张配图：`lecture-4-log-projections-concept.png` 作讲义概念图（seq 从 0 起），`lecture-4-log-projections.svg` 作实践篇实测对照图（seq 与 demo 对齐，从 1 起）。两图结构相同，仅编号起点不同。
- 新增 `mini-harness/lecture-4/`：`session_core.py` 与 `demo.py`，离线可运行。
- README 补第 4 讲两行索引。

## v0.8.12 — 2026-11-24

- `tool-invocation-lifecycle.md` 的 43 处源码落点全部改为可点击链接，绑定上游 deepseek-harness 仓库固定 commit `4b399c39` 的行锚点（如 `#L295-L297`）。链接锁定基线不漂移，源码仍不入库，符合脱敏约定。
- 证据范围一节补链接说明与基线记录指引；承接上文的简写行号（`:5-7`、`:14` 等）也补全为独立链接。

## v0.8.11 — 2026-11-24

- 新增代码原理专题 `docs/code/tool-invocation-lifecycle.md`。把工具从注册到回灌的问答整理成完整链路：工具来源、缺工具的三种情况、模型侧四条决策路径、本地与运行时检索，以及并发调度、执行前审批、失败重试、上下文压缩、取消重放五个关键问题，收束于 waterfall 主线与平台取舍表。
- 新增配图 `docs/code/tool-lifecycle-five-questions.png`（五个关键问题对照卡片，脱敏技术示意图），`.gitignore` 精确放行；图后附文字对照表以弥补深色主题下文字偏暗。
- README 资料索引补该专题一行。

## v0.8.10 — 2026-11-24

- 新增第 3 讲讲义 `lecture-3-agent-loop.md` 与实践篇 `lecture-3-practice.md`。讲义讲三层循环、数据判定终止、max-tokens 粘性、日志投影与取消语义，引用已入库的 `lecture-3-loop-layers.png`；实践篇记录最小会话驱动器四场景实测、小测四题批改（两题重答、一题补动机）与验收。
- 新增 `mini-harness/lecture-3/`：`loop_core.py`（Inbox/Session/AbortSignal/Driver/FakeModel）与 `demo.py`（完成判定、多轮驱动、取消、粘性四场景），全部离线运行。
- README 索引补第 3 讲讲义与实践篇两行。终止原因按源码如实写全七种（含 blocked 与两个恢复期标记），修正口头讲解的「四类」简化。

## v0.8.9 — 2026-11-23

- 新增第 3 讲配图 `docs/course/lecture-3-loop-layers.png`。图示三层嵌套循环（driver / turn / step）与唤醒入口，供第 3 讲讲义引用。`.gitignore` 精确放行该图。

## v0.8.8 — 2026-11-23

- 统一标题格式。讲义用「第 N 讲：主题」，实践篇改为「第 N 讲：实践篇」，两者都以冒号分隔讲次与副标题。覆盖 README 索引三条链接、三篇实践篇的一级标题，以及讲义中对实践篇的一处引用。CHANGELOG 历史条目保留原样。

## v0.8.7 — 2026-11-23

- README 索引移除「mini-harness 第 2 讲代码」独立条目。第 2 讲代码链接已收在该讲实践篇开头的文件表，主索引只列讲义与实践篇。第 1 讲此前已按此整理；第 0 讲代码内联于讲义，无独立代码条目。
- `AGENTS.md` 固化课程产出结构：每讲一篇讲义 + 一篇实践篇，代码链接只放实践篇，README 不单列代码或报文样本。

## v0.8.6 — 2026-11-23

- 新增第 2 讲实践篇 `docs/course/lecture-2-practice.md`。记录任务 1-3 与选做的实测输出：echoer 插件零内核改动收到事件、卸载自动撤销监听、effect 逆序清理的两层验证（子先父后 + 注册逆序）、waterfall 不调 `next()` 的三场景对照，含小测批改与验收记录。
- 新增任务代码 `mini-harness/lecture-2/demo_task2.py`（事件自动注册与卸载撤销）与 `demo_task4.py`（waterfall 吞链实验）。`demo.py` 的 greeter 增加第二个 effect 用于逆序清理验证。
- 第 2 讲讲义的实测输出块同步任务 3 后的现状，补「启动计时器」「停止计时器」两行，卸载要点改为逆序清理表述；「移植到骨架」一节补实践篇指引。
- README 索引新增第 2 讲实践篇条目。

## v0.8.5 — 2026-11-23

- 第 2 讲讲义新增「五种方式的使用场景」一节。用 emit、parallel、serial、bail、waterfall 配一张对比图，逐种说明典型场景与判断标准，附上游真实事件用例和 bail 的事实边界。
- 新增配图 `docs/course/lecture-2-dispatch-modes.svg`。SVG 矢量图，GitHub 原生渲染，不在 .gitignore 忽略范围。
- 本讲小测新增第 5 题，考派发方式的选择判断。

## v0.8.4 — 2026-11-23

- 整理 README 资料索引。第 1 讲的四个代码条目与报文样本从主索引移除，代码链接收进第 1 讲实践篇开头的文件表，保持目录索引整洁。

## v0.8.3 — 2026-11-23

- 新增第 2 讲讲义 `docs/course/lecture-2-plugin.md`。讲插件化解决什么问题、三种插件形态、ctx 与 fiber、effect 与 disposer、五种事件派发、上游源码落点与平台取舍，附四道小测。
- 新增第 2 讲代码 `mini-harness/lecture-2/plugin_core.py` 与 `demo.py`。最小插件框架，实现注册、六态生命周期、effect 逆序清理、事件广播与 waterfall 拦截，已实测运行通过。
- README 索引新增第 2 讲讲义与代码条目。

## v0.8.2 — 2026-11-23

- 新增第 1 讲实践篇 `docs/course/lecture-1-practice.md`。记录三阶段脚本的实测过程、tool_calls 返回形状、两轮真 API 报文、三版对照、小测批改与验收记录。
- 新增配图 `docs/course/lecture-1-tool-call-id-pairing.png`，说明多个 tool_calls 靠 id 配对回灌结果。
- README 索引新增第 1 讲实践篇条目，`.gitignore` 精确放行配图。

## v0.8.1 — 2026-11-23

- 第 1 讲讲义的「本讲小测」改为「小测与批改」逐题结构。四题各含题目、正确答案、当时的回答与判定，附批改说明。
- 记录第 1 讲小测的重做过程：第 2 题答错方向经两次修正通过，第 3 题与第 4 题补全理由后通过。便于独立看文档的人自测对照。

## v0.8.0 — 2026-11-23

- 第 1 讲新增真 API 脚本 `agent_loop_api.py`。把假模型换成 OpenRouter 模型跑完整循环，逐轮打印请求与响应原始报文，key 只从环境变量读取。
- 新增真 API 报文样本 `api-run-sample.log`。记录两轮完整报文，含 tool_calls 返回、tool 消息回灌与 token 增长，Authorization 头已遮蔽。
- 对照版 `agent_loop_real.py` 的第二轮假模型改为从 tool 消息取真实结果作答，消除工具结果与模型回复的不一致。
- 讲义新增「真 API 实测」一节，用实测数据回答第 0 讲遗留观察题，并给出三个版本的对照表。更新动手任务与「a.txt 在哪里」一节。
- README 索引新增真 API 脚本与报文样本条目。动手任务 5 已实测完成。

## v0.7.1 — 2026-11-23

- 第 1 讲代码目录新增 `a.txt` 与 `agent_loop_real.py`。对照版把 `execute_tool` 改为真实读取文件，与原版写死返回值形成对照。两版均已运行验证。
- 第 1 讲讲义新增「a.txt 在哪里」一节，说明示例中的文件最初只是字符串，并解释对照版模型回复仍为预设文本的原因。动手任务扩为五项。
- README 索引新增真实 I/O 对照版条目。

## v0.7.0 — 2026-11-23

- 仓库范围扩展：从只存文档改为文档与课程代码一同入库。新增 `mini-harness/` 代码目录。
- 迁入第 1 讲假模型示例 `mini-harness/lecture-1/agent_loop.py`，可离线运行，已实测通过。
- `AGENTS.md` 更新入库范围、目录映射与提交类型（新增 `feat`）。README 课程目标、资料范围与索引新增代码条目。

## v0.6.4 — 2026-11-23

- 新增课程讲义 `docs/course/lecture-1-agent-loop.md`。讲循环五步、tools 清单与 tool_calls 返回，附可离线运行的假模型脚本和 OpenRouter 真 API 对照。脚本已实际运行验证。
- README 课程索引新增第 1 讲条目。

## v0.6.3 — 2026-11-23

- 实践篇「小测与批改」改为逐题结构。每题列出题目、正确答案、当时的回答与判定，另补追加观察题参考答案，便于独立学习者自测对照。

## v0.6.2 — 2026-11-23

- 新增课程讲义类文档：`docs/course/lecture-0-practice.md`。记录 OpenRouter 免费模型的实测调用、原始返回、逐字段索引、责任链路与小测批改。
- 新增配套配图：`docs/course/lecture-0-response-structure.png`、`docs/course/lecture-0-role-chain.png`。
- README 资料索引新增实践篇条目。`.gitignore` 精确放行两张配图。

## v0.6.1 — 2026-11-23

- README 新增「课程目标」章节。记录课程主线、三层目标与验收方式、零基础起点的展开方式，并链接课程大纲。

## v0.6.0 — 2026-11-23

- 仓库可见性由私有改为公开，用于一起学习和交流。
- README 新增「学习交流」章节，公开微信群二维码，注明有效期与更新方式。
- 新增配图 `docs/community/wechat-group-qr.png`。`.gitignore` 精确放行该图。

## v0.5.0 — 2026-11-23

- 新增课程讲义类文档：`docs/course/ten-lectures-outline.md`。三段 10 讲的目标、内容、时间估算、每讲节奏与验收标准。
- 新增课程讲义类文档：`docs/course/lecture-0-llm-call.md`。裸调用与 Agent 循环的差别、`messages` 角色、`tool_calls` 结构化文本、可运行请求脚本与小测。
- 新增配套配图：`docs/course/ten-lectures-outline.png`、`docs/course/lecture-0-call-vs-loop.png`。
- `README.md` 资料范围与索引新增课程讲义条目。`AGENTS.md` 补入课程讲义目录映射。`.gitignore` 精确放行两张配图。

## v0.4.1 — 2026-11-22

- 替换 `docs/product/module-fishbone-diagram.png` 为六根骨齐全的版本。
- 移除文档中关于下方三根骨标签被裁切的说明。

## v0.4.0 — 2026-11-22

- 新增子模块索引类文档：`docs/product/module-fishbone.md`。按六个用户能力域划分功能，标注机制锚点与挂靠功能、复用机制和源码位置。
- 新增配套配图：`docs/product/module-fishbone-diagram.png`。
- README 资料范围与索引新增子模块索引条目。

## v0.3.1 — 2026-11-22

- 更新 `AGENTS.md`：目录映射补入技术架构类，明确脱敏技术示意图可作为配图入库。
- 更新 `.gitignore`：精确放行技术架构配图。

## v0.3.0 — 2026-11-22

- 新增技术架构类文档：`docs/code/architecture-source-mapping.md`。逐层记录五层架构与源码文件行号的对应，含三条不变量、版本漂移表和复现命令。
- 新增配套配图：`docs/code/architecture-layers.png`。
- README 资料范围与索引新增技术架构条目。

## v0.2.1 — 2026-11-22

- README 资料索引只保留已入库文档，移除未入库资料的登记条目。

## v0.2.0 — 2026-11-22

- 在 `README.md` 新增资料索引，按主题分组登记全部学习资料。已入库项给链接，未入库项标注状态与用途。
- 新增证据基线速查表，列明界面版本与两条源码分析基线。

## v0.1.0 — 2026-11-22

初始版本。

- 新增产品功能地图脱敏版：`docs/product/feature-map.md`。
- 新增源码基线与复现记录：`meta/sources.md`。
- 新增同步与版本管理约定：`AGENTS.md`。
