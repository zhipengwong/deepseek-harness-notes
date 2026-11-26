"""第 6 讲演示：服务键与约定、重复注册拒绝、Consumer 换实现不改、约定类型断言。

四个场景对应讲义的四条动手任务。全部离线运行，只用标准库。
"""

from seam_core import (
    BashTool,
    Context,
    DuplicateServiceError,
    LocalBashExecutor,
    SandboxBashExecutor,
    ShellExecutor,
    assert_contract,
    prompt_schema,
)


def hr(title):
    print(f"\n{'=' * 62}\n{title}\n{'=' * 62}")


# ---------------------------------------------------------------- 场景 1
hr("场景 1：Service Definition 挂服务键，Provider 注册到同一个键")
ctx = Context()
print("  约定 ShellExecutor.service_key =", ShellExecutor.service_key)
print("  约定是带服务键的类，模型 schema 另算一份，两者不绑在一起")
print("[模型 schema]", prompt_schema(BashTool))
print("  装配本地实现")
ShellExecutor.install(ctx, LocalBashExecutor())
print("  按服务键取回", type(ctx.get("shell")).__name__)


# ---------------------------------------------------------------- 场景 2
hr("场景 2：一个 context 只装一个实现，重复注册被拒绝")
ctx2 = Context()
ShellExecutor.install(ctx2, LocalBashExecutor())
print("  已装本地执行器，再装沙箱执行器")
try:
    ShellExecutor.install(ctx2, SandboxBashExecutor())
    print("  未拒绝，异常")
except DuplicateServiceError as exc:
    print(f"  [reject] {exc}")
print("  → 加载期失败，选择权在部署方，不在工具代码里")


# ---------------------------------------------------------------- 场景 3
hr("场景 3：Consumer 只认服务键，换实现时它一行不改")
print("  同一份 BashTool 类，先接本地实现")
ctx_local = Context()
ShellExecutor.install(ctx_local, LocalBashExecutor())
tool_local = BashTool(ctx_local)
print("   [run]", tool_local.run("echo hi"))
print("  再换沙箱实现，BashTool 定义不动")
ctx_sandbox = Context()
ShellExecutor.install(ctx_sandbox, SandboxBashExecutor())
tool_sandbox = BashTool(ctx_sandbox)
print("   [run]", tool_sandbox.run("echo hi"))
print("  → 两次用的都是 BashTool，schema 只有一份，改动只发生在装配处")
print("[模型 schema 仍是]", prompt_schema(BashTool))


# ---------------------------------------------------------------- 场景 4
hr("场景 4：断言实现是约定类型，看直接依赖怎么破坏替换")
print("  断言本地实现是约定类型", assert_contract(ctx_local.get("shell")))
print("  断言沙箱实现是约定类型", assert_contract(ctx_sandbox.get("shell")))
print("  反例：Consumer 若直接 import 具体实现，换实现就得改它自己")


class TightlyCoupledTool:
    """反面演示。直接持有具体实现类，服务键被绕开。"""

    def __init__(self, executor):
        self.executor = executor

    def run(self, spec):
        return self.executor.execute(spec)


tight = TightlyCoupledTool(LocalBashExecutor())
print("   [run]", tight.run("echo hi"))
print("  → 要换成沙箱，必须把 LocalBashExecutor 改成 SandboxBashExecutor 并改这行调用")
print("  → 每个持有具体实现的 Consumer 都要跟着动，这正是 seam 要避免的")

hr("四个场景结束")
