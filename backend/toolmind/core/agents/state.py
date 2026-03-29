"""
Agent 共享状态定义

使用 LangGraph 的 TypedDict State，所有 Agent 节点通过读写 AgentState 进行数据传递。
"""

from typing import Annotated, Any, Dict, List, Optional

from toolmind.schema.agent import AgentTaskStep
from typing_extensions import TypedDict


def _append_events(existing: List[dict], new: List[dict]) -> List[dict]:
    """Reducer: 将新事件追加到已有事件列表"""
    return existing + new


class AgentState(TypedDict, total=False):
    """LangGraph 状态机的共享状态"""

    # ── 输入 ──
    query: str
    user_id: str

    # ── 规划结果 ──
    steps: List[AgentTaskStep]
    tasks_show: List[Dict[str, str]]

    # ── 执行结果 ──
    context_task: List[Dict[str, Any]]

    # ── 汇总 ──
    final_response: str

    # ── 评估 ──
    eval_score: int
    eval_reasoning: str

    # ── 控制流 ──
    loop_count: int
    max_loop: int

    # ── 会话 ──
    session_model: Optional[Any]

    # ── SSE 事件队列（每个节点产出的事件追加到此列表） ──
    events: Annotated[List[dict], _append_events]
