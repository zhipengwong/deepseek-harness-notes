"""共享核心：业务函数与允许跨入口调用的清单。

对应上游机制：
  - @Remote 标记的方法 = ALLOWED 清单里的 endpoint
  - 描述只在两端本地，线路上只有 endpoint 和具名参数
  - 业务函数不认识 argv，也不认识 HTTP request

只含自己编写的逻辑，离线运行，只用标准库。
"""


class BusinessError(Exception):
    """业务失败。带上稳定的错误码，供两个入口共用同一套投影。"""

    def __init__(self, code, message):
        super().__init__(message)
        self.code = code
        self.message = message


class Harness:
    """两个入口共用的核心。会话状态只存一份。"""

    def __init__(self):
        self._sessions = {}
        self._next_id = 1

    def create_session(self, title):
        sid = f"s-{self._next_id}"
        self._next_id += 1
        self._sessions[sid] = {"title": title, "turns": []}
        return {"sessionId": sid, "title": title}

    def prompt(self, sessionId, text):
        session = self._sessions.get(sessionId)
        if session is None:
            raise BusinessError("session/not-found", f"会话 {sessionId!r} 不存在")
        session["turns"].append(text)
        return {
            "sessionId": sessionId,
            "reply": f"已收到 {text!r}",
            "turns": len(session["turns"]),
        }

    def list_sessions(self):
        return {
            "sessions": [
                {"sessionId": sid, "title": data["title"], "turns": len(data["turns"])}
                for sid, data in self._sessions.items()
            ]
        }


class Endpoint:
    """本地描述。只在两端本地，不上线路。"""

    def __init__(self, name, params, handler):
        self.name = name
        self.params = tuple(params)
        self.handler = handler


ALLOWED = {
    "sessions/create": Endpoint("sessions/create", ("title",), Harness.create_session),
    "sessions/prompt": Endpoint("sessions/prompt", ("sessionId", "text"), Harness.prompt),
    "sessions/list": Endpoint("sessions/list", (), Harness.list_sessions),
}


def describe():
    """给两个入口看的同一份清单。"""
    return [{"endpoint": ep.name, "params": list(ep.params)} for ep in ALLOWED.values()]


def dispatch(harness, envelope):
    """按清单查表并调用业务函数。未知 endpoint 与坏参数都变成错误信封。"""
    rid = envelope.get("rpcId")
    endpoint = envelope.get("endpoint")
    args = envelope.get("args", {})

    ep = ALLOWED.get(endpoint)
    if ep is None:
        return {
            "rpcId": rid,
            "ok": False,
            "error": {"code": "unknown/endpoint", "message": f"endpoint {endpoint!r} 不在清单里"},
        }
    missing = [name for name in ep.params if name not in args]
    extra = [name for name in args if name not in ep.params]
    if missing or extra:
        detail = f"缺少 {missing}" if missing else f"多余 {extra}"
        return {
            "rpcId": rid,
            "ok": False,
            "error": {"code": "gateway/input-invalid", "message": detail},
        }
    try:
        result = ep.handler(harness, **args)
    except BusinessError as exc:
        return {
            "rpcId": rid,
            "ok": False,
            "error": {"code": exc.code, "message": exc.message},
        }
    return {"rpcId": rid, "ok": True, "result": result}
