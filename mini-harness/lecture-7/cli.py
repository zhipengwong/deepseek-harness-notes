"""命令行入口。解析位置参数，调用共享核心，只把结果写到 stdout。

对应上游 headless profile：任务文本走位置参数，推理写 stderr，结果写 stdout。
"""

import json
import sys

from connection import Connection, InProcessCarrier
from harness_core import Harness, describe


def print_manifest(stream=sys.stderr):
    for item in describe():
        print(f"  {item['endpoint']}({', '.join(item['params'])})", file=stream)


def main(argv=None, harness=None, out=None, err=None):
    argv = sys.argv[1:] if argv is None else argv
    out = out or sys.stdout
    err = err or sys.stderr

    if not argv or argv[0] in ("-h", "--help"):
        print("用法: cli.py <endpoint> [JSON 参数]", file=err)
        print("清单:", file=err)
        print_manifest(err)
        return 0

    endpoint = argv[0]
    try:
        args = json.loads(argv[1]) if len(argv) > 1 else {}
    except json.JSONDecodeError as exc:
        print(f"[cli] 参数不是合法 JSON: {exc}", file=err)
        return 2

    carrier = InProcessCarrier(harness or Harness())
    reply = Connection(carrier).invoke(endpoint, args)

    if reply["ok"]:
        print(json.dumps(reply["result"], ensure_ascii=False), file=out)
        return 0
    print(f"[{reply['error']['code']}] {reply['error']['message']}", file=err)
    return 1


if __name__ == "__main__":
    sys.exit(main())
