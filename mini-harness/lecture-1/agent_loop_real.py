# 最小 Agent 循环演示：真实文件读取 + 消费工具结果版。
# 与 agent_loop.py 有两点区别：
#   1. execute_tool 真的读磁盘文件，不返回写死的字符串。
#   2. 假模型第二轮读取回灌的 tool 消息，用真实结果生成回复。
# 配套讲义：docs/course/lecture-1-agent-loop.md，动手任务 3。
import json
import os

# 工具清单（与 agent_loop.py 相同）
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


# 假模型（第二轮消费 tool 消息）
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
            # 从回灌的 tool 消息取真实结果，模拟模型读到工具输出后作答。
            tool_result = next((m["content"] for m in messages if m["role"] == "tool"), "")
            message = {
                "role": "assistant",
                "content": f"a.txt 的内容是：{tool_result}"
            }
            finish_reason = "stop"
        return {"choices": [{"finish_reason": finish_reason, "message": message}]}


# 唯一改动：真实读取文件。
def execute_tool(tool_call):
    name = tool_call["function"]["name"]
    args = json.loads(tool_call["function"]["arguments"])
    if name == "read_file":
        path = args["path"]
        # 相对路径按脚本所在目录解析，避免受运行目录影响。
        if not os.path.isabs(path):
            path = os.path.join(os.path.dirname(os.path.abspath(__file__)), path)
        with open(path, "r", encoding="utf-8") as f:
            return f.read().rstrip("\n")
    return "未知工具"


# 循环（与 agent_loop.py 相同）
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

    print("=== 完整 messages ===")
    for i, m in enumerate(messages):
        print(f"[{i}] role={m['role']}")


if __name__ == "__main__":
    agent_loop("读一下 a.txt")
