# 第 1 讲：从单次调用到 Agent 循环

第 0 讲调了一次 API，模型说一句话就结束。这一讲把那次调用接成循环。循环让模型能要求工具，让程序执行工具，再把结果送回模型。这是 Harness 的核心动作。

本讲先用假模型把循环逻辑看清。假模型不联网，不需要 key。看完逻辑再换成真 API，接口位置不变。

## 循环多出来的五个动作

裸调用只有两步：发请求，收返回。

Agent 循环把返回结果接回输入。完整的一轮有五个动作。

```
发请求（带 tools） → 收返回 → 看 finish_reason
                                   │
                     ┌─────────────┴─────────────┐
                     │                           │
                 tool_calls                    stop
                     │                           │
                执行工具 → 回灌                 结束
                     │
                  再次请求（回到起点）
```

五步展开如下。

1. 发请求。`messages` 带全部历史，`tools` 带工具清单。
2. 收返回。从 `choices[0]` 取出 `message`。
3. 看 `finish_reason`。值为 `stop` 时循环结束。值为 `tool_calls` 时继续。
4. 执行工具。按 `message.tool_calls` 里的名字和参数调用本地函数。
5. 回灌结果。把执行结果作为一条 `role` 为 `tool` 的消息追加进 `messages`，回到第 1 步。

第 4 步和第 5 步是裸调用没有的。这两步由调用方程序完成，模型和服务端都不参与。

## tools 清单的形状

请求里的 `tools` 是数组。每一项描述一个工具的名字、用途和参数格式。

```json
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
```

这份清单告诉模型：有个叫 `read_file` 的工具，它接受一个 `path` 字符串。模型不读文件，它只根据这份描述决定是否要求调用。

## tool_calls 返回的形状

模型决定用工具时，返回如下。

```json
{
  "choices": [{
    "finish_reason": "tool_calls",
    "message": {
      "role": "assistant",
      "content": null,
      "tool_calls": [{
        "id": "call_1",
        "type": "function",
        "function": {
          "name": "read_file",
          "arguments": "{\"path\": \"a.txt\"}"
        }
      }]
    }
  }]
}
```

注意三点。`finish_reason` 是 `tool_calls`，不再是 `stop`。`content` 是 `null`，模型这一轮没有说话。`arguments` 是字符串，内容是 JSON。这些都是文本，不是函数调用本身。

`id` 用来把执行结果和这次请求对应起来。回灌时要把同一个 `id` 放进 `tool_call_id` 字段。

## 用假模型看清循环

把上面的返回写成一个函数，就能离线观察循环。假模型按轮次返回两次结果。第一轮要求读文件，第二轮给出回答。

完整脚本如下。可直接保存为 `agent_loop.py` 运行。

```python
# 最小 Agent 循环演示。不联网，不需要 key。
import json

# 1. 工具清单
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

# 2. 假模型
class FakeModel:
    def __init__(self):
        self.turn = 0

    def chat(self, messages, tools=None):
        self.turn += 1
        if self.turn == 1:
            message = {
                "role": "assistant",
                "content": None,
                "tool_calls": [{
                    "id": "call_1",
                    "type": "function",
                    "function": {
                        "name": "read_file",
                        "arguments": json.dumps({"path": "a.txt"})
                    }
                }]
            }
            finish_reason = "tool_calls"
        else:
            message = {
                "role": "assistant",
                "content": "a.txt 的内容是：hello"
            }
            finish_reason = "stop"
        return {"choices": [{"finish_reason": finish_reason, "message": message}]}

# 3. 执行工具
def execute_tool(tool_call):
    name = tool_call["function"]["name"]
    args = json.loads(tool_call["function"]["arguments"])
    if name == "read_file":
        return "hello"
    return "未知工具"

# 4. 循环
def agent_loop(user_input):
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": user_input}
    ]
    model = FakeModel()

    while True:
        response = model.chat(messages, tools)
        choice = response["choices"][0]
        message = choice["message"]
        messages.append(message)

        print(f"--- 第 {model.turn} 轮 ---")
        print(f"finish_reason: {choice['finish_reason']}")
        print(f"message: {message}")
        print()

        if choice["finish_reason"] == "stop":
            print("模型回复：", message["content"])
            break

        if choice["finish_reason"] == "tool_calls":
            for tool_call in message["tool_calls"]:
                result = execute_tool(tool_call)
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call["id"],
                    "content": result
                })
                print(f"执行工具 {tool_call['function']['name']}，结果：{result}")
                print()

if __name__ == "__main__":
    agent_loop("读一下 a.txt")
```

## 运行结果

脚本实际运行输出如下。

```
--- 第 1 轮 ---
finish_reason: tool_calls
message: {'role': 'assistant', 'content': None, 'tool_calls': [{'id': 'call_1', 'type': 'function', 'function': {'name': 'read_file', 'arguments': '{"path": "a.txt"}'}}]}

执行工具 read_file，结果：hello

--- 第 2 轮 ---
finish_reason: stop
message: {'role': 'assistant', 'content': 'a.txt 的内容是：hello'}

模型回复： a.txt 的内容是：hello
```

看 `messages` 的最终状态。它有五条消息，按顺序是 `system`、`user`、`assistant`（带 `tool_calls`）、`tool`（带结果）、`assistant`（最终回答）。这就是第 0 讲说的「调用方保存全部历史」。循环每转一轮，历史就多两条。

## 换成真 API

假模型和真 API 的返回结构一致。换后端只需替换 `chat` 函数。下面的实现调用 OpenRouter，key 从环境变量读取。

```python
import os
import requests

def real_chat(messages, tools=None):
    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {os.environ['OPENROUTER_API_KEY']}"
        },
        json={
            "model": "nvidia/nemotron-3.5-super-vl:free",
            "messages": messages,
            "tools": tools,
            "stream": False
        }
    )
    return response.json()
```

把 `model.chat(messages, tools)` 改成 `real_chat(messages, tools)`，循环部分不用改。这就是接口对齐的好处。

真模型不一定按假模型的轮次返回。它可能第一轮就说话，也可能连续要求调用多个工具。循环代码要能处理这两种情况。`while True` 配 `finish_reason` 判断，正好覆盖。

## 动手任务

1. 保存脚本为 `agent_loop.py`，运行一次，确认输出与本讲一致。
2. 在 `agent_loop` 结尾打印完整 `messages`，数出五条消息。
3. 把 `execute_tool` 改成真的读文件。用 Python 打开文件，返回内容。
4. 选做：换成 `real_chat`，用免费模型跑一次，观察真模型的 `finish_reason`。

任务 1 到 3 不需要网络。任务 4 需要 key 和可用模型。

## 本讲小测

1. 循环里为什么要用 `while True`，而不是固定次数？
2. `finish_reason` 为 `tool_calls` 时，`message.content` 通常是什么值？为什么？
3. 回灌消息为什么要带 `tool_call_id`？
4. 模型返回两个 `tool_calls` 时，循环代码要改吗？

## 边界说明

工具清单与返回字段来自 OpenAI 兼容格式约定。假模型的轮次行为是本讲为演示设定的，不代表任何真实模型。真 API 的调用方式来自 OpenRouter 公开接口。循环、工具执行与错误处理的分工属于 Harness 层的设计判断，参照 DSH 的实现，在后续各讲展开。
