# 第 8 讲实践篇：端到端任务的作答与判定

本篇记录[第 8 讲讲义](lecture-8-e2e-task.md)五道小测的作答与判定，并给出端到端课程代码与实测。讲义只留题目，批改放在这里。

| 文件 | 作用 |
|---|---|
| [mini-harness/lecture-8/session_core.py](../../mini-harness/lecture-8/session_core.py) | append-only 日志、消息派生、持久检查点、因果校验。唯一事实源。 |
| [mini-harness/lecture-8/gate_core.py](../../mini-harness/lecture-8/gate_core.py) | 工具清单与 schema 边界、审批 waterfall 的失败关闭、按序执行回灌。 |
| [mini-harness/lecture-8/seam_core.py](../../mini-harness/lecture-8/seam_core.py) | 模型与 shell 两个 seam 的约定、两个 Provider、服务键装配。 |
| [mini-harness/lecture-8/driver_core.py](../../mini-harness/lecture-8/driver_core.py) | turn 与 step 循环，日志顺序不变量落地，取消与关停。 |
| [mini-harness/lecture-8/app.py](../../mini-harness/lecture-8/app.py) | 统一装配入口，按序创建，按逆序关闭。 |
| [mini-harness/lecture-8/demo.py](../../mini-harness/lecture-8/demo.py) | 四个场景对应讲义四条动手任务，就地捕获诊断保证输出可复现。 |

六个文件只用标准库，离线运行。命令是 `cd mini-harness/lecture-8 && python3 demo.py`。

## 小测批改

### 第 1 题：六块在链上的位置

**题目。** 六块机制在一条任务链上各管哪一段？为什么说整合不是把六块硬编码进一个入口？

**正确答案。** 第 2 讲插件化管装配，决定装哪些实现。第 3 讲循环管驱动，推进轮次与步骤并决定何时停。第 4 讲日志管事实源，消息历史从日志派生。第 5 讲闸门管执行，审批并调度工具调用。第 6 讲 seam 管换实现，换后端不改调用方。第 7 讲进程形态管承载，决定入口和物理载体。整合不能硬编码，因为扩展插件只依赖 `agent` 约定，不依赖 `agent-loop` 具体实现。没有特权内核，扩展靠往插件树挂插件，每项注册都是卸载时撤销的副作用。硬编码把调用方绑死在具体循环上，换实现就要改所有调用方。

**当时的回答。** 完整抄了讲义开头的流程主线，driver 领输入，Session 记事实，提示词从日志派生，模型输出写回日志，工具闸门执行，结果再写回日志。没有逐块对应六讲。第二问写的是"六块不是六个并列功能，而是这条链上的六段"，是描述不是理由。

**判定。** 第一轮不通过。第一问只给了串联流程，没有逐块定位。第二问没有回答为什么不能硬编码，漏掉了可替换这个关键点。

**重做回答。** 第一轮重写仍抄流程主线，补了"没有特权内核，全部按序挂在同一棵插件树上"，但没有点出可替换。第二轮答：扩展插件依赖 `agent`，不直接依赖 `agent-loop`。循环因此可以替换，整合时你要换的是实现，不是调用方。

**重做判定。** 第二轮通过。因（只认 `agent` 约定）、果（循环可替换）、绑定对象（换实现不改调用方）三点齐全。前两轮均为原文复述。

### 第 2 题：接缝上交换什么

**题目。** 一次模型可见事实从产生到进入下一轮请求，经过哪些接缝？哪两个接缝最容易传错东西？

**正确答案。** 六个接缝依次是入口到 driver 传 inbox 消息，driver 到 Session 传带类型的事件，Session 到提示词传 `deriveMessages()` 的派生结果，提示词到模型传请求头、派生历史和工具 schema，模型到闸门传完整的 `tool_calls` 批次，闸门到 Session 传规范的 `tool/result`。最容易传错的是 Session 到提示词和闸门到 Session。前者的边界是 projection 只改派生内容，不改记录的消息，工具 schema 不能带 `execute`、`timeoutMs` 这些宿主字段。后者传规范的 `tool/result`，不传原始执行输出，不跳过审批直接回灌。它容易错有两条原因，结果要按模型提交顺序回灌，执行完直接写日志会乱序，审批拒绝或执行失败也要落成规范结果，绕过闸门就等于审批没生效。

**当时的回答。** 答了入口到 driver、driver 到 Session、Session 到提示词、提示词到模型这条线，写出 `session.append()` 提交类型化事件、`deriveMessages()` 投影、surface 事件提供消息身份、工具 schema 不带宿主字段。结尾写"模型看到的一切都来自日志"。漏了闸门到 Session 这条接缝，也没有明确列出六个接缝。

**判定。** 第一轮部分通过。答对了 Session 到提示词这条重点接缝和 schema 边界，但另一条重点接缝缺失，六个接缝没列全。

**重做回答。** 第一轮答成"传完整的 `tool_calls` 批次，不让模型自己执行"，这是模型到闸门那条，上一轮已经答过。第二轮答：传规范的 `tool/result`，不传原始执行输出，不跳过审批直接回灌。容易错的原因有两条，一是结果要按模型提交顺序回灌，工具执行完直接写日志会乱序，二是审批拒绝或执行失败也要落成规范结果，绕过闸门写日志就等于审批没生效。

**重做判定。** 第二轮通过。判定点齐全。这段是按批改给出的答案复述，逻辑正确。

### 第 3 题：顺序是不变量

**题目。** 消息入日志、工具分派和请求派生之间有什么顺序约定？把顺序倒过来会出什么问题？

**正确答案。** agent loop 先领取 inbox 消息，再运行 `agent/pre-step`。只有作出 enter 决策后才打开 `step/start`。返回的 `user/message` 批次在请求派生前追加。提供方输出组装成 `assistant/message` 追加之后，才分派工具。倒过来有两个后果。先分派工具再补记用户消息，工具引用的是还没落日志的历史，回放时模型看到一批没有对应工具结果的用户消息，崩溃恢复走另一条分支。先派生下一轮请求再把消息入日志，请求发出后崩溃，日志尾部出现没有因的果，因果倒置破坏日志连续性。

**当时的回答。** 完整抄了顺序约定原文，先领 inbox、再 `agent/pre-step`、enter 决策后开 `step/start`、`user/message` 在派生前追加、`assistant/message` 落日志后才分派工具。题目第二问"倒过来会出什么问题"一个字没答。后半段大篇幅写的是一轮里的真实步骤，属于另一道题的内容。

**判定。** 第一轮不通过。顺序约定抄对了，但漏答后果，且大段内容跑题。

**重做回答。** 列了三个倒序场景及后果。一是先分派工具后把模型响应入日志，工具若产生不可逆副作用而模型流式输出断流或取消，该轮只结算为 `assistant/attempt` 不计入历史，恢复后模型不知道触发过工具，会重复执行或产生状态幻觉。二是先派生下一轮请求后把消息与工具结果入日志，请求发出后崩溃，日志尾部出现没有触发它的用户输入或工具结果的孤儿响应，破坏 `validateSessionLog` 的连续性校验，会话无法恢复。三是未入日志就派生子代理，子任务种子上下文缺父任务最新状态，父子视图分叉后无法对齐。

**重做判定。** 通过，是这轮答得最好的一题。两个必答后果都说到点上，第三个 fork 场景是自己加的，讲义里没有，推理方向正确。

### 第 4 题：生命周期与 flush

**题目。** 创建和关闭各按什么顺序做？`session/flush` 解决什么问题，为什么不能假定延后写入已排空？

**正确答案。** 创建受回滚保护。构造具象 agent 与带作用域上下文，进入 SessionStore 并发出 `session/created`，等待 setup 及其 commit，进入 AgentRegistry，等待串行 `agent/created` 监听器，然后才释放排队输入。任一步失败都回滚。关闭顺序反过来，先停止并排空驱动器，撤销作用域，关闭会话写路径，detach agent，最后 detach 会话。每次 detach 绑定到确切进入的对象。追加操作同步，持久化插件缓冲延后写，轮次结束时在 `session/flush` 检查点等待排空。需要立即持久屏障的生产方要显式等待 `flush`，因为代码执行到下一行时数据可能还在内存队列，多进程交接或退出会读到滞后状态或丢失尾部事件。

**当时的回答。** 完整抄了创建顺序、关闭顺序、同步追加与轮末 flush、显式等待的必要性四问。全部答到，但为原文复述。

**判定。** 通过。五题里唯一第一轮全对的，但无自主推理。

**变式题。** 假设在 `setup` 里注册了一个 agent 本地的投影插件，为什么要等 `agent/created` 串行监听器全部完成才放输入？

**变式第一轮。** 答的仍是生命周期通述，创建等监听器就位再放输入，关闭严格逆序，热路径同步写内存，轮末靠 flush 落盘。没有回答变式本身。

**变式判定。** 第一轮不通过。答的是原题，没有说清投影插件与第一次提示词组装的时序。

**变式重做。** 投影插件必须先于第一次提示词组装就绪并完成计算。分两层。生命周期层按自底向上挂载，日志与持久化层最先，投影插件依赖并订阅 Session 事件流，在会话就绪前挂载并构建初始投影视图，工具与配置随后，agent-loop 与模型适配器最后就绪，只有依赖全部激活才触发第一次组装。

**变式判定。** 通过。抓到核心因果，投影先于组装，依赖未全就位就组装会漏掉插件贡献。有一处边界要说明。变式问的是 agent 本地 scope 内 `setup` 注册的时机，重做答的是全局 Cordis 插件树的挂载顺序。两者同构，因果一致，但场景不同，要记牢题目问的是 agent 本地注册。

### 第 5 题：整合的平台取舍

**题目。** 平台取舍题。你要给自建平台接上这套链路，哪些机制必须先做，哪些可以等？说出判断标准和先做协议的代价。

**正确答案。** 先让一条循环跑通带工具的任务，再补 append-only 日志和派生，再补审批闸门，再把要换的后端切成 seam，最后按真实入口需求决定进程边界。判断标准是一次任务只调一次模型就结束，直接用函数调用，任务要跨两个轮次、有工具调用或需要断线续跑才接日志和循环。工具只有一种实现不用拆 seam，出现第二种再拆。先做协议的代价是前期样板代码增多，改一条提示词也要先定义事件类型、序列化校验和投影函数，而且 schema 一旦落盘就要维护旧日志的向后兼容。

**当时的回答。** 答了五步顺序，以及"先做协议再补核心，会得到一堆漂亮接口和跑不通的任务"。没有给判断标准。

**判定。** 第一轮部分通过。顺序和先做协议的代价答到了，判断标准缺失。

**重做回答。** 判断标准分两类。状态不可逆性优先，丢失或乱序会导致数据损坏、死循环或无法排障的机制比如日志协议、顺序约束和 flush 屏障必须先做。性能优化与扩展形态可以等，比如热插拔插件化、缓存调优和多代理派生。先做协议的代价有两条。一是样板代码拖慢前期开发，不能随手拼 messages 发给模型，加一条系统提示也要定义事件类型、写序列化校验、再经投影转换。二是 schema 演进的兼容包袱，协议一旦落盘，改字段或投影规则就要维护旧日志的向后兼容，否则历史会话无法回放。

**重做判定。** 通过。判断标准用了自己的框架，比讲义的分法更抽象，成立。schema 兼容包袱是讲义里没写的自主推理。

## 总评

五题最终全通过。第一轮只有第 4 题全对，其余四题都漏了题目里的因果问或取舍问。整轮暴露一个持续问题：作答以原文复述为主，题目问"为什么"和"会出什么问题"时容易只抄机制描述，不抄因果。经过多轮重做补齐。

独立推理出现在两处。第 3 题的 fork 场景是自己加的，推理方向正确。第 5 题的 schema 兼容包袱是讲义没有的内容。这两处说明机制读进去了，能往相邻场景推。

这批题的设计意图是考整合能力。六块单独都讲过，整合考的是接缝传什么、顺序能不能倒、取舍怎么判。复述流程只能拿到一半分，另一半在因果和边界上。下一讲进入平台设计对照，需要把这里的判断标准直接拿来用。


## 动手：跑通四个场景

四个场景对应讲义的四条动手任务。下面是 `python3 demo.py` 的实际输出。诊断在演示里就地捕获后随场景打印，保证终端输出顺序稳定。

### 场景 1：端到端跑一次带工具的任务

```
==============================================================
场景 1：端到端跑一次带工具的任务
==============================================================
[build] 1. Session 日志与持久化插件
[build] 2. 服务键装配：模型与 shell
[build] 3. 工具清单与闸门监听器
[build] 4. 模型 Provider
[build] 5. Driver 装配，setup 贡献先于第一次组装
  [log#01] turn/start {'turn': 1}
    [step 1.1] 认领 1 条，target=next-turn
  [log#02] step/start {'turn': 1, 'step': 1}
  [log#03] user/message {'text': '帮我算 2 加 3'}
      [derive] 1 条可见消息，1 个工具 schema
      [model] 第 1 次调用：先算一下 2 加 3
  [log#04] assistant/message {'text': '先算一下 2 加 3'}
        [approve] calculator 放行一次
        [exec] calculator {'a': 2, 'b': 3} -> local:a=2,b=3
  [log#05] tool/result {'text': 'local:a=2,b=3', 'name': 'calculator', 'ok': True}
  [flush] 缓冲落盘 5 条，已排空到 seq=5
    [step 1.2] 认领 1 条，target=next-step
  [log#06] step/start {'turn': 1, 'step': 2}
  [log#07] user/message {'text': 'calculator: local:a=2,b=3'}
      [derive] 4 条可见消息，1 个工具 schema
      [model] 第 2 次调用：结果是 5，还要继续吗
  [log#08] assistant/message {'text': '结果是 5，还要继续吗'}
      [followup] 下一轮输入：谢谢，再确认一次
  [flush] 缓冲落盘 3 条，已排空到 seq=8
  [log#09] turn/end {'turn': 1, 'reason': 'completed'}
  [log#10] turn/start {'turn': 2}
    [step 2.1] 认领 1 条，target=next-turn
  [log#11] step/start {'turn': 2, 'step': 1}
  [log#12] user/message {'text': '谢谢，再确认一次'}
      [derive] 6 条可见消息，1 个工具 schema
      [model] 第 3 次调用：已确认，任务完成
  [log#13] assistant/message {'text': '已确认，任务完成'}
  [flush] 缓冲落盘 5 条，已排空到 seq=13
  [log#14] turn/end {'turn': 2, 'reason': 'completed'}
  [driver] phase 归位 idle
  [result] {"turns": 2, "steps": 1, "end": "completed", "messages": [{"role": "user", "content": "帮我算 2 加 3"}, {"role": "assistant", "content": "先算一下 2 加 3"}, {"role": "tool", "content": "local:a=2,b=3"}, {"role": "user", "content": "calculator: local:a=2,b=3"}, {"role": "assistant", "content": "结果是 5，还要继续吗"}, {"role": "user", "content": "谢谢，再确认一次"}, {"role": "assistant", "content": "已确认，任务完成"}], "causal": [true, "每个工具结果都有在前的用户输入"], "durable": 13, "buffered": 1}
  → 两轮以上，中间一次工具调用，消息历史从日志派生
```

装配按序做五件事。日志与持久化插件先建，服务键装配模型与 shell，工具清单与闸门监听器就位，模型 Provider 选定，最后装 driver。driver 装配完成才放输入，对应讲义里等 `agent/created` 完成才释放排队输入。

一次输入跑出两个 turn。第一个 turn 两步。先领用户输入入日志，派生出一条可见消息，模型申请 `calculator`，审批放行，执行结果落成 `tool/result`。再领工具结果入日志，派生出四条可见消息，模型给出文本并带 followup。followup 进 next-turn，触发第二个 turn。日志共 14 条，每次 step 结束都 flush 一次代理缓冲。

结果里 `causal` 为 `true`，说明每个工具结果前面都有用户输入。消息历史七条全部从日志派生，没有另存一份。`durable` 为 13，`buffered` 为 1，因为最后一条 `turn/end` 在最后一次 flush 之后追加，留在缓冲里。这正是讲义说的延后写入：追加同步，落盘在下一个检查点。

### 场景 2：审批拒绝落成规范结果，换 shell 不改 driver

```
==============================================================
场景 2：审批拒绝落成规范结果，换 shell 不改 driver
==============================================================
[build] 1. Session 日志与持久化插件
[build] 2. 服务键装配：模型与 shell
[build] 3. 工具清单与闸门监听器
[build] 4. 模型 Provider
[build] 5. Driver 装配，setup 贡献先于第一次组装
  [log#01] turn/start {'turn': 1}
    [step 1.1] 认领 1 条，target=next-turn
  [log#02] step/start {'turn': 1, 'step': 1}
  [log#03] user/message {'text': '批量试工具'}
      [derive] 1 条可见消息，1 个工具 schema
      [model] 第 1 次调用：试两个工具
  [log#04] assistant/message {'text': '试两个工具'}
        [approve] calculator 放行一次
        [exec] calculator {'a': 7, 'b': 8} -> sandbox:a=7,b=8
        [gate] danger_tool 被拒：denied
  [log#05] tool/result {'text': 'sandbox:a=7,b=8', 'name': 'calculator', 'ok': True}
  [log#06] tool/result {'text': 'error: denied', 'name': 'danger_tool', 'ok': False}
  [flush] 缓冲落盘 6 条，已排空到 seq=6
    [step 1.2] 认领 2 条，target=next-step
  [log#07] step/start {'turn': 1, 'step': 2}
  [log#08] user/message {'text': 'calculator: sandbox:a=7,b=8'}
  [log#09] user/message {'text': 'danger_tool: error: denied'}
      [derive] 6 条可见消息，1 个工具 schema
      [model] 第 2 次调用：一个成功一个被拒，继续
  [log#10] assistant/message {'text': '一个成功一个被拒，继续'}
  [flush] 缓冲落盘 4 条，已排空到 seq=10
  [log#11] turn/end {'turn': 1, 'reason': 'completed'}
  [driver] phase 归位 idle
  [result] {"turns": 1, "steps": 2, "end": "completed", "messages": [{"role": "user", "content": "批量试工具"}, {"role": "assistant", "content": "试两个工具"}, {"role": "tool", "content": "sandbox:a=7,b=8"}, {"role": "tool", "content": "error: denied"}, {"role": "user", "content": "calculator: sandbox:a=7,b=8"}, {"role": "user", "content": "danger_tool: error: denied"}, {"role": "assistant", "content": "一个成功一个被拒，继续"}], "causal": [true, "每个工具结果都有在前的用户输入"], "durable": 10, "buffered": 1}
  → 被拒工具也落成 tool/result，换了 shell 实现，driver 未改
```

这一场景验证两条接缝。审批闸门上，`calculator` 被放行，执行走 `SandboxShell`，返回 `sandbox:` 前缀。`danger_tool` 被 `deny_danger` 监听器拒绝，没有执行，但仍落成一条规范的 `tool/result`，文本是 `error: denied`，`ok` 为 false。讲义说闸门到 Session 这条接缝最容易传错，这里演示了正确传法：拒绝也写结果，不跳过审批直接回灌。

seam 上，shell 从 `LocalShell` 换成 `SandboxShell`，driver 一行没改。工具 schema 只有名字和参数，`execute` 与审批元数据都没有进模型可见清单。`derive` 显示 6 条可见消息，包含两条工具结果，被拒的那条也在里面，模型能看到自己被拒了。

### 场景 3：取消语义与关停清理顺序

```
==============================================================
场景 3：取消语义与关停清理顺序
==============================================================
[build] 1. Session 日志与持久化插件
[build] 2. 服务键装配：模型与 shell
[build] 3. 工具清单与闸门监听器
[build] 4. 模型 Provider
[build] 5. Driver 装配，setup 贡献先于第一次组装
  [log#01] turn/start {'turn': 1}
    [step 1.1] 认领 1 条，target=next-turn
  [log#02] step/start {'turn': 1, 'step': 1}
  [log#03] user/message {'text': '开始'}
      [derive] 1 条可见消息，1 个工具 schema
      [model] 第 1 次调用：长任务
  [log#04] assistant/message {'text': '长任务'}
  [flush] 缓冲落盘 4 条，已排空到 seq=4
  [log#05] turn/end {'turn': 1, 'reason': 'completed'}
  [driver] phase 归位 idle
  [cancel] cause=user，keepInbox=False
  [close] 1. 停止接新并排空 driver
  [close] 2. 显式 flush 持久屏障
  [flush] 缓冲落盘 1 条，已排空到 seq=5
  [close] 3. 释放作用域与句柄
  [result] {"pending_before": true, "pending_after_cancel": false, "closed": true, "durable": 5, "buffer": 0}
  → 默认 cancel 清空 inbox，close 先停再 flush 最后释放
```

取消前 inbox 有排队输入。`cancel("user")` 用默认参数，`keepInbox` 为 false，排队输入被清空，`pending_after_cancel` 变成 false。取消信号只在 phase 非 idle 时设置，这次 turn 已经跑完，phase 是 idle，所以 `signal` 保持 None。这与讲义一致：没有活动时取消是空操作，不会给后续工作埋标记。

关停按逆序做三步。先停并排空 driver，再显式 flush 持久屏障，最后释放作用域与句柄。关停后 `durable` 为 5，`buffer` 为 0，缓冲全部排空。这验证了讲义的生命周期顺序：创建等监听器就位才放输入，销毁先停再排空最后释放。

### 场景 4：换模型 Provider，driver 一行不改

```
==============================================================
场景 4：换模型 Provider，driver 一行不改
==============================================================
[build] 1. Session 日志与持久化插件
[build] 2. 服务键装配：模型与 shell
[build] 3. 工具清单与闸门监听器
[build] 4. 模型 Provider
[build] 5. Driver 装配，setup 贡献先于第一次组装
  [log#01] turn/start {'turn': 1}
    [step 1.1] 认领 1 条，target=next-turn
  [log#02] step/start {'turn': 1, 'step': 1}
  [log#03] user/message {'text': '用脚本模型'}
      [derive] 1 条可见消息，1 个工具 schema
      [model] 第 1 次调用：脚本模型回复
  [log#04] assistant/message {'text': '脚本模型回复'}
  [flush] 缓冲落盘 4 条，已排空到 seq=4
  [log#05] turn/end {'turn': 1, 'reason': 'completed'}
  [driver] phase 归位 idle
[build] 1. Session 日志与持久化插件
[build] 2. 服务键装配：模型与 shell
[build] 3. 工具清单与闸门监听器
[build] 4. 模型 Provider
[build] 5. Driver 装配，setup 贡献先于第一次组装
  [log#01] turn/start {'turn': 1}
    [step 1.1] 认领 1 条，target=next-turn
  [log#02] step/start {'turn': 1, 'step': 1}
  [log#03] user/message {'text': '用回显模型'}
      [derive] 1 条可见消息，1 个工具 schema
      [model] EchoModel 回显
  [log#04] assistant/message {'text': 'echo'}
  [flush] 缓冲落盘 4 条，已排空到 seq=4
  [log#05] turn/end {'turn': 1, 'reason': 'completed'}
  [driver] phase 归位 idle
  [result] {"script": {"turns": 1, "end": "completed"}, "echo": {"turns": 1, "end": "completed"}}
  → 两次装配只换了 model 实现，driver 与闸门未动
```

两次装配只换了模型实现。第一次用 `ScriptModel` 跑脚本回复，第二次用 `EchoModel` 回显。两次都跑出一个 completed 的 turn，`driver` 与闸门代码完全一致。这是第 6 讲 seam 在整合链路上的复用：约定是 `ModelDefinition.current()`，两个 Provider 各自实现，消费方 driver 只认约定。

## 验收

```
==============================================================
验收
==============================================================
  [通过] 端到端两轮带工具
  [通过] 审批失败关闭落规范结果
  [通过] 取消清空 inbox
  [通过] 关停后缓冲排空
  [通过] 换实现不改 driver

{"exit": 0}
```

五项验收全部通过。

| 检查项 | 结果 |
|---|---|
| 端到端两轮带工具 | 通过。两个 turn，消息历史含一条 tool 角色消息。 |
| 审批失败关闭落规范结果 | 通过。被拒工具落成 `error: denied` 的 `tool/result`，因果校验为真。 |
| 取消清空 inbox | 通过。默认 `keepInbox` 为 false，待处理从 true 变 false。 |
| 关停后缓冲排空 | 通过。`close()` 后 `buffer` 为 0。 |
| 换实现不改 driver | 通过。换 `EchoModel` 后 driver 与闸门未改，任务照常完成。 |
| 只用标准库、离线运行 | 通过。无网络请求，无真实进程。 |

## 事实边界

上面六份文件是自己编写的骨架，不是上游源码。实测输出来自本机 `python3 demo.py` 的真实运行，逐字取自终端，三次复跑逐字一致。四段场景输出与验收块按场景标题切分，顺序稳定。

上游对照见讲义的源码事实一览，基线 commit `4b399c39`。骨架省略了真实模型调用、SQLite 持久化、类型投影生成器、WebSocket mux、snapshot 恢复与真实进程执行。假模型按脚本产出回复，shell 返回固定字符串不启进程。小测判定是教学判断，不是源码事实。
