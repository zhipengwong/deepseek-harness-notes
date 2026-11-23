# 第 1 讲真 API 脚本：把假模型换成真实模型，跑完整 Agent 循环。
# 配套讲义：docs/course/lecture-1-agent-loop.md「换成真 API」与动手任务 5。
# 需先设置环境变量 OPENROUTER_API_KEY。本文件不含任何凭证。
import json
import os
import sys

try:
    import requests
except ImportError:
    print("requests 未安装")
    sys.exit(1)

API_KEY = os.environ.get("OPENROUTER_API_KEY")
if not API_KEY:
    print("OPENROUTER_API_KEY 未设置")
    sys.exit(1)

ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "nvidia/nemotron-3.5-super-vl:free"

# 工具清单，与讲义一致
tools = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "读取本地文本文件的内容",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "文件路径"}
                },
                "required": ["path"]
            }
        }
    }
]


def real_chat(messages, tools=None):
    payload = {
        "model": MODEL,
        "messages": messages,
        "stream": False,
    }
    if tools:
        payload["tools"] = tools
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}",
    }

    # 请求报文。Authorization 脱敏，不打印真实 key。
    safe_headers = dict(headers)
    safe_headers["Authorization"] = "Bearer <redacted>"
    print("=== 请求报文 ===")
    print(f"POST {ENDPOINT}")
    print(json.dumps({"headers": safe_headers, "body": payload}, ensure_ascii=False, indent=2))
    print()

    response = requests.post(ENDPOINT, headers=headers, json=payload, timeout=90)

    if response.status_code != 200:
        print(f"HTTP {response.status_code}: {response.text[:600]}")
        sys.exit(1)

    result = response.json()
    # 响应报文。原样打印服务端返回体。
    print("=== 响应报文 ===")
    print(f"HTTP {response.status_code}")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print()
    return result


def execute_tool(tool_call):
    name = tool_call["function"]["name"]
    args = json.loads(tool_call["function"]["arguments"])
    if name == "read_file":
        path = args["path"]
        if not os.path.isabs(path):
            path = os.path.join(os.getcwd(), path)
        with open(path, "r", encoding="utf-8") as f:
            return f.read().rstrip("\n")
    return "未知工具"


messages = [
    {
        "role": "system",
        "content": "You are a helpful assistant. When the user asks to read a file, use the read_file tool.",
    },
    {"role": "user", "content": "请读取 a.txt 文件，告诉我里面写了什么。"},
]

for turn in range(1, 6):
    print(f"--- 第 {turn} 轮 ---")
    response = real_chat(messages, tools)
    usage = response.get("usage", {})
    print(
        f"usage: prompt={usage.get('prompt_tokens')} "
        f"completion={usage.get('completion_tokens')} cost={usage.get('cost')}"
    )
    choice = response["choices"][0]
    finish = choice["finish_reason"]
    msg = choice["message"]
    print(f"finish_reason: {finish}")
    print(f"content: {msg.get('content')}")
    if msg.get("tool_calls"):
        print(f"tool_calls: {json.dumps(msg['tool_calls'], ensure_ascii=False)}")
    messages.append(msg)
    print()

    if finish == "stop":
        print("模型最终回复：", msg.get("content"))
        break

    if finish == "tool_calls":
        for tool_call in msg["tool_calls"]:
            result = execute_tool(tool_call)
            print(f"执行工具 {tool_call['function']['name']}，结果：{result}")
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call["id"],
                    "content": result,
                }
            )
        print()
else:
    print("达到最大轮次，停止。")
