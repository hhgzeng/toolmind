"""
请求上下文 (ContextVar)，用于在异步调用链中传递 trace_id、user_id、agent_name。
"""
from contextvars import ContextVar
from typing import Optional

# 请求跟踪 ID，由中间件设置
trace_id: ContextVar[Optional[str]] = ContextVar("trace_id", default=None)

# 当前用户 ID
user_id: ContextVar[Optional[str]] = ContextVar("user_id", default=None)

# 当前对话 Agent 名称（用于统计）
agent_name: ContextVar[Optional[str]] = ContextVar("agent_name", default=None)


def set_trace_id_context(tid: str) -> None:
    trace_id.set(tid)


def get_user_id_context() -> Optional[str]:
    return user_id.get()


def set_user_id_context(uid: str) -> None:
    user_id.set(uid)


def get_agent_name_context() -> str:
    return agent_name.get() or "其他"


def set_agent_name_context(ag_name: str) -> None:
    agent_name.set(ag_name)
