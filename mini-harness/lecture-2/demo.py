# 第 2 讲演示：用最小插件框架跑通注册、生命周期、事件与拦截。
# 运行：python3 demo.py
from plugin_core import App, FiberState


def heartbeat(ctx):
    """一个子插件。用 effect 管理定时器资源。"""
    def setup():
        print(f"  [{ctx.name}] 启动定时器")
        def cleanup():
            print(f"  [{ctx.name}] 清理定时器")
        return cleanup
    ctx.effect(setup)


def greeter(ctx):
    """主插件。挂载子插件，注册事件监听。"""
    print(f"[加载] {ctx.name}")
    ctx.plugin(heartbeat, name="heartbeat")

    def setup():
        print("  [greeter] 打开连接")
        def cleanup():
            print("  [greeter] 关闭连接")
        return cleanup
    ctx.effect(setup)

    # 任务 3：第二个 effect。验证两点：
    #   1) 卸载时它的清理函数也会执行；
    #   2) 多个 effect 逆序清理（后打开的先关闭，像栈一样）。
    def setup_timer():
        print("  [greeter] 启动计时器")
        def cleanup_timer():
            print("  [greeter] 停止计时器")
        return cleanup_timer
    ctx.effect(setup_timer)

    ctx.on("greet", lambda name: print(f"  [greeter] 收到 greet: {name}"))


def shouter(ctx):
    """另一个插件。也监听同一事件。"""
    print(f"[加载] {ctx.name}")
    ctx.on("greet", lambda name: print(f"  [shouter] 收到 greet: {name}"))


def upper_middleware(ctx):
    """waterfall 监听器。改写下游结果。"""
    ctx.on("render", lambda text, next: next(text).upper())


def veto_middleware(ctx):
    """waterfall 监听器。遇到 blocked 就短路。"""
    def handle(text, next):
        if "blocked" in text:
            return "** veto **"
        return next(text)
    ctx.on("render", handle)


def main():
    app = App()
    print("=== 加载插件 ===")
    greeter_fiber = app.load(greeter, name="greeter")
    app.load(shouter, name="shouter")
    app.load(upper_middleware, name="upper")
    app.load(veto_middleware, name="veto")

    print("\n=== 事件广播 emit ===")
    app.root.emit("greet", "world")

    print("\n=== 链式拦截 waterfall ===")
    for text in ("hello", "blocked words"):
        result = app.root.waterfall("render", text, default=lambda t: t)
        print(f"  render({text!r}) -> {result!r}")

    print("\n=== 卸载主插件（子插件随父一起）===")
    print(f"  greeter 卸载前状态: {greeter_fiber.state.name}")
    greeter_fiber.dispose()
    print(f"  greeter 卸载后状态: {greeter_fiber.state.name}")

    print("\n=== 卸载后事件监听已移除 ===")
    app.root.emit("greet", "again")


if __name__ == "__main__":
    main()
