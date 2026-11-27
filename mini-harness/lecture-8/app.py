"""第 8 讲：统一装配入口。

创建按依赖顺序，关闭按逆序。setup 阶段注册的 agent 本地贡献先于
第一次提示词组装，对应等 agent/created 完成才放输入。
"""

from gate_core import Tool, ToolRegistry, Verdict
from seam_core import Context, LocalShell, ScriptModel
from session_core import MemoryPersistence, Session, diag
from driver_core import Driver


def allow_once(call, next_fn):
    """审批监听器：本案只放行 calculator，其余交给下一个。"""
    if call["name"] == "calculator":
        diag(f"        [approve] {call['name']} 放行一次")
        return Verdict.ALLOW
    return next_fn(call)


def build(script, model_impl=None, shell_impl=None, extra_listeners=None):
    """按序装配。返回 driver 与 session，供 demo 驱动。"""
    diag("[build] 1. Session 日志与持久化插件")
    persistence = MemoryPersistence()
    session = Session(persistence)

    diag("[build] 2. 服务键装配：模型与 shell")
    ctx = Context()
    ctx.provide("shell", shell_impl or LocalShell())

    diag("[build] 3. 工具清单与闸门监听器")
    registry = ToolRegistry()
    registry.register(Tool("calculator", {"a": "number", "b": "number"}, None, "shell"))
    listeners = [allow_once] + (extra_listeners or [])

    diag("[build] 4. 模型 Provider")
    model = model_impl or ScriptModel(script)

    diag("[build] 5. Driver 装配，setup 贡献先于第一次组装")
    driver = Driver(model, session, registry, ctx, listeners)
    return driver, session


def run_task(script, seed, model_impl=None, shell_impl=None, extra_listeners=None, shutdown=False):
    """端到端跑一次任务，返回结果字典。诊断走 stderr。"""
    driver, session = build(script, model_impl, shell_impl, extra_listeners)
    driver.wake(seed)
    result = {
        "turns": driver.turn_no,
        "steps": driver.step_no,
        "end": session.log[-1]["data"].get("reason") if session.log else None,
        "messages": session.derive_messages(),
        "causal": session.validate_causality(),
        "durable": len(session.persistence.durable),
        "buffered": len(session.persistence.buffer),
    }
    if shutdown:
        driver.close()
        result["closed"] = driver.closed
        result["durable_after_close"] = len(session.persistence.durable)
    return result
