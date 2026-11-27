"""第 8 讲：append-only 日志与消息派生，作为整条链的唯一事实源。

对应第 4 讲 session_core，保持同样的不变量：
  - log 只追加，不改过去
  - 模型可见消息从日志派生，不另存一份
  - turn/step 边界先入日志，再派生请求
只用标准库，离线运行。诊断写 stderr，不污染结果通道。
"""

import sys

# 能进入模型可见视图的事件类型
SURFACE_TYPES = {"user/message", "assistant/message", "tool/result"}


def diag(msg):
    print(msg, file=sys.stderr)


class Session:
    """唯一事实源。append 同步写内存，flush 是显式的持久屏障。"""

    def __init__(self, persistence=None):
        self.log = []
        self.persistence = persistence
        self.flushed_at = 0

    def append(self, etype, data):
        event = {"seq": len(self.log) + 1, "type": etype, "data": dict(data)}
        self.log.append(event)
        if self.persistence is not None:
            self.persistence.append(event)
        diag(f"  [log#{event['seq']:02d}] {etype} {data}")
        return event

    def derive_messages(self):
        """模型可见视图。只按 surface 事件顺序取，log-only 事件不进。"""
        messages = []
        for event in self.log:
            if event["type"] not in SURFACE_TYPES:
                continue
            text = event["data"].get("text")
            if text:
                messages.append({"role": event["type"].split("/")[0], "content": text})
        return messages

    def flush(self):
        """持久屏障。等所有持久化监听器排空，返回已落盘的事件数。"""
        if self.persistence is not None:
            landed = self.persistence.flush()
            self.flushed_at = len(self.log)
            diag(f"  [flush] 缓冲落盘 {landed} 条，已排空到 seq={self.flushed_at}")
        return self.flushed_at

    def validate_causality(self):
        """检查日志因果：每个 tool/result 之前必须有 user/message。"""
        first_user = None
        for event in self.log:
            if event["type"] == "user/message" and first_user is None:
                first_user = event["seq"]
            if event["type"] == "tool/result":
                if first_user is None or event["seq"] < first_user:
                    return False, f"tool/result#{event['seq']} 早于任何 user/message"
        return True, "每个工具结果都有在前的用户输入"


class MemoryPersistence:
    """模拟延后写入的持久化插件。事件先入缓冲，flush 才落盘。"""

    def __init__(self):
        self.buffer = []
        self.durable = []

    def append(self, event):
        self.buffer.append(event)

    def flush(self):
        self.durable.extend(self.buffer)
        n = len(self.buffer)
        self.buffer.clear()
        return n
