"""第 8 讲演示：端到端任务把六块拼成一条链。

四个场景对应讲义四条动手任务。全部离线运行，只用标准库。
诊断就地捕获后随场景打印，结果只走 stdout。运行：python3 demo.py
"""

import contextlib
import io
import json

from app import build, run_task
from gate_core import Verdict
from seam_core import EchoModel, SandboxShell


def hr(title):
    print("=" * 62)
    print(title)
    print("=" * 62)


def capture(fn):
    """捕获诊断，返回 (函数结果, 诊断文本)。保证场景内顺序可复现。"""
    buf = io.StringIO()
    with contextlib.redirect_stderr(buf):
        result = fn()
    return result, buf.getvalue()


def show(label, result):
    print(f"  [{label}] {json.dumps(result, ensure_ascii=False)}")


# ---------------------------------------------------------------- 场景 1
hr("场景 1：端到端跑一次带工具的任务")
script = [
    {"text": "先算一下 2 加 3", "tools": [{"name": "calculator", "args": {"a": 2, "b": 3}}]},
    {"text": "结果是 5，还要继续吗", "followup": "谢谢，再确认一次"},
    {"text": "已确认，任务完成"},
]
result, diag1 = capture(lambda: run_task(script, "帮我算 2 加 3"))
print(diag1, end="")
show("result", result)
print("  → 两轮以上，中间一次工具调用，消息历史从日志派生")

# ---------------------------------------------------------------- 场景 2
hr("场景 2：审批拒绝落成规范结果，换 shell 不改 driver")
def deny_danger(call, next_fn):
    return Verdict.DENY

script2 = [
    {"text": "试两个工具", "tools": [
        {"name": "calculator", "args": {"a": 7, "b": 8}},
        {"name": "danger_tool", "args": {"path": "/tmp/x"}},
    ]},
    {"text": "一个成功一个被拒，继续"},
]
result2, diag2 = capture(
    lambda: run_task(script2, "批量试工具", shell_impl=SandboxShell(), extra_listeners=[deny_danger])
)
print(diag2, end="")
show("result", result2)
print("  → 被拒工具也落成 tool/result，换了 shell 实现，driver 未改")

# ---------------------------------------------------------------- 场景 3
hr("场景 3：取消语义与关停清理顺序")
def scene3():
    driver, session = build([{"text": "长任务"}])
    driver.wake("开始")
    driver.inbox.send("排队中的后续输入", "next-step")
    pending_before = driver.inbox.has_pending()
    driver.cancel("user")
    pending_after = driver.inbox.has_pending()
    driver.close()
    return {
        "pending_before": pending_before,
        "pending_after_cancel": pending_after,
        "closed": driver.closed,
        "durable": len(session.persistence.durable),
        "buffer": len(session.persistence.buffer),
    }

result3, diag3 = capture(scene3)
print(diag3, end="")
show("result", result3)
print("  → 默认 cancel 清空 inbox，close 先停再 flush 最后释放")

# ---------------------------------------------------------------- 场景 4
hr("场景 4：换模型 Provider，driver 一行不改")
def scene4():
    r_script = run_task([{"text": "脚本模型回复"}], "用脚本模型")
    r_echo = run_task([], "用回显模型", model_impl=EchoModel())
    return {"script": {"turns": r_script["turns"], "end": r_script["end"]},
            "echo": {"turns": r_echo["turns"], "end": r_echo["end"]}}

result4, diag4 = capture(scene4)
print(diag4, end="")
show("result", result4)
print("  → 两次装配只换了 model 实现，driver 与闸门未动")

# ---------------------------------------------------------------- 收尾
hr("验收")
checks = [
    ("端到端两轮带工具", result["turns"] >= 2 and any(m["role"] == "tool" for m in result["messages"])),
    ("审批失败关闭落规范结果", result2["causal"][0] and any("denied" in m["content"] for m in result2["messages"])),
    ("取消清空 inbox", not result3["pending_after_cancel"]),
    ("关停后缓冲排空", result3["buffer"] == 0),
    ("换实现不改 driver", result4["echo"]["turns"] >= 1),
]
for name, ok in checks:
    print(f"  [{'通过' if ok else '失败'}] {name}")
print()
print(json.dumps({"exit": 0 if all(ok for _, ok in checks) else 1}))
