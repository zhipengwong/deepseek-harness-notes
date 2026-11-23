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

完整脚本在 `mini-harness/lecture-1/agent_loop_api.py`。它把上面的 `real_chat` 接进循环，含工具执行与回灌，可用 `python3 agent_loop_api.py` 直接运行。运行前先设置环境变量 `OPENROUTER_API_KEY`。key 只从环境变量读取，脚本里没有凭证。

真模型不一定按假模型的轮次返回。它可能第一轮就说话，也可能连续要求调用多个工具。循环代码要能处理这两种情况。`while True` 配 `finish_reason` 判断，正好覆盖。

实测注意：OpenRouter 的 key 以 `sk-or-` 开头。若返回 HTTP 401 并提示 key 格式无效，检查环境变量里是否为 OpenRouter 凭证，不要用其他服务的 key。key 明文暴露后应及时撤销并更换。

## 真 API 实测

动手任务 5 用 OpenRouter 的免费模型 `nvidia/nemotron-3.5-super-vl:free` 跑通完整循环。脚本是 `mini-harness/lecture-1/agent_loop_api.py`，key 从环境变量读取。每轮的请求与响应原始报文存于同目录的 `api-run-sample.log`，Authorization 头里的 key 已遮蔽。

实测两轮结果。

| 轮次 | finish_reason | message.content | 关键动作 |
|---|---|---|---|
| 1 | tool_calls | null | 模型返回 tool_calls，要求读 a.txt。程序执行工具，读到 hello from real file |
| 2 | stop | a.txt 文件里的内容是：hello from real file | 模型读工具结果后自行组织语言作答 |

第 1 轮的 `tool_calls.function.arguments` 是字符串 `{"path":"a.txt"}`。程序解析后执行 `open()`，把 `hello from real file` 作为 `tool` 消息回灌。这与假模型的返回结构一致。

第 2 轮的 prompt_tokens 为 404，第 1 轮为 318。增量 86 来自回灌的 assistant 消息和 tool 消息。这是「历史在增长」在报文层的证据。两轮 cost 均为 0，免费模型生效。

这份实测回答第 0 讲遗留的观察题。请求加上 `tools` 之后，`finish_reason` 从 `stop` 变成 `tool_calls`，`message.content` 变成 `null`，`message` 多出 `tool_calls` 字段。三处与讲义预测一致。

三个版本对照。

| 版本 | 第 1 轮 finish_reason | 模型回复来源 |
|---|---|---|
| `agent_loop.py` | tool_calls | 写死的字符串 |
| `agent_loop_real.py` | tool_calls | 从 tool 消息取真实结果，机械拼接 |
| `agent_loop_api.py` | tool_calls | 真实模型读 tool 结果后自行组织语言 |

第三个版本是完整闭环。前两个版本用于离线看清循环结构。

## a.txt 在哪里

代码里的 `a.txt` 最初只是一个字符串。它出现在假模型的 `arguments` 里，被 `execute_tool` 解出，但函数直接返回写死的 `hello`，没有调用 `open()`。仓库里当时并不存在这个文件。文件没有被读，这正是第 0 讲那条认知在演示代码里的延续。

课程代码目录现已补上真实文件 `mini-harness/lecture-1/a.txt`，内容是一行 `hello from real file`。同时提供对照脚本 `agent_loop_real.py`。对照版与原版有两处区别。

```
                          原版 agent_loop.py        对照版 agent_loop_real.py
execute_tool            return "hello"             open(path).read()
假模型第二轮 content     写死的「内容是 hello」       从 tool 消息取真实结果
```

第一处让程序真的读磁盘。第二处让模型回复用上读到的结果。只改第一处不够。工具结果虽然回灌进了 `messages`，但假模型第二轮仍写死回答，输出会自相矛盾：工具说读到 `hello from real file`，模型却说内容是 `hello`。所以对照版也让假模型从回灌的 `tool` 消息里取内容。

两版实测输出有两行不同。

```
原版     执行工具 read_file，结果：hello
         模型回复： a.txt 的内容是：hello

对照版   执行工具 read_file，结果：hello from real file
         模型回复： a.txt 的内容是：hello from real file
```

对照版这两行一致，证明程序碰了磁盘，也证明模型回复消费了工具结果。五条 `messages` 的结构在两版中一致。

对照版把相对路径按脚本所在目录解析，避免运行目录不同导致找不到文件。

要验证回复确实依赖文件内容，可以改 `a.txt` 的内容再运行。模型回复会跟着变，因为它取自工具结果，不再写死。这演示了「回灌」的价值：模型看到工具输出后才作答。真实模型的行为也是如此，只是它会用自己的语言组织回答。这正是第 1 讲末尾换成 `real_chat` 的意义所在。

## 动手任务

1. 运行 `mini-harness/lecture-1/agent_loop.py`，确认输出与本讲一致。
2. 在脚本结尾打印完整 `messages`，数出五条消息。
3. 运行 `agent_loop_real.py`，对比它与原版的输出差异，确认真实文件读取生效。
4. 选做：删掉 `a.txt` 再运行对照版，观察 `FileNotFoundError`，确认报错来自真实的 `open()`。
5. 选做：设置 `OPENROUTER_API_KEY` 后运行 `agent_loop_api.py`，观察真模型的 `finish_reason`。

任务 1 到 4 不需要网络。任务 5 需要 OpenRouter key 和可用模型。

## 本讲小测

1. 循环里为什么要用 `while True`，而不是固定次数？
2. `finish_reason` 为 `tool_calls` 时，`message.content` 通常是什么值？为什么？
3. 回灌消息为什么要带 `tool_call_id`？
4. 模型返回两个 `tool_calls` 时，循环代码要改吗？

## 边界说明

工具清单与返回字段来自 OpenAI 兼容格式约定。假模型的轮次行为是本讲为演示设定的，不代表任何真实模型。真 API 的调用方式来自 OpenRouter 公开接口。循环、工具执行与错误处理的分工属于 Harness 层的设计判断，参照 DSH 的实现，在后续各讲展开。
