"""最小会话驱动器：三层循环 + inbox 驱动 + 终止判定 + 取消。

结构对应上游 agent-loop/src/agent.ts：
  - kick() = driver 层 (agent.ts:273)
  - turn() = turn 层   (agent.ts:340)
  - step() = step 层   (agent.ts:439)

省略并发工具、崩溃恢复与插件拦截。全部离线运行。
"""

from dataclasses import dataclass, field


class Aborted(Exception):
    """signal.throw_if_aborted() 抛出的协作式取消异常。"""

    def __init__(self, cause):
        self.cause = cause
        super().__init__(f"aborted: {cause}")


class AbortSignal:
    """简化版 AbortController：协作式取消的信号载体。"""

    def __init__(self):
        self.aborted = False
        self.cause = None

    def abort(self, cause):
        self.aborted = True
        self.cause = cause

    def throw_if_aborted(self):
        if self.aborted:
            raise Aborted(self.cause)


class Inbox:
    """两级收件箱。next-turn 驱动 driver，next-step 驱动 turn 内多步。

    对应 agent.ts:423 的 hasPending 判定——它就是 driver 要不要再跑一轮的依据。
    """

    def __init__(self):
        self.next_turn = []
        self.next_step = []

    def send(self, text, target):
        bucket = self.next_turn if target == "next-turn" else self.next_step
        bucket.append(text)
        print(f"      [inbox] +{target}: {text}")

    @property
    def has_pending(self):
        return bool(self.next_turn or self.next_step)

    def claim(self, target):
        """取出并清空目标队列，返回被认领的输入。"""
        bucket = self.next_turn if target == "next-turn" else self.next_step
        taken = list(bucket)
        bucket.clear()
        return taken

    def clear(self):
        self.next_turn.clear()
        self.next_step.clear()
        print("      [inbox] 已清空（cancel 的默认行为）")


class Session:
    """append-only 日志。终态写完不改，对应 turn/end 的粘性。"""

    def __init__(self):
        self.events = []

    def append(self, etype, data):
        event = {"seq": len(self.events) + 1, "type": etype, "data": dict(data)}
        self.events.append(event)
        print(f"      [log#{event['seq']:02d}] {etype} {data}")
        return event


class FakeModel:
    """脚本化模型。每条回复可带 tools / max_tokens / followup / trigger_cancel。

    - tools 非空：执行工具并把结果回灌 next-step，循环继续（同一 turn）
    - tools 空：本步完成（completed）
    - max_tokens：触顶（粘性），可与 tools 共存
    - followup：模拟用户在下一轮追问，写入 next-turn
    """

    def __init__(self, script):
        self.script = list(script)
        self.cursor = 0

    def current(self):
        reply = self.script[self.cursor] if self.cursor < len(self.script) else {"text": "(无更多回复)", "tools": []}
        self.cursor += 1
        return reply


@dataclass
class Driver:
    model: FakeModel
    inbox: Inbox
    session: Session

    phase: str = "idle"
    turn_no: int = 0
    step_no: int = 0
    abort: AbortSignal = field(default_factory=AbortSignal)

    def wake(self, seed=None, target="next-turn"):
        """wakeDriver()：放入初始输入，建立 running phase 并启动 driver。"""
        if seed is not None:
            self.inbox.send(seed, target)
        if self.phase != "idle":
            print("  [wake] 已有活跃 driver，忽略本次唤醒")
            return
        self.phase = "running"
        self.kick()

    def kick(self):
        """driver 层：while (await turn())。对应 agent.ts:273。"""
        print("\n=== kick：driver 循环启动 ===")
        try:
            while self.turn():
                print("  [driver] turn() 返回 True → 再开一轮")
        finally:
            self.phase = "idle"
            print("=== kick：phase 归位 idle ===\n")

    def turn(self):
        """turn 层：一个回合内的多步。返回是否还要开下一轮。对应 agent.ts:323。"""
        if self.phase != "running":
            raise RuntimeError("turn outside running phase")
        signal = self.abort
        signal.throw_if_aborted()

        self.turn_no += 1
        turn = self.turn_no
        self.session.append("turn/start", {"turn": turn})
        turn_ends = None
        target = "next-turn"

        print(f"  --- turn {turn} 开始 ---")
        try:
            while True:
                signal.throw_if_aborted()
                self.step_no += 1
                step = self.step_no
                messages = self.inbox.claim(target)
                print(f"    [step {turn}.{step}] target={target}，认领 {len(messages)} 条输入")

                step_end = self.step(step, messages, signal)

                # max-tokens 粘性：先到的 max-tokens 不被后续 completed 降级
                if step_end is not None:
                    if turn_ends is None or turn_ends != "max-tokens":
                        turn_ends = step_end

                # turn-stopping 检查点：监听器可往 inbox 塞输入让循环续跑
                if turn_ends and not self.inbox.next_step:
                    print("      [hook] agent/turn-stopping 检查点")

                if turn_ends and not self.inbox.next_step:
                    break
                target = "next-step"
        except Aborted as exc:
            turn_ends = f"aborted({exc.cause})"
            print(f"    [cancel] turn {turn} 被打断：{exc.cause}")
        finally:
            self.session.append("turn/end", {"turn": turn, "reason": turn_ends})

        print(f"  --- turn {turn} 结束：{turn_ends} ---")

        # 对应 agent.ts:423：没有待处理输入就停，有则开下一轮
        if not self.inbox.has_pending:
            return False
        self.step_no = 0
        self.abort = AbortSignal()  # 新一轮换 controller
        return True

    def step(self, step, messages, signal):
        """step 层：一次模型调用 + 完成判定。对应 agent.ts:431。

        返回 step 终态：'completed' / 'max-tokens' / None（有工具调用，继续循环）。
        """
        signal.throw_if_aborted()
        turn = self.turn_no
        self.session.append("step/start", {"turn": turn, "step": step})

        reply = self.model.current()
        print(f"      [model] {reply['text']}，tools={reply.get('tools', [])}")

        if reply.get("trigger_cancel"):
            self.cancel(reply["trigger_cancel"])

        self.session.append("step/end", {"turn": turn, "step": step})

        step_end = None
        if reply.get("max_tokens"):
            step_end = "max-tokens"

        tools = reply.get("tools", [])
        if not tools:
            if step_end is None:
                step_end = "completed"
        else:
            for tool in tools:
                self.inbox.send(f"{tool} 的结果", "next-step")

        if reply.get("followup"):
            self.inbox.send(reply["followup"], "next-turn")

        signal.throw_if_aborted()
        return step_end

    def cancel(self, cause="user", keep_inbox=False):
        """cancel()：默认清空 inbox，然后 abort 当前 phase。对应 agent.ts:189。"""
        print(f"\n  [cancel] cause={cause}，keepInbox={keep_inbox}")
        if not keep_inbox:
            self.inbox.clear()
        if self.phase != "idle":
            self.abort.abort(cause)
