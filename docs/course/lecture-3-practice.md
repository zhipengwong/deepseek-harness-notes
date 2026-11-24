# 第 3 讲：实践篇

本文记录第 3 讲的动手过程。讲义讲三层循环、终止判定、状态投影与取消语义，这篇讲实测。目标是跑通一个最小会话驱动器，验证四件事：工具调用在 turn 层、追加输入走 driver 层、取消默认清空 inbox、max-tokens 终态粘性。最后记录小测批改。

代码在 `mini-harness/lecture-3/`，共两个文件，全部离线运行，不需要网络和 key。

| 文件 | 用途 |
|---|---|
| [loop_core.py](../../mini-harness/lecture-3/loop_core.py) | 最小驱动器。`Inbox` 两级队列、`Session` 追加日志、`AbortSignal` 协作取消、`Driver` 三层循环、`FakeModel` 脚本化模型。 |
| [demo.py](../../mini-harness/lecture-3/demo.py) | 四个场景：完成判定、多轮驱动、取消、max-tokens 粘性。 |

## 任务 1：跑通基线

```bash
cd mini-harness/lecture-3
python3 demo.py
```

四个场景一次跑完。下面按场景贴关键输出并解读。

## 场景 1：完成判定看有没有 tool-call

```
[step 1.1] target=next-turn，认领 1 条输入
  [model] 查天气，tools=['weather']
  [inbox] +next-step: weather 的结果
[step 1.2] target=next-step，认领 1 条输入
  [model] 查地图，tools=['map']
  [inbox] +next-step: map 的结果
[step 1.3] target=next-step，认领 1 条输入
  [model] 查汇率，tools=['fx']
  [inbox] +next-step: fx 的结果
[step 1.4] target=next-step，认领 1 条输入
  [model] 三件事都办好了，tools=[]
  [log#10] turn/end {'turn': 1, 'reason': 'completed'}
```

三次工具调用（weather / map / fx）都在 turn 1 内。每次 `tools` 非空，结果回灌 `next-step`，`target='next-step'` 把循环拉回 turn 内的下一步（对应上游 `agent.ts:396`）。第四步 `tools` 为空，判定 `completed`，turn 结束。

这正是小测第 1、2 题的实测答案：**工具调用是 turn 层的多步，完成判定是「本步无 tool-call」，不是数步数，也不是看 finish_reason**。

## 场景 2：追加输入走 driver 层

```
[log#04] turn/end {'turn': 1, 'reason': 'completed'}
[log#05] turn/start {'turn': 2}
[log#06] step/start {'turn': 2, 'step': 1}
[log#07] step/end   {'turn': 2, 'step': 1}
[log#08] turn/end   {'turn': 2, 'reason': 'completed'}
```

turn 1 答完第一条后，`followup` 往 `next-turn` 塞入第二条消息。`turn()` 结尾检查 `has_pending` 为真，返回 `True`，driver 的 `while (await turn())` 再开一轮（对应上游 `agent.ts:423-428`）。turn 2 消费掉第二条、没有后续输入，`has_pending` 为假，driver 停。

要点。**新消息带来的是「另一个 turn」，由 driver 层负责。工具调用带来的是「同一 turn 的下一步」，由 turn 层负责**。两者分属不同循环。这一点在小测第 1 题里最初答反了，实测确认了这个区分。

一个实现细节。`claim(target)` 会把目标队列整批认领。如果一开始就往 `next-turn` 塞两条，它们会在同一步被一起取走，不会产生两个 turn。所以演示追加输入必须用 `followup` 在 turn 结束后再塞。这也符合真实场景。新消息是在 Agent 运行期间陆续到达的。

## 场景 3：取消默认清空 inbox

```
[step 1.1] target=next-turn，认领 2 条输入
  [model] 处理中，tools=[]

[cancel] cause=user，keepInbox=False
  [inbox] 已清空（cancel 的默认行为）
  [log#04] turn/end {'turn': 1, 'reason': 'aborted(user)'}
```

我们入队两条输入（一条正在处理、一条排队）。`cancel()` 默认 `keepInbox=False`，先把 inbox 清空，再 abort 当前 phase。当前 turn 记为 `aborted(user)` 并正常写 `turn/end`。agent 本身没有销毁，phase 归位 idle 后还能被再次唤醒。

对应上游 `agent.ts:189-199` 的 `if (!options.keepInbox) this.inbox.clear()`。取消的语义是「这个请求作废」，所以默认连输入一起丢弃。只有明确要「暂停待续」时才传 `keepInbox: true` 保留。这是小测第 4 题的实测答案，也是最初答错的地方。

## 场景 4：max-tokens 粘性

```
[step 1.1] [model] 输出触顶，tools=['tool_a']
[step 1.2] [model] 后续又调一次工具，tools=['tool_b']
[step 1.3] [model] 最终正常完成，tools=[]
[log#08] turn/end {'turn': 1, 'reason': 'max-tokens'}
```

第一步触顶（`max_tokens=True`），后两步正常推进，其中第三步已经完整完成。但 `turn/end` 仍记 `max-tokens`，没有被降成 `completed`。

驱动器里的保护是一行（对应上游 `agent.ts:369`）：

```python
if step_end is not None:
    if turn_ends is None or turn_ends != "max-tokens":
        turn_ends = step_end
```

turn_ends 一旦是 max-tokens 就不再被覆盖。原因是 `turn/end` 是写盘的唯一终态结论。截断信号若被后续 completed 抹掉，下游就无从知道这次输出不完整。粘性保住的正是这个信号。这也是小测第 3 题追问「截断后追问一句算什么」的答案。仍算 max-tokens。

## 小测与批改

第 3 讲共四题。首轮两题通过、两题需修正，重答后四题全部通过。每题先列题目和正确答案，再记录作答与判定。

### 第 1 题：循环层级

**题目。**
一个 Agent 回答用户前先调了 3 次工具。这 3 次发生在哪层循环？用户追加一条消息让它再跑一轮，又在哪层？

**正确答案。**
3 次工具调用都在同一 turn 的 step 循环（`agent.ts:340`），每调一次工具就是一步，结果回灌后进入下一步。追加消息再跑一轮是 driver 层（`:273`），`turn()` 返回 `true` 让 driver 再开一轮。分界点是 `:423` 的 `if (!this.inbox.hasPending) return false`。工具调用不经过 driver，在 turn 内部靠 `target='next-step'`（`:396`）回到 step 循环。

**当时的回答。**
答成「driver 层，turn 层」，顺序反了。把工具调用放到了 driver，把追加消息放到了 turn。

**重答。**
完全答对，并补上了 `:423` 的 `hasPending` 判定和 `:396` 的 `target='next-step'` 两处证据。

**判定。**
重答后正确。

### 第 2 题：maxSteps 认知纠偏

**题目。**
有人说「这个 Agent 设了 `maxSteps=20`，超过就停」。这句话对不对？真正的完成判定是什么？

**正确答案。**
不对。上游无 `maxSteps`/轮次预算（`agent-loop/README.md:238` 明确 "No built-in turn budget"）。完成判定是本步无 tool-call block（`agent.ts:576-577`）。终止原因汇入 `TurnEndReason`，除 completed 外还有 max-tokens、error、aborted、blocked，以及恢复期的 interrupted 与 forked。

**当时的回答。**
正确。指出没有 maxSteps，真正判定是本步没有 tool-call block。

**判定。**
正确。补一点。终止原因不止 completed 一类，源码枚举共七种（详见讲义「怎么停」一节的表格）。

### 第 3 题：max-tokens 粘性

**题目。**
`max-tokens` 是粘性的，代码专门加了保护不让它被后续 completed 覆盖。为什么？用户看到截断后追问一句，这轮算 completed 还是 max-tokens？

**正确答案。**
两层。第一层问为什么。`turn/end` 日志是写盘的唯一终态结论，会被投影读取。截断后若被后续 completed 覆盖，就抹掉了「这次输出不完整」的事实，下游无从知道。第二层问追问后的结论。仍算 max-tokens，`:369` 的保护让先到的信号一直保留。

**当时的回答。**
首轮只复述了机制（粘性、不被降级、算 max-tokens），没答「为什么」这层设计动机。

**重答。**
补齐设计动机。终态信号不能被后续正常结果抹掉，否则截断看不出来。

**判定。**
重答后正确。

### 第 4 题：取消与 inbox

**题目。**
上游没有 `paused` 状态。用户取消时会怎样？取消的是 step、turn 还是 agent？未消费的输入去哪？

**正确答案。**
三问分别答。取消粒度。`cancel()` abort 当前 phase 的 `AbortController`，`signal.throwIfAborted()` 贯穿 step，结果是当前 turn 提前结束记为 `aborted`，turn 正常写 `turn/end`，agent 不销毁、下次还能唤醒。cause 分四类：`user / parent / hook / disposed`（`:93-108`）。未消费输入。默认清空，`if (!options.keepInbox) this.inbox.clear()`（`:191`），只有传 `keepInbox: true` 才保留。

**当时的回答。**
状态分层部分（日志投影、无 paused、靠 AbortSignal）正确，但没直接答「输入去哪」，且顺带说成「未消费输入留在 inbox 供下一次 wake 使用」。这在默认路径下是错的。

**重答。**
三问全对，明确指出默认 `inbox.clear()`，只有 `keepInbox: true` 才不清。

**判定。**
重答后正确。

### 批改说明

首轮第 2 题一次通过。第 1、4 题答错或答反，第 3 题只答了机制没答动机。四题重答全部到位后过关。三处修正指向同一条主线。**日志是唯一真相，但入口数据会被显式处理的**。终态写完就不改（粘性），取消默认清输入（`inbox.clear()`），新输入决定要不要再开一轮（`hasPending`）。

## 验收记录

| 项 | 结果 |
|---|---|
| 跑通 `demo.py`，四个场景输出与讲义一致 | 通过 |
| 工具调用在 turn 层，完成判定看 tool-call | 通过 |
| 追加输入走 driver 层，多轮驱动复现 | 通过 |
| 取消默认清空 inbox，turn 记 aborted | 通过 |
| max-tokens 粘性，后续正常推进不降级 | 通过 |
| 小测四题通过（含两题重答、一题补动机） | 通过 |

六项全部通过，第 3 讲过关。

## 事实边界

所有输出来自本地 Python 3 实测，脚本只用标准库，离线运行。最小驱动器是教学简化实现，结构对齐上游 `agent-loop/src/agent.ts` 的三层循环，但不覆盖 step 失败重试、并发工具执行、崩溃恢复与 fork 补记。「后两类终止原因不在运行时产生」来自上游 `session/src/types.ts` 的注释。要不要设轮次上限的判断是设计取舍，不是源码事实。
