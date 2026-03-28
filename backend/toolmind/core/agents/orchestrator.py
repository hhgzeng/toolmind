"""
LangGraph 编排器 — Agent 的核心入口

使用 LangGraph StateGraph 构建状态机：
  increment_loop → Planner → Executor → Synthesizer → Evaluator → (条件边: 重跑 / 结束)
"""

import time

from langgraph.graph import END, START, StateGraph
from loguru import logger
from toolmind.api.services.session import SessionService
from toolmind.core.agents.evaluator import Evaluator
from toolmind.core.agents.executor import Executor
from toolmind.core.agents.planner import Planner
from toolmind.core.agents.state import AgentState
from toolmind.core.agents.synthesizer import Synthesizer
from toolmind.core.agents.tool_manager import ToolManager
from toolmind.core.callbacks import usage_metadata_callback
from toolmind.core.models.manager import ModelManager
from toolmind.database.models.session import SessionContext, SessionCreate
from toolmind.prompts.agent import GenerateTitlePrompt
from toolmind.schema.agent import AgentTask

# ── LangGraph 辅助节点 & 条件边 ──


async def _increment_loop(state: AgentState) -> dict:
    """每次进入规划前递增循环计数"""
    new_count = state.get("loop_count", 0) + 1
    events = []
    if new_count > 1:
        events.append(
            {
                "event": "step_result",
                "data": {
                    "message": "正在重新规划任务并重头执行...",
                    "title": f"第 {new_count} 次重跑",
                },
            }
        )
    return {"loop_count": new_count, "events": events}


def _should_retry(state: AgentState) -> str:
    """条件边：决定是否重跑"""
    if state["eval_score"] >= 80:
        return "end"
    if state["loop_count"] >= state["max_loop"]:
        return "end"
    return "retry"


def _build_graph(user_id: str, tool_manager: ToolManager):
    """构建并编译 LangGraph 状态机"""

    planner = Planner(user_id, tool_manager)
    executor = Executor(user_id, tool_manager)
    synthesizer = Synthesizer(user_id)
    evaluator = Evaluator(user_id, tool_manager)

    graph = StateGraph(AgentState)

    # ── 注册节点 ──
    graph.add_node("increment_loop", _increment_loop)
    graph.add_node("planner", planner)
    graph.add_node("executor", executor)
    graph.add_node("synthesizer", synthesizer)
    graph.add_node("evaluator", evaluator)

    # ── 注册边 ──
    #   START → increment_loop → planner → executor → synthesizer → evaluator
    #   evaluator →(条件)→ increment_loop（重跑）/ END（结束）
    graph.add_edge(START, "increment_loop")
    graph.add_edge("increment_loop", "planner")
    graph.add_edge("planner", "executor")
    
    def _should_continue_executing(state: AgentState) -> str:
        """条件边：决定是否继续执行下一个子任务"""
        steps = state.get("steps", [])
        context_task = state.get("context_task", [])
        if len(context_task) < len(steps):
            return "executor"
        return "synthesizer"

    graph.add_conditional_edges(
        "executor",
        _should_continue_executing,
        {"executor": "executor", "synthesizer": "synthesizer"},
    )
    graph.add_edge("synthesizer", "evaluator")

    graph.add_conditional_edges(
        "evaluator",
        _should_retry,
        {"retry": "increment_loop", "end": END},
    )

    return graph.compile()


class Agent:
    """
    Agent 编排器（基于 LangGraph StateGraph）

    对外 API 保持与原始 Agent 完全一致。
    """

    def __init__(self, user_id: str):
        self.user_id = user_id
        self.tool_manager = ToolManager(user_id)
        self.graph = _build_graph(user_id, self.tool_manager)

    async def submit_agent_task(self, agent_task: AgentTask):
        """主入口：接收 AgentTask，驱动 LangGraph 状态机，yield SSE 事件"""
        task_start = time.monotonic()

        # ── 创建会话 ──
        session_model = await SessionService.create_session(
            SessionCreate(title="新对话", user_id=self.user_id, contexts=[])
        )

        yield {
            "event": "session_started",
            "data": {
                "session_id": session_model.session_id,
                "title": session_model.title,
                "create_time": (
                    session_model.create_time.isoformat()
                    if session_model.create_time
                    else None
                ),
            },
        }

        # ── 初始化状态 ──
        initial_state: AgentState = {
            "query": agent_task.query,
            "user_id": self.user_id,
            "steps": [],
            "tasks_show": [],
            "context_task": [],
            "final_response": "",
            "eval_score": 0,
            "eval_reasoning": "",
            "loop_count": 0,
            "max_loop": 3,
            "session_model": session_model,
            "events": [],
        }

        # ── 运行 LangGraph 状态机（带节点级耗时日志）──
        final_state = initial_state
        node_start = time.monotonic()
        async for update in self.graph.astream(initial_state, stream_mode="updates"):
            for node_name, state_update in update.items():
                node_elapsed = time.monotonic() - node_start
                logger.info(
                    f"[Agent] Node '{node_name}' completed in {node_elapsed:.2f}s"
                )
                node_start = time.monotonic()

                # 实时推送该节点产出的 SSE 事件
                for sse_event in state_update.get("events", []):
                    yield sse_event
                # 合并状态以获取最终结果
                final_state = {**final_state, **state_update}

                # ── 在每一轮评估结束后，保存当前轮次的对话 ──
                if node_name == "evaluator":
                    score = final_state.get("eval_score", 0)
                    reasoning = final_state.get("eval_reasoning", "")
                    loop_count = final_state.get("loop_count", 0)
                    max_loop = final_state.get("max_loop", 3)

                    if score >= 80:
                        feedback_msg = (
                            f"\n\n\n> **✅ 自我反馈通过** (匹配度: {score}/100)\n"
                            f"> **理由**: {reasoning}\n\n---\n\n"
                        )
                    else:
                        feedback_msg = (
                            f"\n\n\n> **⚠️ 自我反馈未通过** (匹配度: {score}/100)\n"
                            f"> **理由**: {reasoning}\n\n---\n\n"
                        )

                    yield {"event": "task_result", "data": {"message": feedback_msg}}

                    # ── 持久化当前轮次的会话 ──
                    final_response = final_state.get("final_response", "")
                    await SessionService.update_session_contexts(
                        session_model.session_id,
                        SessionContext(
                            query=agent_task.query,
                            task=final_state.get("context_task", []),
                            task_graph=final_state.get("tasks_show", []),
                            answer=final_response + feedback_msg,
                        ).model_dump(),
                    )

        total_elapsed = time.monotonic() - task_start
        logger.info(f"[Agent] Total pipeline completed in {total_elapsed:.2f}s")

        # ── 流式生成标题 ──
        async for event in self._stream_title(session_model, agent_task.query):
            yield event

    async def _stream_title(self, session_model, query: str):
        """流式生成会话标题并持久化"""
        title_prompt = GenerateTitlePrompt.format(query=query)
        conversation_model = await ModelManager.get_conversation_model(
            user_id=self.user_id
        )

        streamed_title = ""
        async for title_chunk in conversation_model.astream(
            input=title_prompt,
            config={"callbacks": [usage_metadata_callback]},
        ):
            chunk_content = getattr(title_chunk, "content", "") or ""
            if not chunk_content:
                continue
            streamed_title += chunk_content
            yield {
                "event": "session_title_chunk",
                "data": {
                    "session_id": session_model.session_id,
                    "title": streamed_title,
                },
            }

        final_title = streamed_title.strip() or "新对话"

        await SessionService.update_session(
            session_model.session_id,
            self.user_id,
            title=final_title,
            is_pinned=None,
        )

        yield {
            "event": "session_updated",
            "data": {
                "session_id": session_model.session_id,
                "title": final_title,
            },
        }
