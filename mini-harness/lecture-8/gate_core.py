"""第 8 讲：工具清单与执行闸门，对应第 5 讲的注册、审批、调度回灌。

三件事接进这条链：
  - 注册工具，给模型的 schema 只含名字与参数，不含 execute 与审批元数据
  - 审批 waterfall，失败关闭，无人接手用 default 兜底
  - 执行器与模型顺序一致，审批拒绝也落成规范 tool/result
"""

from session_core import diag


class Tool:
    def __init__(self, name, params, execute, shell_key=None):
        self.name = name
        self.params = params
        self.execute = execute
        self.shell_key = shell_key  # 只注入服务键，不 import 具体实现

    def prompt_view(self):
        """给模型的只有名字和参数，宿主字段一律不外泄。"""
        return {"name": self.name, "parameters": dict(self.params)}


class ToolRegistry:
    def __init__(self):
        self.tools = {}

    def register(self, tool):
        self.tools[tool.name] = tool
        return lambda: self.tools.pop(tool.name, None)

    def schemas(self):
        return [t.prompt_view() for t in self.tools.values()]

    def get(self, name):
        return self.tools.get(name)


class Verdict:
    ALLOW = "allowed-once"
    DENY = "denied"


def waterfall(listeners, value, default):
    """按注册顺序裁决，任一个监听器不调用 next 即终结。"""
    def run(index, current):
        if index >= len(listeners):
            return default
        return listeners[index](current, lambda nxt: run(index + 1, nxt))
    return run(0, value)


def approve(call, listeners):
    """失败关闭：没有监听器或抛错都用 default 拒绝。"""
    def default(_):
        return Verdict.DENY
    try:
        return waterfall(listeners, call, default)
    except Exception as exc:
        diag(f"        [gate] 审批异常，失败关闭：{exc}")
        return Verdict.DENY


def execute_batch(registry, calls, listeners, shells):
    """执行一批调用，保持模型顺序。每一项都落成规范的 tool/result。"""
    results = []
    for call in calls:
        name = call["name"]
        verdict = approve(call, listeners)
        if verdict != Verdict.ALLOW:
            diag(f"        [gate] {name} 被拒：{verdict}")
            results.append({"name": name, "text": f"error: {verdict}", "ok": False})
            continue
        tool = registry.get(name)
        if tool is None:
            results.append({"name": name, "text": "error: unknown-tool", "ok": False})
            continue
        try:
            if tool.shell_key is not None:
                text = shells[tool.shell_key].run(**call["args"])
            else:
                text = tool.execute(**call["args"])
            diag(f"        [exec] {name} {call['args']} -> {text}")
            results.append({"name": name, "text": text, "ok": True})
        except Exception as exc:
            results.append({"name": name, "text": f"error: {exc}", "ok": False})
    return results
