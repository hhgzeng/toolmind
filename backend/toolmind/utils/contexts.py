"""
请求上下文 (ContextVar)，用于在异步调用链中传递 trace_id、user_id。
"""

from contextvars import ContextVar
from typing import Optional

# 请求跟踪 ID，由中间件设置
trace_id: ContextVar[Optional[str]] = ContextVar("trace_id", default=None)

# 当前用户 ID
user_id: ContextVar[Optional[str]] = ContextVar("user_id", default=None)


def set_trace_id_context(tid: str) -> None:
    trace_id.set(tid)


def get_user_id_context() -> Optional[str]:
    return user_id.get()


def set_user_id_context(uid: str) -> None:
    user_id.set(uid)
