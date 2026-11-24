"""最小 session 日志与投影：append-only 日志 + 双投影 + 遮蔽式压缩 + 崩溃补记。

结构对应上游 packages/core/session：
  - Session.append()      = index.ts:557-570      只追加、不改过去
  - fold_surface()        = surface.ts:609-624     纯折叠，append / replace
  - derive_messages()     = index.ts:778-799       模型可见视图
  - transcript()          = surface.ts:82-92       人类可读视图（append-origin）
  - interrupted_closers() = repair.ts:53-97        崩溃恢复补记

全部离线运行，只用标准库。seq 从 1 开始（上游从 0 开始，这里教学简化）。
"""

# 能进入 surface（模型可见视图）的五类事件，对应 surface.ts:49-56
SURFACE_TYPES = {
    "system/message",
    "developer/message",
    "user/message",
    "assistant/message",
    "tool/result",
}


class Session:
    """append-only 事件日志。log 是唯一事实；模型与人类视图都是它的投影。"""

    def __init__(self):
        self.log = []

    def append(self, etype, data, surface_op=None, source_event_seqs=None):
        """追加一条事件。日志只增不改。对应 index.ts:557-570。

        五类消息事件默认 surface_op='append'；其余事件一律 log-only，
        显式传 surface_op 会被拒绝——对应 types.ts:532-535 的编译期约束。
        """
        if etype in SURFACE_TYPES:
            if surface_op is None:
                surface_op = "append"
        elif surface_op is not None:
            raise ValueError(f"{etype} 不是 surface 事件，不能带 surfaceOp")
        event = {
            "seq": len(self.log) + 1,
            "type": etype,
            "data": dict(data),
        }
        if etype in SURFACE_TYPES:
            event["surface_op"] = surface_op
            if source_event_seqs:
                event["source_event_seqs"] = list(source_event_seqs)
        self.log.append(event)
        print(f"  [log#{event['seq']:02d}] {etype} {data}")
        return event

    def derive_messages(self):
        """模型可见视图：按 surface 节点顺序取出消息。对应 index.ts:778-799。"""
        nodes, _ = fold_surface(self.log)
        messages = []
        for seq in nodes:
            event = self.log[seq - 1]
            msg = message_of(event)
            if msg is not None:
                messages.append(msg)
        return messages

    def transcript(self):
        """人类可读视图：只读 append-origin 事件。对应 surface.ts:82-92。

        replace 副本不进这里——用户看过的对话不因压缩而消失。
        """
        result = []
        for event in self.log:
            if event.get("surface_op") == "append" and event["type"] in SURFACE_TYPES:
                result.append(message_of(event))
        return result


def message_of(event):
    """把一条 surface 事件投影成消息文本。对应 surface.ts:120-152。"""
    data = event["data"]
    text = data.get("text") or data.get("message", {}).get("text")
    if not text:
        return None  # 空内容的助手消息不进视图（index.ts:792-795）
    return f"{event['type']}: {text}"


def fold_surface(events):
    """纯函数：把日志折叠成 surface 节点序列。对应 surface.ts:609-624。

    nodes 存的是 seq 索引，不是事件本体——replace 只动这个索引数组。
    """
    nodes = []
    replacements = []
    for event in events:
        op = event.get("surface_op")
        if op is None:
            continue  # log-only 事件（chunk、边界、压缩记录）不进视图
        seq = event["seq"]
        if op == "append":
            nodes.append(seq)
        elif isinstance(op, dict) and op.get("op") == "replace":
            start_seq, end_seq = op["start_seq"], op["end_seq"]
            start_idx = nodes.index(start_seq)
            end_idx = nodes.index(end_seq)
            shadowed = nodes[start_idx : end_idx + 1]
            cited = set(event.get("source_event_seqs", []))
            missing = set(shadowed) - cited
            if missing:
                raise ValueError(f"replace 未覆盖全部被遮蔽节点：{sorted(missing)}")
            nodes[start_idx : end_idx + 1] = [seq]
            replacements.append(
                {"seq": seq, "start": start_seq, "end": end_seq, "shadowed": shadowed}
            )
    return nodes, replacements


def interrupted_closers(events):
    """崩溃恢复：为未闭合的 turn/step 合成收尾事件。对应 repair.ts:53-97。

    合成的是普通事件——重放走的是与实时追加相同的 fold 路径。
    """
    open_turns = set()
    open_steps = {}
    started_tools = {}
    for event in events:
        t, data = event["type"], event["data"]
        if t == "turn/start":
            open_turns.add(data["turn"])
        elif t == "turn/end":
            open_turns.discard(data["turn"])
        elif t == "step/start":
            open_steps[data["turn"]] = data["step"]
        elif t == "step/end":
            open_steps.pop(data["turn"], None)
        elif t == "tool/call":
            started_tools[data["id"]] = data
        elif t == "tool/result":
            started_tools.pop(data["id"], None)

    closers = []
    next_seq = len(events) + 1
    for turn, step in sorted(open_steps.items()):
        closers.append(
            {"seq": next_seq, "type": "step/end", "data": {"turn": turn, "step": step}}
        )
        next_seq += 1
    for turn in sorted(open_turns):
        closers.append(
            {
                "seq": next_seq,
                "type": "turn/end",
                "data": {"turn": turn, "reason": "interrupted"},
            }
        )
        next_seq += 1
    # 未出结果的工具：合成错误结果，让 replay 每个调用都有确定结果
    for tool_id, data in started_tools.items():
        closers.append(
            {
                "seq": next_seq,
                "type": "tool/result",
                "data": {"id": tool_id, "text": "结果未知（崩溃）", "is_error": True},
                "surface_op": "append",
            }
        )
        next_seq += 1
    return closers


def replay(events):
    """重放 = 把日志重新折叠一遍，不是加载第二份聊天记录。对应 validation.ts:381-390。"""
    restored = Session()
    restored.log = list(events)  # 同一份事件，零拷贝语义上的事实复用
    return restored.derive_messages(), fold_surface(restored.log)[1]
