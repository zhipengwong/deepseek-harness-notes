"""第 4 讲演示：append-only 日志 + 双投影 + 遮蔽式压缩 + 崩溃重放。

四个场景对应小测四题：
  1 压缩后原始事件是否还在、模型为何看不到
  2 replace 是遮蔽不是删除（nodes 与 log 分离）
  3 模型可见 ⟺ 已记录（没写事件的消息不进视图）
  4 崩溃恢复：补记事件走同一条折叠路径
"""

from session_core import Session, fold_surface, interrupted_closers, replay


def hr(title):
    print(f"\n{'=' * 60}\n{title}\n{'=' * 60}")


# ---------------------------------------------------------------- 场景 1
hr("场景 1：基础 append + 双投影")
s = Session()
s.append("system/message", {"text": "你是助手"})
s.append("user/message", {"text": "查一下北京天气"})
s.append("assistant/message", {"text": "我来查", "stream": []})
s.append("tool/result", {"text": "晴 25℃"})
s.append("assistant/message", {"text": "北京今天晴，25℃"})

print("\n[日志] 共 %d 条事件，seq %d..%d" % (len(s.log), s.log[0]["seq"], s.log[-1]["seq"]))
print("[模型视图 derive_messages]")
for m in s.derive_messages():
    print("   ", m)
print("[人类视图 transcript]")
for m in s.transcript():
    print("   ", m)
print("   → 此时两个视图一致：都是 5 条消息")

# ---------------------------------------------------------------- 场景 2
hr("场景 2：压缩 replace —— 遮蔽不是删除")
s.append("compaction/summary", {"text": "已查询北京天气：晴 25℃"}, surface_op=None)
# replace seq2-4（user + assistant + tool result），用一条摘要 user 消息遮蔽
s.append(
    "user/message",
    {"text": "[摘要] 用户问北京天气，查到晴 25℃"},
    surface_op={"op": "replace", "start_seq": 2, "end_seq": 4},
    source_event_seqs=[2, 3, 4],
)
s.append("assistant/message", {"text": "已为你查询完毕"})

nodes, replacements = fold_surface(s.log)
print("\n[日志] 共 %d 条事件（压缩没有删任何一条）" % len(s.log))
print("[surface nodes] ", nodes)
print("[replace 记录] ", replacements)
print("\n[模型视图] —— seq2-4 不见了，被 seq7 的摘要取代")
for m in s.derive_messages():
    print("   ", m)
print("[人类视图] —— seq2-4 是 append-origin，仍然在")
for m in s.transcript():
    print("   ", m)
print("   → 同一份日志，模型看到 4 条、用户看到 6 条，谁都没改日志")

# ---------------------------------------------------------------- 场景 3
hr("场景 3：模型可见 ⟺ 已记录")
s2 = Session()
s2.append("user/message", {"text": "正常问题"})
# 模拟"临时拼一段系统提示进请求，但不写日志"
s2.log.append(
    {
        "seq": 3,
        "type": "system/message",
        "data": {"text": "临时插入的秘密指令"},
        # 故意不带 surfaceOp —— 上游这类事件是 log-only
    }
)
s2.append("assistant/message", {"text": "回答"})
print("\n[日志] 共 %d 条；seq2 有文本但没有 surfaceOp" % len(s2.log))
print("[模型视图] —— 临时指令没有 surfaceOp，被 derive 正确跳过")
for m in s2.derive_messages():
    print("   ", m)
print("   → 重放这段日志，得到的模型输入一模一样：可复现")

# ---------------------------------------------------------------- 场景 4
hr("场景 4：崩溃恢复 —— 补记事件走同一条折叠路径")
crash = Session()
crash.append("turn/start", {"turn": 1})
crash.append("step/start", {"turn": 1, "step": 1})
crash.append("user/message", {"text": "开始任务"})
crash.append("tool/call", {"id": "c1", "name": "weather"})
# 模拟崩溃：没有 step/end、没有 turn/end、没有 tool/result

closers = interrupted_closers(crash.log)
print("\n[补记事件] 崩溃检测出 %d 条缺失收尾：" % len(closers))
for c in closers:
    print("   ", c["type"], c["data"])

recovered = list(crash.log) + closers
print("\n[重放恢复后] 日志 %d 条 → %d 条" % (len(crash.log), len(recovered)))
msgs1, repl1 = replay(crash.log)
msgs2, repl2 = replay(recovered)
print("[崩溃前视图] ", msgs1)
print("[恢复后视图] ", msgs2)
print("[两次重放一致?] ", msgs1 == msgs2)
print("   → 视图不同是预期的：补记的 tool/result 是新增事实，恢复后模型应看到它")
print("   → 关键是补记事件走的是同一个 fold 路径，重放不是加载第二份聊天记录")

hr("四个场景结束")
