"""第 8 讲：能力 seam，对应第 6 讲的三角色。

Service Definition 是约定，Provider 是实现，Consumer 只注入服务键。
这条链里有两个 seam：模型适配器和 shell 执行器。
换实现不改 driver，也不改模型看到的 schema。
"""

from session_core import diag


class ModelDefinition:
    """约定：current() 返回一条回复，带 text 与可选 tools。"""
    def current(self):
        raise NotImplementedError


class ScriptModel(ModelDefinition):
    """Provider A：脚本化假模型，离线可跑。"""
    def __init__(self, script):
        self.script = list(script)
        self.cursor = 0

    def current(self):
        reply = self.script[self.cursor] if self.cursor < len(self.script) else {"text": "(无更多回复)"}
        self.cursor += 1
        diag(f"      [model] 第 {self.cursor} 次调用：{reply['text']}")
        return reply


class EchoModel(ModelDefinition):
    """Provider B：换一个实现，driver 一行不改。"""
    def current(self):
        diag("      [model] EchoModel 回显")
        return {"text": "echo"}


class ShellDefinition:
    """约定：run() 执行一条命令并返回文本。"""
    def run(self, **kwargs):
        raise NotImplementedError


class LocalShell(ShellDefinition):
    """Provider A：本地执行，返回固定文本不启真实进程。"""
    def run(self, **kwargs):
        return "local:" + ",".join(f"{k}={v}" for k, v in kwargs.items())


class SandboxShell(ShellDefinition):
    """Provider B：沙箱执行，换实现不改工具 schema。"""
    def run(self, **kwargs):
        return "sandbox:" + ",".join(f"{k}={v}" for k, v in kwargs.items())


class Context:
    """服务键装配。Consumer 只拿键，不 import 实现。"""
    def __init__(self):
        self.services = {}

    def provide(self, key, impl):
        if key in self.services:
            raise ValueError(f"重复服务键：{key}")
        self.services[key] = impl

    def get(self, key):
        return self.services[key]
