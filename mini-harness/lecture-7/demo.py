"""第 7 讲演示：共享核心、命令行入口、本地 HTTP 入口、未知 endpoint 的报错差异。

四个场景对应讲义四条动手任务。全部离线运行，只用标准库。
HTTP 入口监听 127.0.0.1 的随机端口，请求也发往本机，不访问外网。

输出约定：标题与结果走 stdout，诊断走 stderr。演示里把诊断就地捕获后
按场景打印，避免两个通道缓冲差异打乱终端上的阅读顺序。
"""

import io
import json
import sys
import threading
from contextlib import redirect_stderr, redirect_stdout

from cli import main as cli_main
from connection import Connection, InProcessCarrier, RpcCarrier
from harness_core import Harness, describe
from remote import start_server


def hr(title):
    print(f"\n{'=' * 62}\n{title}\n{'=' * 62}")


def invoke_shown(conn, endpoint, args=None):
    """调用并按本次顺序就地打印诊断，随后返回结果。"""
    diag = io.StringIO()
    with redirect_stderr(diag):
        reply = conn.invoke(endpoint, args)
    for line in diag.getvalue().splitlines():
        print(line)
    return reply


# ---------------------------------------------------------------- 场景 1
hr("场景 1：共享核心与一份允许调用的清单")
harness = Harness()
print("  两个入口共用同一份清单，业务函数不认识载体")
for item in describe():
    print(f"  [allowed] {item['endpoint']}({', '.join(item['params'])})")
reply = invoke_shown(Connection(InProcessCarrier(harness)), "sessions/create", {"title": "demo"})
print("  [direct]", json.dumps(reply, ensure_ascii=False))


# ---------------------------------------------------------------- 场景 2
hr("场景 2：命令行入口解析参数，结果只写 stdout")
out, err = io.StringIO(), io.StringIO()
with redirect_stdout(out), redirect_stderr(err):
    code = cli_main(["sessions/prompt", '{"sessionId":"s-1","text":"hi"}'], harness)
print(f"  [exit] {code}")
print(f"  [stdout] {out.getvalue().strip()}")
print("  [stderr]", err.getvalue().strip().replace("\n", " | "))
print("  → 诊断与结果分通道，stdout 可以直接被下游解析")


# ---------------------------------------------------------------- 场景 3
hr("场景 3：HTTP 入口把同一份清单映射成 endpoint")
server, thread = start_server(harness)
port = server.server_address[1]
try:
    conn = Connection(RpcCarrier(f"http://127.0.0.1:{port}"))
    reply = invoke_shown(conn, "sessions/list", {})
    print("  [reply]", json.dumps(reply, ensure_ascii=False))
    print("  → 业务函数与清单没改，换的只是 Connection 的载体")
finally:
    server.shutdown()
    server.server_close()
    thread.join(timeout=2)


# ---------------------------------------------------------------- 场景 4
hr("场景 4：未知 endpoint，两种入口的报错对照")
out2, err2 = io.StringIO(), io.StringIO()
with redirect_stdout(out2), redirect_stderr(err2):
    code2 = cli_main(["nope/run", "{}"], harness)
print(f"  CLI   exit={code2} stdout={out2.getvalue().strip()!r}")
print("  CLI   stderr", err2.getvalue().strip().replace("\n", " | "))

server2, thread2 = start_server(harness)
port2 = server2.server_address[1]
try:
    reply2 = invoke_shown(Connection(RpcCarrier(f"http://127.0.0.1:{port2}")), "nope/run", {})
    print("  HTTP ", json.dumps(reply2, ensure_ascii=False))
finally:
    server2.shutdown()
    server2.server_close()
    thread2.join(timeout=2)
print("  → 清单是唯一裁决点，两个入口都拒绝同一个 endpoint")
