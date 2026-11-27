"""Connection：统一调用形状，独占 rpcId 与信封。

对应上游机制：
  - ctx.connection.rpc.call = Connection 独占 route 与 envelope
  - 载体替换只改这里，业务函数与清单不动
  - Remote 层不暴露 request 或 fetch

进程内载体直接查表。远程载体走一次本地 HTTP POST。只用标准库。
"""

import json
import sys
import urllib.error
import urllib.request

from harness_core import ALLOWED, dispatch


class InProcessCarrier:
    """进程内载体。没有线路，直接把信封交给同一份清单。"""

    def __init__(self, harness):
        self.harness = harness

    def call(self, envelope):
        return dispatch(self.harness, envelope)


class RpcCarrier:
    """远程载体。只认 endpoint 与参数，把物理细节关在类里。"""

    def __init__(self, base_url):
        self.base_url = base_url.rstrip("/")

    def call(self, envelope):
        body = json.dumps(envelope, ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request(
            f"{self.base_url}/invoke",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=3) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            return json.loads(exc.read().decode("utf-8"))


class Connection:
    """两个入口共用的调用面。上层只看到 invoke(endpoint, args)。"""

    def __init__(self, carrier):
        self.carrier = carrier
        self._seq = 0

    def invoke(self, endpoint, args=None):
        self._seq += 1
        envelope = {
            "rpcId": f"rpc-{self._seq}",
            "endpoint": endpoint,
            "args": args or {},
        }
        print(f"      [conn] {envelope['rpcId']} -> {endpoint} args={envelope['args']}", file=sys.stderr)
        return self.carrier.call(envelope)
