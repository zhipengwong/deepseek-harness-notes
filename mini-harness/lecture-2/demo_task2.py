# 第 2 讲动手任务 2：新增第三个插件，验证它是否自动收到事件。
# 基线 demo.py 保持不动。运行：python3 demo_task2.py
from plugin_core import App


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

    ctx.on("greet", lambda name: print(f"  [greeter] 收到 greet: {name}"))


def shouter(ctx):
    """另一个插件。也监听同一事件。"""
    print(f"[加载] {ctx.name}")
    ctx.on("greet", lambda name: print(f"  [shouter] 收到 greet: {name}"))


def echoer(ctx):
    """任务 2 新增的插件。与另外两个互不认识，只订阅同一事件。"""
    print(f"[加载] {ctx.name}")
    ctx.on("greet", lambda name: print(f"  [echoer] 收到 greet: {name}"))


def main():
    app = App()
    print("=== 加载插件 ===")
    app.load(greeter, name="greeter")
    app.load(shouter, name="shouter")
    echoer_fiber = app.load(echoer, name="echoer")

    print("\n=== 事件广播 emit ===")
    app.root.emit("greet", "world")

    print("\n=== 卸载 echoer 后再广播 ===")
    echoer_fiber.dispose()
    print("  [echoer] 已卸载")
    app.root.emit("greet", "again")


if __name__ == "__main__":
    main()
