"""最小能力 seam：服务键、约定、Provider 与只认约定的 Consumer。

结构对应上游 packages/shell 三件套：
  - ShellExecutor extends Service, super(ctx, 'shell') = shell/src/index.ts:64
    服务键由构造时挂上，是 Service 而非 interface
  - 一个 context 只装一个实现，装第二个加载期报错 = shell/src/index.ts:36
  - LocalBashExecutor extends ShellExecutor = bash-local/src/index.ts:97
    Provider 继承约定，注册到同一个 ctx.shell 键
  - tool-bash 的 inject 含 shell = tool-bash/src/index.ts:36
    Consumer 声明依赖键，不 import 具体实现
  - ctx.shell.execute(spec) = tool-bash/src/index.ts:571
    Consumer 只调约定里的方法

省略 Cordis 的 fiber 挂起、多服务键接线与真实进程执行。全部离线，只用标准库。
"""


class DuplicateServiceError(Exception):
    """重复注册同一服务键。对应加载期失败。"""


class Context:
    """极简 ctx。一个键只挂一个实现，正好对应一个 context 一个执行器。"""

    def __init__(self):
        self._services = {}

    def provide(self, key, impl):
        if key in self._services:
            raise DuplicateServiceError(
                f"服务键 {key!r} 已挂 {type(self._services[key]).__name__}，"
                f"再挂 {type(impl).__name__} 被拒绝"
            )
        self._services[key] = impl
        print(f"      [provide] {key} <- {type(impl).__name__}")

    def get(self, key):
        if key not in self._services:
            raise KeyError(f"服务键 {key!r} 未注册")
        return self._services[key]


class ShellExecutor:
    """Service Definition。约定命令执行能力，服务键是 shell。

    上游这里是 Cordis Service 的抽象类，靠 super(ctx, 'shell') 把键挂到 ctx。
    骨架用类属性 service_key 标键，用 ctx.provide 完成装配，语义对齐。
    """

    service_key = "shell"

    def execute(self, spec):
        raise NotImplementedError

    @classmethod
    def install(cls, ctx, impl):
        """Provider 注册入口。一个 context 只接受一个实现。"""
        ctx.provide(cls.service_key, impl)


class LocalBashExecutor(ShellExecutor):
    """Service Provider。本地子进程执行。"""

    def execute(self, spec):
        return f"local bash -c '{spec}'"


class SandboxBashExecutor(ShellExecutor):
    """Service Provider。沙箱执行。与本地版依据同一约定，可互换。"""

    def execute(self, spec):
        return f"sandbox confined '{spec}'"


class BashTool:
    """Consumer。面向模型的 bash 工具，只声明依赖服务键。

    inject 列键名，构造时按 ctx 解析，执行时调约定里的方法。
    全程不 import LocalBashExecutor 或 SandboxBashExecutor，换实现时这个类不改。
    """

    inject = ("shell",)

    def __init__(self, ctx):
        self.shell = ctx.get("shell")
        print(f"      [inject] BashTool 取到服务键 shell -> {type(self.shell).__name__}")

    def run(self, spec):
        return self.shell.execute(spec)


def prompt_schema(tool):
    """模型看到的工具 schema 只有一份，与执行器实现无关。"""
    return {"name": "bash", "description": "执行一条命令", "parameters": {"cmd": "string"}}


def assert_contract(impl):
    """动手任务 4。断言拿到的实现确实是约定类型。"""
    assert isinstance(impl, ShellExecutor), "实现不是约定类型"
    return True
