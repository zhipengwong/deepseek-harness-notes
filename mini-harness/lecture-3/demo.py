"""第 3 讲基线演示：三层循环、完成判定、多轮驱动、取消、max-tokens 粘性。

运行：python3 demo.py
"""

from loop_core import Driver, FakeModel, Inbox, Session


def make_driver(script):
    return Driver(model=FakeModel(script), inbox=Inbox(), session=Session())


def show_log(driver, title):
    print(f"  --- {title}（日志只追加，不改写）---")
    for event in driver.session.events:
        if event["type"] in ("turn/start", "step/start", "step/end", "turn/end"):
            print(f"    #{event['seq']:02d} {event['type']:12s} {event['data']}")


print("#" * 60)
print("# 场景 1：工具调用在 turn 层，完成判定看有没有 tool-call")
print("#" * 60)
# 同一轮里调 3 次工具：tools 非空 → 回灌 next-step → 回到 step 循环。
# 第 4 步 tools 为空 → completed → turn 结束。
d = make_driver([
    {"text": "查天气", "tools": ["weather"]},
    {"text": "查地图", "tools": ["map"]},
    {"text": "查汇率", "tools": ["fx"]},
    {"text": "三件事都办好了", "tools": []},
])
d.wake(seed="帮我查天气、地图和汇率")
show_log(d, "三次工具调用 + 完成判定")
print("  观察：3 次工具调用都在 turn 1 内；无 tool-call 后 turn 才结束。\n")


print("#" * 60)
print("# 场景 2：追加新输入 → driver 再开一轮")
print("#" * 60)
# :423 hasPending 决定 turn() 返回 true/false。
# 第一条答完后 followup 往 next-turn 塞入新消息 → inbox 非空 → turn() 返回 true → driver 再开一轮。
d = make_driver([
    {"text": "回答第一条", "tools": [], "followup": "用户追加：第二条消息"},
    {"text": "回答第二条，没有后续输入了", "tools": []},
])
d.wake(seed="第一条消息")
show_log(d, "两个 turn 的边界")
print("  观察：turn 1 结束时 followup 塞入第二条 → turn() 返回 true → driver 再开 turn 2；")
print("  turn 2 后 inbox 空，driver 停。追加输入走的是 driver 层，不是 turn 层。\n")


print("#" * 60)
print("# 场景 3：取消 → 当前 turn 中断，默认清空 inbox")
print("#" * 60)
d = make_driver([{"text": "处理中", "tools": []}])
d.inbox.send("正在处理的输入", "next-turn")
d.inbox.send("排队待处理的输入", "next-turn")
# trigger_cancel 模拟外部取消：abort 当前 phase + 清空 inbox
d.model.script[0]["trigger_cancel"] = "user"
d.wake()
print("  观察：turn 记为 aborted(user)；两条输入被清空，agent 本身未销毁。\n")


print("#" * 60)
print("# 场景 4：max-tokens 粘性 → 后续 completed 不降级")
print("#" * 60)
d = make_driver([
    {"text": "输出触顶", "tools": ["tool_a"], "max_tokens": True},
    {"text": "后续又调一次工具", "tools": ["tool_b"]},
    {"text": "最终正常完成", "tools": []},
])
d.wake(seed="触发一次输出截断")
show_log(d, "max-tokens 粘性")
print("  观察：三步里第一步 max-tokens，后两步正常推进；turn/end 仍记 max-tokens。")
print("  因为 turn_ends 一旦是 max-tokens 就不再被覆盖。\n")


print("=" * 60)
print("全部演示结束。四个场景对应讲义的四节核心：")
print("  1 完成判定  2 inbox 驱动  3 取消语义  4 粘性终态")
print("=" * 60)
