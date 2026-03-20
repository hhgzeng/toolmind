"""
MindAgent 共享状态定义

类似 LangGraph 的 TypedDict State，所有 Agent 通过读写 MindState 进行数据传递。
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from toolmind.schema.mind import MindTaskStep


@dataclass
class MindState:
    """状态机的共享状态，在各 Agent 节点间流转"""

    # ── 输入 ──
    query: str = ""
    mcp_servers: List[str] = field(default_factory=list)
    web_search: bool = True
    user_id: str = ""

    # ── 规划结果 ──
    steps: List[MindTaskStep] = field(default_factory=list)
    tasks_show: List[Dict[str, str]] = field(default_factory=list)

    # ── 执行结果 ──
    context_task: List[Dict[str, Any]] = field(default_factory=list)

    # ── 汇总 ──
    final_response: str = ""

    # ── 评估 ──
    eval_score: int = 0
    eval_reasoning: str = ""

    # ── 控制流 ──
    loop_count: int = 0
    max_loop: int = 3

    # ── 会话 ──
    session_model: Optional[Any] = None
