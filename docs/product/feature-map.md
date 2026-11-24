# DeepSeek Harness 产品功能地图

本文记录 DeepSeek Harness（以下简称 DSH）Web 端的产品功能。内容来自界面截图，界面显示版本为 `0.2.2-rc.5`。源码位置以包名标注，供查找使用。

## 证据范围

| 项目 | 说明 |
|---|---|
| 界面来源 | Web 端截图，共 32 张 |
| 界面版本 | `0.2.2-rc.5`，显示在设置页左下角 |
| 功能描述 | 以界面截图为准 |
| 源码位置 | 包级或目录级索引，不承诺行号精确 |

界面版本与分析时使用的源码副本版本不同。需要行号级对应时，先 checkout 与 `0.2.2-rc.5` 对应的 tag，再核对源码。

标注含义如下。

- 界面实测。截图中直接可见的内容，保留原文文案。
- 源码位置。按界面术语定位到的包或目录，属于查找入口。

## 产品定位

DSH 是本地优先的 Agent 工作台。它以工作区为单位组织会话，采用「一切皆插件」的架构。主界面标语为「探索未至之境 预览版」。

插件是主导航的一级入口。Agent 循环、终端、网页搜索和子智能体都作为可配置的插件提供。「创造模式」让 Agent 编写插件。

## 一级功能区

左侧栏依次是 **新会话**、**插件**、**自动化任务**、**更多**。工作区区提供搜索（`⌘K`）、视图设置和添加工作区（`⌘O`）。头像菜单包含 **设置**、**意见反馈** 和 **退出登录**。

五个一级功能区：会话页、插件页、自动化任务页、工作区管理、设置页。

## 新会话

输入框由六类控件组成。

| 位置 | 控件 | 行为 |
|---|---|---|
| 顶部左 | 工作区 | 选择会话使用的工作区 |
| 顶部右 | 模式 | 选择 Agent 预设 |
| 输入框内 | 占位文案 | `描述你想构建的内容，/ 调用指令，@ 文件跟对话` |
| 底部左 | 添加（`+`） | 展开斜杠指令面板 |
| 底部中 | 权限 | 选择权限档 |
| 底部右 | 模型 | 选择会话模型，显示 `DeepSeek-V4.1-Flash High` |
| 浮层 | 智能体团队协作 | 开关，默认关闭 |

源码位置按控件分布。会话外壳在 `packages/session` 和 `packages/client/ui-chat`。工作区在 `packages/workspace` 和 `packages/client/ui-directory-picker-*`。模式在 `packages/bundle/web-app/presets/`。指令在 `packages/client/ui-commands`。权限在 `packages/interaction/permission-presets`。模型在 `packages/llm`。团队协作在 `packages/team`。

占位文案里有两个语法触发器：`/` 唤起指令，`@` 引用文件。创造模式下占位文案变为「创建一个带左侧栏入口的 DSH 插件。」

### 四种模式

设置页说明：「选择 Agent 的工具和工作方式。日常任务用『标准模式』，扩展 DSH 的能力用『创造模式』。」

| 界面名 | 内部名 | 官方说明 | 源码位置 |
|---|---|---|---|
| 标准模式 | `standard` | 新任务默认。处理代码、文件和资料，适合大多数任务。Agent 会按需使用检索、编辑和终端等工具。 | `packages/bundle/web-app/presets/standard.patch.yml` |
| PTC 模式 | `ptc` | 包含标准模式的所有能力，更适合批量调用工具，并对结果进行筛选、整理、去重、统计或汇总的任务。 | `packages/bundle/web-app/presets/ptc.patch.yml`、`packages/ptc-runtime` |
| 极简模式 | `minimal` | Agent 使用终端和图片读取工具，并支持上下文压缩，适合测试和对比其他基础表现。 | `packages/bundle/web-app/presets/minimal.patch.yml`、`packages/compaction` |
| 创造模式 | `cordis` | 用对话定制 DSH：让 Agent 编写插件、添加新功能或界面；也能组合工具和提示词，创建自己的模式。 | `packages/bundle/web-app/presets/cordis.patch.yml`、`packages/extensions/ui-cordis`、`packages/extensions/tool-cordis` |

极简模式说明在两处截图中不同。一处写「终端和**图片**读取工具」，另一处写「终端和**文件**读取工具」。两处均为 `0.2.2-rc.5`。以预设补丁内容为准。

设置页提供「`+` 让 Agent 帮我创建预设模式」入口。预设本身可由 Agent 生成。

### 斜杠指令

点击 **+** 展开面板，分「添加」和「指令」两组，共七项。

| 分组 | 项 | 说明 | 源码位置 |
|---|---|---|---|
| 添加 | 文件 `file` | 文件引用或附件 | `packages/client/ui-attachment`、`packages/client/ui-file-actions` |
| 添加 | 目标 `goal` | 设置或查看长期任务目标 | `packages/goal/command-goal` |
| 添加 | 计划 `plan` | 进入或退出计划模式 | `packages/plan/plan-mode` |
| 添加 | 反馈 `feedback` | 发送关于当前会话的反馈 | `packages/feedback/command-feedback` |
| 指令 | 压缩 `compact` | 压缩以上对话内容 | `packages/compaction/command-compact` |
| 指令 | 权限 `permission` | 切换权限预设（沙箱模式与审批策略） | `packages/interaction/permission-presets`、`packages/client/ui-permission-presets` |
| 指令 | 模型 `model` | 选择本会话使用的模型 | `packages/settings` |

`goal`、`plan`、`compact` 和 `feedback` 各对应独立的包。指令把包的 command 入口暴露到输入框。

### 权限三档

| 界面名 | 内部值 | 配置 |
|---|---|---|
| 仅可查看 | `read-only` | 只读 |
| 工作区内修改 | `workspace-write` | `sandbox: 'workspace-write'`，`approval: 'ask'`，默认档 |
| 完全权限 | `danger-full-access` | `sandbox: 'danger-full-access'`，`approval: 'never'` |

权限由两个参数组合。`sandbox` 决定可读写范围，`approval` 决定是否审批。工作区内修改允许写工作区，越界操作需要审批。完全权限允许任意写操作，不需要审批。源码位置：`packages/interaction/permission-presets/src/index.ts:119-120,191-197`。

### 智能体团队协作

浮层文案：「通过共享任务板协调多个智能体的分工与进度，复杂任务表现更佳，token 开销也相应更高。」开关默认关闭。源码位置 `packages/team`，含 `agent-team` 和 `tool-agent-team`。

## 插件页

副标题「安装、启用和配置插件」。右上角提供 **刷新** 和 **+ 添加插件**。

### 内置插件配置

四项可配置，不可卸载。

| 界面项 | 官方说明 | 源码位置 |
|---|---|---|
| 子智能体 | 设置子智能体的递归层级、数量和模型。 | `packages/subagent`、`packages/experimental/subagent-oar` |
| 网页搜索与获取 | 选择网页搜索与网页获取使用的提供方。 | `packages/browser-use`、`packages/experimental/browser-use-runtime` |
| Agent 循环 | 控制 Agent 派发工具调用的方式。 | `packages/core/agent-loop` |
| 终端 | 限制每条命令最多能跑多久、最多输出多少内容。 | `packages/terminal`、`packages/experimental/terminal-bundle` |

### 实验性插件

截图可见十三项，均为开关式并带「实验性」标签。截图分三屏显示。

| 界面项 | 官方说明 | 默认 | 源码位置 |
|---|---|---|---|
| 语音输入 | 在本机使用 SenseVoice 转写录音，首次使用需安装依赖。 | 开 | `packages/experimental/speech-to-text-sensevoice`、`packages/client/client-ui-voice-input` |
| 自定义插件索引 | 在插件页添加「发现」标签页，从你添加的插件索引中浏览和安装插件。 | 关 | `packages/extensions/plugin-recommendations`、`packages/experimental/plugin-market-bundle` |
| 自动授权审查 | 提供「自动审查」访问模式：每次工具调用前，由模型对照你的要求检查，获准的调用立即运行，被拒绝的调用等你审批。 | 关 | `packages/experimental/auto-review` |
| 变更请求与工作树 | 在会话侧栏集中跟踪关联的 GitHub PR：查看检查状态、评审意见与代码差异，并把修改建议交给智能体继续处理。 | 关 | `packages/experimental/worktree`、`packages/experimental/tool-worktree`、`packages/experimental/webhook-github` |
| 个性化推荐 | 针对你对 DSH 的个性化需求，在回答下方展示推荐卡片。 | 关 | `packages/extensions/creation-recommendations` |
| 开发者工具 | 用于排查问题：在「会话数据诊断」中查看 DSH 为会话记录的内容，在「统计」页签查看每轮、每步的上下文、耗时、缓存和工具数据。 | 关 | `packages/experimental/inspector`、`packages/client/client-ui-stats`、`packages/client/session-inspector` |
| Computer Use | 目前仅支持 macOS，Windows 支持正在开发中。为已有及新建 PTC 会话加载 Computer Use。 | 关 | `packages/experimental/cua`、`packages/experimental/cua-macos`、`packages/experimental/cua-windows` |
| 思考过程机器翻译 | 智能体输出时，把展开的「思考」行翻译成你选择的语言，点击「查看原文」可切换回原文。 | 关 | `packages/experimental/cot-translation-bundle`、`packages/experimental/translator` |
| 随对话更新标题 | 根据你的所有消息生成会话标题，并在主要任务变化时更新，而不是只根据第一条消息生成。 | 关 | `packages/experimental/session-title-all-prompts-llm` |
| DSH 微章技能 | 让 Agent 为文档、PR 等产出添加「powered by dsh」微章。 | 关 | `packages/experimental/badge-skill-bundle`、`packages/experimental/skill-badge` |
| DeepSeek 会话导入 | 点击「新会话」旁的按钮上传 DeepSeek 官网导出的 ZIP 文件，每段对话都会成为所选工作区中的一个会话。 | 关 | `packages/experimental/deepseek-chat-import` |
| Codex 子智能体 | 使用 Codex 原生认证和设置委派单个任务。 | 未安装 | `packages/experimental/hooks-codex`、`packages/experimental/hook-protocol` |
| Claude Code 子智能体 | 使用 Claude Code 原生认证和设置委派单个任务。 | 未安装 | `packages/experimental/hooks-claude-code`、`packages/experimental/claude-code-mods` |

### 已安装插件

界面显示一个通过 bundle-skill 通道接入的第三方技能包插件，开关开启。bundle-skill 是把外部技能体系接入 DSH 的通道。

### 添加插件

弹窗文案：「输入插件的包名、GitHub 仓库地址或本地目录路径。」安装源默认「中国大陆镜像源」。

黄色警告原文：「请确认插件来源可信，插件在本机以你的权限运行，来源不明的插件可能损坏 DeepSeek Harness，或读取和泄露你的数据。按需安装的官方插件会在版本与 DSH 不同时提供『更新』。其他插件请先卸载再安装新版。」

## 自动化任务

列表页状态标签为已开启、已暂停、已结束和全部，带搜索框。示例任务显示「报告当天是星期几 — 每天 12:00 · 下次计划时间：11 月 23 日 12:00」。

**+ 新建** 提供两个入口。选择「在会话中创建」会跳回输入框并预填「请根据需求创建一个自动化任务。」选择「手动创建」会打开右侧抽屉表单。

创建表单字段包括任务名称、任务内容、执行位置、关联工作区、重复规则、日期、时间和时区。默认执行位置为「新建会话并复用」。

源码位置：`packages/schedule`、`packages/schedule/tool-schedule` 和 `packages/client/ui-schedule`。调度器把到期任务作为普通 follow-up 消息投递到目标 Session，重复规则用 RFC 5545 表达。

### 编辑视图字段对照

详情页顶部有 **规则** 和 **任务运行记录** 两个页签。规则页字段与数据结构对应如下。

| 界面字段 | 示例值 | 数据结构 |
|---|---|---|
| 下次运行 | 11 月 23 日 12:00 | `DailyScheduleRecord.scheduledAt` |
| 自动化任务名称 | 报告当天是星期几 | `title`，非空、去空白、不超过 120 字 |
| 自动化任务内容 | 今天星期几？请先确认当前日期（用 date 命令或运行时间），然后用中文简洁回答：今天是 XXXX 年 X 月 X 日，星期 X。 | `prompt`，去空白 |
| 执行位置 | 当前关联会话 | `target.kind='session'` |
| 重复 | 每天 | `kind:'daily'` |
| 重复间隔 | 1 | 界面概念。Daily 记录无 interval 字段，间隔由 kind 决定 |
| 时间 | 12:00:00 | `time`，规范化为 HH:mm:ss.SSS |
| 时区 | UTC+08:00 · 中国标准时间（系统） | `timeZone`，显式 IANA 名 |
| 关联会话 | 报告当天是星期几 | `target.sessionId`、`involvedSessionIds` |
| 任务运行记录 | 页签 | `deliveryHistory` |

数据结构定义在 `packages/schedule/schedule/src/types.ts` 和 `packages/schedule/schedule/src/storage.ts`。

### 执行位置三态

`target` 是 discriminated union，有三个取值。

| 界面选项 | 帮助文案 | locale key | `target.kind` |
|---|---|---|---|
| 当前关联会话 | 无，已选中 | `host.currentConversation` | `session` |
| 新建会话并复用 | 首次运行时创建，之后沿用这个会话 | `host.targetNewOnce`、`host.targetNewOnceHelp` | `new_once` |
| 每次新建会话 | 每次运行都创建独立会话 | `host.targetNew`、`host.targetNewHelp` | `new` |

界面文案定义在 `packages/client/ui-schedule/src/client/task-manager-locales.ts:188-193`。用户文档用「对话」，界面文案和源码 locale 用「会话」。数据模型统一用 Session。

### 重复规则

界面「重复」下拉有八项，底层持久化类型七种。`OneShotScheduleRecord` 包含 `after` 和 `at`。`RecurringScheduleRecord` 包含 `every`、`daily`、`weekly`、`cron` 和 `rrule`。

| 界面项 | 底层 kind | 说明 |
|---|---|---|
| 仅一次 | `after` 或 `at` | 按正延迟或绝对时刻二选一 |
| 每 N 分钟 | `every` | `everySeconds` 按秒数区分 |
| 每 N 小时 | `every` | `everySeconds` 按秒数区分 |
| 每天 | `daily` | `time` 加 `timeZone` |
| 每周 | `weekly` | `weekdays[]` |
| 周一至周五 | `weekly` | `weekdays=[1..5]` |
| 每月 | 无独立类型 | 由 `cron` 或 `rrule` 表达 |
| 自定义 | `cron` 或 `rrule` | `cron` 五字段，`rrule` 带 DTSTART |

界面项与底层类型不一一对应。每 N 分钟和每 N 小时共用 `every`。每周和周一至周五共用 `weekly`。每月没有独立类型。

### 时间与时区

「每天」的时间选择器显示时和分两列。其他重复类型显示三列。时区搜索框占位「搜索 UTC 偏移、IANA 标识或城市」，下面按 UTC 偏移列出城市。当前选中项示例为 `UTC+08:00 · 中国标准时间（系统）`。

### 任务运行记录

每条记录显示日期时间、任务名和完整指令原文。源码为 `deliveryHistory.records[]`，每条含 `scheduledAt`、`deliveredAt`、`messageId` 和 `prompt`。

界面显示一条记录只表示消息投递发生，不代表模型给出了结果或任务成功完成。

编辑态使用本地草稿。改动后界面显示「有未保存的修改」。**保存修改** 只提交变更字段。**放弃** 恢复存储值。存在未保存修改时，不能暂停、恢复、立即执行或删除任务。

## 工作区管理

标题栏三个按钮：搜索（`⌘K`）、视图设置和添加工作区（`⌘O`）。添加工作区打开系统目录选择器，选中的本地目录即为工作区。

视图设置菜单分三组：

- 分组方式：按工作区、按工作区树（默认）、单列表。
- 排序方式：手动排序（默认）、最近更新。
- 筛选会话：隐藏已归档（默认）、全部对话（显示已归档）、仅显示已归档。

源码位置：`packages/workspace`、`packages/client/ui-directory-picker-native`、`packages/client/ui-directory-picker-browse` 和 `packages/session-query`。

## 设置页

左侧五个分区：账号与余额、通用设置、模型、内置插件和 Agent 预设。右上角提供 **打开配置文件**。

### 账号与余额

显示账户标识、手机号尾号和充值余额，提供 **查询用量** 和 **充值** 按钮。

### 通用设置

| 字段 | 当前值 |
|---|---|
| 权限（新会话默认权限模式） | 工作区内修改 |
| 语言 | 中文 |
| 外观 | 浅色、深色或跟随系统 |
| 字号大小（仅影响会话内容） | 14 px |
| 工作步骤展示（希望看到多少工具调用细节） | 完全展开 |
| 工作步骤收起时机 | 回答结束后 |
| 显示代码工作视图（轨迹、本轮代码差异，可选完整 Agent 预设切换） | 开 |
| 快捷键 | 编辑快捷键 |
| 网页链接默认打开方式 | 应用内侧边栏 |
| 繁忙时的发送行为（`Enter` 和发送按钮，`Cmd/Ctrl+Enter` 使用另一行为） | 排队发送 |
| 性能与用量（信息展示详细程度） | 详细 |
| 在使用官方模型 API 时上传 Session Log | 开 |
| 更新渠道 | 开发版 |

源码位置：`packages/settings`、`packages/client/config`、`packages/client/shortcuts` 和 `packages/host/product-telemetry-otel`。最后一项对应 Session Log 上传。

### 其他分区

模型分区配置会话模型。内置插件分区与插件页的内置配置相同。Agent 预设分区见「四种模式」。

## 界面术语与源码位置索引

| 界面术语 | 源码入口 |
|---|---|
| 新会话外壳 | `packages/session`、`packages/client/ui-chat` |
| 工作区与目录选择 | `packages/workspace`、`packages/client/ui-directory-picker-*` |
| 模式预设 | `packages/bundle/web-app/presets/` |
| 斜杠指令 | `packages/client/ui-commands`、`packages/goal/command-goal`、`packages/plan/plan-mode`、`packages/compaction/command-compact`、`packages/feedback/command-feedback` |
| 权限三档 | `packages/interaction/permission-presets`、`packages/client/ui-permission-presets` |
| 智能体团队协作 | `packages/team`，含 `agent-team`、`tool-agent-team` |
| 插件页 | `packages/extensions`、`packages/experimental`、`packages/core/agent-loop` |
| 自动化任务 | `packages/schedule`、`packages/schedule/tool-schedule`、`packages/client/ui-schedule` |
| 子智能体 | `packages/subagent`、`packages/experimental/hooks-codex`、`packages/experimental/hooks-claude-code` |
| 网页搜索与获取 | `packages/browser-use` 及提供方包 |
| 终端 | `packages/terminal`、`packages/experimental/terminal-bundle` |
| 会话查询 | `packages/session-query` |
| 设置 | `packages/settings`、`packages/client/config`、`packages/client/shortcuts` |

## 已知文案差异

两处文案在同一版本中并存。

1. 极简模式说明写「图片读取工具」或「文件读取工具」。
2. 执行位置写「新建对话并复用」或「新建会话并复用」。

以界面截图和源码 locale 为准。用户文档中的「对话」为历史措辞。
