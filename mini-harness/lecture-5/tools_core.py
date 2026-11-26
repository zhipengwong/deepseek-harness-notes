"""最小工具注册、审批闸门与按序回灌。

结构对应上游 packages/core/tools：
  - ToolRegistry.register/resolve = adding-a-tool.zh.md:18-39  注册是副作用，卸载即注销
  - approve() waterfall           = tools/src/events.ts:14       dispatch 前裁决，失败关闭
  - Verdict 四种结果              = contracts.ts:292-307
  - Dispatcher.dispatch()         = batch.ts:3-7                 有界并行 + 屏障 + 按序回灌
  - 并发上限 10                   = constants.ts:5               DEFAULT_MAX_PARALLEL_TOOL_CALLS

省略真实执行器、取消合成结果、重放、压缩 seam 与多路审批应答者。全部离线运行，只用标准库。
"""

from dataclasses import dataclass, field
from enum import Enum


class Verdict(Enum):
    """审批四种结果。只有 ALLOWED_ONCE 放行。"""

    ALLOWED_ONCE = "allowed-once"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
    UNAVAILABLE = "unavailable"


DEFAULT_MAX_PARALLEL_TOOL_CALLS = 10


@dataclass
class Tool:
    """工具定义。name 给运行时定位，description 是模型看到的判断依据。"""

    name: str
    description: str
    parameters: dict = field(default_factory=dict)
    execute: object = None


class ToolRegistry:
    """工具注册表。resolve 按当前插件状态重建清单。"""

    def __init__(self):
        self._tools = {}

    def register(self, tool):
        """注册是副作用。返回注销函数，交给插件的 disposer。"""
        self._tools[tool.name] = tool
        print(f"      [register] +{tool.name}")
        return lambda: self._unregister(tool.name)

    def _unregister(self, name):
        self._tools.pop(name, None)
        print(f"      [dispose]  -{name}")

    def resolve(self):
        """每步重建清单，全量返回。凡在册的工具都进入提示词。"""
        return list(self._tools.values())

    def get(self, name):
        return self._tools.get(name)

    def prompt_view(self):
        """模型视野：只看 description，不看工具名背后的实现。"""
        return [
            {"name": t.name, "description": t.description, "parameters": t.parameters}
            for t in self.resolve()
        ]


class PluginHost:
    """插件宿主。持有注册表与审批应答者，负责装卸与清理。"""

    def __init__(self):
        self.registry = ToolRegistry()
        self._slots = {}        # 插件名 -> disposer 列表
        self._approval = []

    def load(self, name, apply):
        """apply(host) 注册工具与应答者，返回 disposer、列表或 None。"""
        print(f"  [load] {name}")
        extra = apply(self) or []
        if callable(extra):
            extra = [extra]
        self._slots[name] = extra

    def on_approval(self, fn):
        """挂一个审批应答者，随插件卸载一并移除。"""
        self._approval.append(fn)
        return lambda: self._approval.remove(fn)

    def unload(self, name=None):
        """卸载一个插件或全部。逆序清理，工具与应答者随之消失。"""
        names = [name] if name else list(reversed(list(self._slots)))
        label = name if name else "全部插件，逆序清理"
        print(f"  [unload] {label}")
        for slot in names:
            for fn in reversed(self._slots.pop(slot, [])):
                fn()

    def approval_listeners(self, call):
        return list(self._approval)


def waterfall(listeners, value, default):
    """链式裁决，默认失败关闭。

    应答者签名 fn(value, next)，可返回 Verdict 短路，或调用 next(v) 交给
    下一个应答者。后面的应答者仍能返回自己的裁决否决前面的值。只观察却
    不调用 next 也不返回时，结果是 None，也就是吞链。
    """
    def run(index, current):
        if index >= len(listeners):
            return default(current)
        return listeners[index](current, lambda v: run(index + 1, v))

    return run(0, value)


def approve(host, call):
    """dispatch 前的裁决闸门。只有 ALLOWED_ONCE 放行，其余失败关闭。"""
    listeners = host.approval_listeners(call)
    try:
        verdict = waterfall(listeners, call, lambda v: Verdict.UNAVAILABLE)
    except Exception as exc:
        print(f"      [gate] 应答者抛异常 {exc!r} → unavailable")
        verdict = Verdict.UNAVAILABLE
    if verdict is None:
        verdict = Verdict.UNAVAILABLE
        print("      [gate] 链被吞掉，无人认领 → unavailable")
    print(f"      [gate] {call['id']} {call['name']} → {verdict.value}")
    return verdict


class Dispatcher:
    """有界滚动池与按序回灌。"""

    def __init__(self, registry, max_parallel=DEFAULT_MAX_PARALLEL_TOOL_CALLS):
        self.registry = registry
        self.max_parallel = max_parallel

    def dispatch(self, calls):
        """返回按模型提交顺序排列的结果。执行顺序由 finish_after 决定。"""
        results = {}
        batch = []
        for call in calls:
            if call.get("mode") == "exclusive":
                self._run_batch(batch, results)
                batch = []
                print("      [barrier] 池排空，开始 exclusive 调用")
            batch.append(call)
        self._run_batch(batch, results)
        return [results[c["id"]] for c in calls]

    def _run_batch(self, batch, results):
        if not batch:
            return
        if len(batch) > self.max_parallel:
            print(f"      [limit] {len(batch)} 个调用超过上限 {self.max_parallel}，需分批")
        for call in sorted(batch, key=lambda c: c.get("finish_after", 0)):
            tool = self.registry.get(call["name"])
            if tool is None:
                result = "UNKNOWN_TOOL"
            else:
                args = call.get("args", {})
                result = tool.execute(**args)
            results[call["id"]] = result
            print(f"      [done] {call['id']} {call['name']} → {result}")
