"""第 5 讲演示：注册与卸载、审批闸门、乱序按序回灌、吞链默认拒绝。

四个场景对应讲义的四条动手任务。全部离线运行，只用标准库。
"""

from tools_core import (
    DEFAULT_MAX_PARALLEL_TOOL_CALLS,
    Dispatcher,
    PluginHost,
    Tool,
    Verdict,
    approve,
)


def hr(title):
    print(f"\n{'=' * 62}\n{title}\n{'=' * 62}")


# ---------------------------------------------------------------- 场景 1
hr("场景 1：工具注册表，按插件状态重建清单")
host = PluginHost()


def weather_plugin(h):
    stop = h.registry.register(Tool(
        name="get_weather",
        description="查询城市天气，返回温度与状况",
        parameters={"city": "string"},
        execute=lambda city: f"{city} 晴 25C",
    ))
    return stop


def calc_plugin(h):
    return h.registry.register(Tool(
        name="calculator",
        description="计算两个数的和",
        parameters={"a": "number", "b": "number"},
        execute=lambda a, b: a + b,
    ))


host.load("weather", weather_plugin)
host.load("calc", calc_plugin)
print("\n[清单 resolve]", [t.name for t in host.registry.resolve()])
print("[模型视野 prompt_view]")
for item in host.registry.prompt_view():
    print("   ", item)
host.unload("weather")
print("[卸载 weather 后的清单]", [t.name for t in host.registry.resolve()])
print("   → 工具名用于运行时定位，description 才是模型选工具的依据")


# ---------------------------------------------------------------- 场景 2
hr("场景 2：审批闸门，allowed-once 放行与拒绝")
host2 = PluginHost()


def policy_plugin(h):
    """两个应答者串成 waterfall。第一个认领只读调用，第二个拦截危险操作。"""
    def readonly(value, nxt):
        if value["name"] == "get_weather":
            return Verdict.ALLOWED_ONCE
        return nxt(value)

    def block_delete(value, nxt):
        if value["name"] == "delete_file":
            return Verdict.REJECTED
        return nxt(value)

    return [
        h.on_approval(readonly),
        h.on_approval(block_delete),
    ]


host2.load("policy", policy_plugin)
print("  审批链：get_weather 放行，delete_file 拒绝，其余无人认领")
for cid, name in [("c1", "get_weather"), ("c2", "delete_file"), ("c3", "list_dir")]:
    call = {"id": cid, "name": name}
    verdict = approve(host2, call)
    if verdict is Verdict.ALLOWED_ONCE:
        print(f"      [execute] {cid} 放行，进入工具执行")
    else:
        print(f"      [block] {cid} 未放行，不进入执行")


# ---------------------------------------------------------------- 场景 3
hr("场景 3：乱序执行，结果按提交顺序回灌")
print(f"  并发上限 = DEFAULT_MAX_PARALLEL_TOOL_CALLS = {DEFAULT_MAX_PARALLEL_TOOL_CALLS}")
host3 = PluginHost()
host3.load("calc", calc_plugin)
host3.load("weather", weather_plugin)
dispatcher = Dispatcher(host3.registry)

calls = [
    {"id": "a", "name": "get_weather", "finish_after": 3, "args": {"city": "北京"}},
    {"id": "b", "name": "calculator", "finish_after": 1, "args": {"a": 2, "b": 3}},
    {"id": "c", "name": "get_weather", "finish_after": 2, "args": {"city": "上海"}},
]
print("  提交顺序 a, b, c。完成顺序由 finish_after 决定，设为 b, c, a")
replayed = dispatcher.dispatch(calls)
print("\n[回灌结果，按提交顺序]")
for cid, result in zip(["a", "b", "c"], replayed):
    print(f"   {cid}: {result}")
print("   → 执行顺序 b, c, a，回灌顺序 a, b, c，两者不同")

print("\n  加入 exclusive 调用，观察屏障")
calls2 = [
    {"id": "d", "name": "get_weather", "finish_after": 2, "args": {"city": "广州"}},
    {"id": "e", "name": "calculator", "mode": "exclusive", "finish_after": 1, "args": {"a": 7, "b": 8}},
]
replayed2 = dispatcher.dispatch(calls2)
print("[回灌结果]", [f"{cid}:{r}" for cid, r in zip(["d", "e"], replayed2)])


# ---------------------------------------------------------------- 场景 4
hr("场景 4：只观察不调用 next()，下游裁决被吞")
host4 = PluginHost()
host4.load("calc", calc_plugin)


def silent_plugin(h):
    """只观察的监听器。它不调用 next，也不返回裁决。"""
    def silent(value, nxt):
        print(f"      [observe] 看到 {value['name']}，但不调用 next()")

    def allow(value, nxt):
        if value["name"] == "calculator":
            return Verdict.ALLOWED_ONCE
        return nxt(value)

    return [
        h.on_approval(silent),
        h.on_approval(allow),
    ]


host4.load("silent", silent_plugin)
call = {"id": "x", "name": "calculator"}
print("  审批链首是只观察的监听器，链尾本应放行 calculator")
verdict = approve(host4, call)
print(f"   → 裁决 {verdict.value}，调用被默认拒绝，未进入执行")

hr("四个场景结束")
