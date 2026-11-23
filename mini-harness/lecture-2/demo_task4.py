# 第 2 讲选做任务：waterfall 监听器不调 next() 会怎样。
# 运行：python3 demo_task4.py
#
# 上游铁律（vendor/cordis/src/events.ts 的 waterfall 实现）：
# 监听器不返回 next(...) 时，链条在这里终止——它自己的返回值
# 就是最终结果，下游监听器和 default 全部被跳过。
# 所以「只观察不加工」的监听器必须写 return next(value)。
from plugin_core import App


def buggy_observer(ctx):
    """坏例子：只想旁观，忘了把值传下去。"""
    def handle(text, next):
        print(f"  [buggy] 旁听到了: {text!r}（但没有调 next）")
        return None  # 等价于忘了 return next(text)
    ctx.on("render", handle)


def good_observer(ctx):
    """正确写法：只观察也要接力。"""
    def handle(text, next):
        print(f"  [good] 旁听到了: {text!r}，调 next 放行")
        return next(text)
    ctx.on("render", handle)


def terminal(ctx):
    """链尾：把值加工成最终结果。"""
    ctx.on("render", lambda text, next: f"<{text}>")


def run_case(title, plugins):
    print(f"=== {title} ===")
    app = App()
    for p in plugins:
        app.load(p)
    result = app.root.waterfall("render", "hello", default=lambda t: f"DEFAULT({t})")
    print(f"  最终结果: {result!r}\n")


def main():
    # 场景 1：旁观者忘了 next() -> 链断在这里，terminal 和 default 都没跑。
    run_case("坏例子：旁观者不调 next", [buggy_observer, terminal])

    # 场景 2：旁观者正确接力 -> 链完整走到 terminal，再兜底到 default
    # （terminal 返回后链条结束，default 只在没人接手时才用）。
    run_case("正确写法：旁观者调 next", [good_observer, terminal])

    # 场景 3：整条链都没人接手 -> default 兜底。
    run_case("对照组：链上没有监听器", [])


if __name__ == "__main__":
    main()
