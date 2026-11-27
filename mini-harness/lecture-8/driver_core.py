"""第 8 讲：driver 把六块串成一条循环。

对应第 3 讲的三层循环，并接上日志、闸门与 seam。顺序是关键不变量：
  1. 领取 inbox 输入，打开 turn
  2. 用户消息先入日志，再派生请求
  3. assistant/message 追加后，才分派工具
  4. tool/result 规范回灌，下一轮从日志派生
取消没有内置轮次预算。关停先停再排空最后释放。
"""

from gate_core import execute_batch
from session_core import diag


class Aborted(Exception):
    def __init__(self, cause):
        self.cause = cause
        super().__init__(cause)


class AbortSignal:
    def __init__(self):
        self.cause = None

    def abort(self, cause):
        if self.cause is None:
            self.cause = cause

    def throw_if_aborted(self):
        if self.cause is not None:
            raise Aborted(self.cause)


class Inbox:
    def __init__(self):
        self.next_turn = []
        self.next_step = []

    def send(self, text, target):
        (self.next_turn if target == "next-turn" else self.next_step).append(text)

    def claim(self, target):
        queue = self.next_turn if target == "next-turn" else self.next_step
        claimed = list(queue)
        queue.clear()
        return claimed

    def has_pending(self):
        return bool(self.next_turn or self.next_step)

    def clear(self):
        self.next_turn.clear()
        self.next_step.clear()


class Driver:
    def __init__(self, model, session, registry, ctx, listeners, inbox=None):
        self.model = model
        self.session = session
        self.registry = registry
        self.ctx = ctx
        self.listeners = listeners
        self.inbox = inbox or Inbox()
        self.signal = AbortSignal()
        self.phase = "idle"
        self.turn_no = 0
        self.step_no = 0
        self.closed = False

    def wake(self, seed):
        """创建就绪后才放输入。对应等 agent/created 完成才释放排队输入。"""
        if self.closed:
            raise RuntimeError("driver 已关闭")
        self.inbox.send(seed, "next-turn")
        if self.phase != "idle":
            diag("  [wake] 已有活跃 driver，忽略本次唤醒")
            return
        self.phase = "running"
        self.kick()

    def kick(self):
        """driver 层：while turn()。"""
        try:
            while self.turn():
                pass
        finally:
            self.phase = "idle"
            diag("  [driver] phase 归位 idle")

    def turn(self):
        """turn 层：一个回合内的多步。返回是否开下一轮。"""
        self.signal.throw_if_aborted()
        self.turn_no += 1
        turn = self.turn_no
        self.session.append("turn/start", {"turn": turn})
        reason = None
        target = "next-turn"
        try:
            while True:
                self.signal.throw_if_aborted()
                self.step_no += 1
                step = self.step_no
                messages = self.inbox.claim(target)
                diag(f"    [step {turn}.{step}] 认领 {len(messages)} 条，target={target}")
                reason = self.step(turn, step, messages)
                if reason is not None:
                    break
                target = "next-step"
        except Aborted as exc:
            reason = f"aborted({exc.cause})"
            diag(f"    [cancel] turn {turn} 被打断：{exc.cause}")
        finally:
            self.session.append("turn/end", {"turn": turn, "reason": reason})

        if not self.inbox.has_pending():
            return False
        self.step_no = 0
        self.signal = AbortSignal()
        return True

    def step(self, turn, step, messages):
        """step 层：先落日志再派生，assistant 落日志后才分派工具。"""
        self.signal.throw_if_aborted()
        self.session.append("step/start", {"turn": turn, "step": step})

        # 顺序不变量一：用户消息在请求派生前入日志
        for text in messages:
            self.session.append("user/message", {"text": text})
        schemas = self.registry.schemas()
        derived = self.session.derive_messages()
        diag(f"      [derive] {len(derived)} 条可见消息，{len(schemas)} 个工具 schema")

        reply = self.model.current()

        # 顺序不变量二：assistant 追加后才分派工具
        self.session.append("assistant/message", {"text": reply["text"]})
        calls = reply.get("tools", [])
        if calls:
            shells = {"shell": self.ctx.get("shell")}
            results = execute_batch(self.registry, calls, self.listeners, shells)
            for item in results:
                self.session.append("tool/result", {"text": item["text"], "name": item["name"], "ok": item["ok"]})
                self.inbox.send(f"{item['name']}: {item['text']}", "next-step")

        # followup 进 next-turn，模拟用户在下一轮追问
        if reply.get("followup"):
            self.inbox.send(reply["followup"], "next-turn")
            diag(f"      [followup] 下一轮输入：{reply['followup']}")

        # 一轮结束的持久检查点
        self.session.flush()
        self.signal.throw_if_aborted()

        if reply.get("max_tokens"):
            return "max-tokens"
        if not calls and not self.inbox.next_step:
            return "completed"
        return None

    def cancel(self, cause="user", keep_inbox=False):
        """取消。默认清空 inbox，keepInbox 保留待处理工作。"""
        diag(f"  [cancel] cause={cause}，keepInbox={keep_inbox}")
        if not keep_inbox:
            self.inbox.clear()
        if self.phase != "idle":
            self.signal.abort(cause)

    def close(self):
        """关停逆序：先停并排空，再释放资源。"""
        diag("  [close] 1. 停止接新并排空 driver")
        if self.phase != "idle":
            self.cancel("shutdown", keep_inbox=True)
            self.phase = "idle"
        diag("  [close] 2. 显式 flush 持久屏障")
        self.session.flush()
        diag("  [close] 3. 释放作用域与句柄")
        self.closed = True
