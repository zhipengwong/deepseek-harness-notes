# 最小插件框架：注册、生命周期、effect、事件分发。
# 参照 Cordis 的设计，用最少的代码说明「一切皆插件」的核心机制。
# 配套讲义：docs/course/lecture-2-plugin.md
from enum import Enum, auto


class FiberState(Enum):
    # 一个插件实例的六种状态。对照上游 fiber.ts 的 FiberState 枚举。
    PENDING = auto()      # 已声明，等待依赖
    LOADING = auto()      # apply 正在执行
    ACTIVE = auto()       # 已加载
    FAILED = auto()       # apply 抛异常
    UNLOADING = auto()    # 清理中
    DISPOSED = auto()     # 已卸载


class Fiber:
    """一个已加载插件实例的运行时句柄。"""
    def __init__(self, name):
        self.name = name
        self.state = FiberState.PENDING
        self.disposers = []       # 逆序执行的清理函数
        self.children = []        # 子 fiber，父卸载时一起卸载

    def add_disposer(self, fn):
        self.disposers.append(fn)

    def dispose(self):
        if self.state in (FiberState.UNLOADING, FiberState.DISPOSED):
            return
        self.state = FiberState.UNLOADING
        # 子插件先卸载，再逆序执行本插件的清理函数。
        for child in reversed(self.children):
            child.dispose()
        for fn in reversed(self.disposers):
            fn()
        self.disposers.clear()
        self.children.clear()
        self.state = FiberState.DISPOSED


class Context:
    """插件拿到的上下文。插件通过它注册自己贡献的一切。"""
    def __init__(self, app, name, parent=None):
        self.app = app
        self.name = name
        self.fiber = Fiber(name)
        self.parent = parent
        if parent is not None:
            parent.fiber.children.append(self.fiber)

    def effect(self, setup):
        """注册一个外部资源。setup 立即运行，返回清理函数。"""
        disposer = setup()
        if disposer is not None:
            self.fiber.add_disposer(disposer)
        return disposer

    def on(self, event, listener):
        """注册事件监听器。这是 effect，卸载时自动移除。"""
        self.app.listeners.setdefault(event, []).append(listener)
        self.fiber.add_disposer(
            lambda: self.app.listeners[event].remove(listener)
        )

    def emit(self, event, *args):
        """同步广播。不收集返回值。"""
        for listener in list(self.app.listeners.get(event, [])):
            listener(*args)

    def waterfall(self, event, value, default):
        """链式转换。监听器拿到 value 和 next，可改写或短路。"""
        listeners = list(self.app.listeners.get(event, []))

        def run(index, current):
            if index >= len(listeners):
                return default(current)
            return listeners[index](current, lambda v: run(index + 1, v))

        return run(0, value)

    def plugin(self, fn, name=None):
        """挂载子插件，返回它的 fiber。"""
        return self.app.load(fn, name=name, parent=self)


class App:
    """根。加载插件、持有事件表、驱动生命周期。"""
    def __init__(self):
        self.listeners = {}
        self.root = Context(self, "root")
        self.plugins = []

    def load(self, fn, name=None, parent=None):
        plugin_name = name or getattr(fn, "name", fn.__name__)
        ctx = Context(self, plugin_name, parent)
        ctx.fiber.state = FiberState.LOADING
        try:
            fn(ctx)
        except Exception:
            ctx.fiber.state = FiberState.FAILED
            raise
        ctx.fiber.state = FiberState.ACTIVE
        self.plugins.append(ctx.fiber)
        return ctx.fiber

    def dispose(self):
        for fiber in reversed(self.plugins):
            fiber.dispose()
