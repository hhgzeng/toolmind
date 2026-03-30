"""
LangGraph 编排器 — Agent 核心入口
基于状态机驱动任务流转：规划 -> 执行 -> 聚合 -> 评估
"""

from langgraph.graph import END, START, StateGraph
from toolmind.api.services import SessionService
from toolmind.core.agents.evaluator import Evaluator
from toolmind.core.agents.executor import Executor
from toolmind.core.agents.model import ModelManager
from toolmind.core.agents.planner import Planner
from toolmind.core.agents.state import AgentState
from toolmind.core.agents.synthesizer import Synthesizer
from toolmind.core.agents.tool_manager import ToolManager
from toolmind.core.callbacks import UsageMetadataCallback
from toolmind.database.models import SessionContext, SessionCreate
from toolmind.prompts import GenerateTitlePrompt
from toolmind.schema import AgentTask


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


def _should_continue_executing(state: AgentState) -> str:
    """条件边：决定是否继续执行下一个子任务"""
    steps = state.get("steps", [])
    context_task = state.get("context_task", [])
    if len(context_task) < len(steps):
        return "executor"
    return "synthesizer"


def _build_graph(user_id: str, tool_manager: ToolManager):
    """构建并编译 LangGraph 状态机"""

    planner = Planner(user_id, tool_manager)
    executor = Executor(user_id, tool_manager)
    synthesizer = Synthesizer(user_id)
    evaluator = Evaluator(user_id, tool_manager)

    graph = StateGraph(AgentState)

    graph.add_node("increment_loop", _increment_loop)
    graph.add_node("planner", planner)
    graph.add_node("executor", executor)
    graph.add_node("synthesizer", synthesizer)
    graph.add_node("evaluator", evaluator)

    # 编排节点流向：START -> increment_loop -> planner -> executor -> synthesizer -> evaluator
    graph.add_edge(START, "increment_loop")
    graph.add_edge("increment_loop", "planner")
    graph.add_edge("planner", "executor")

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
    """基于 LangGraph 的 Agent 编排器，提供 SSE 任务提交接口"""

    def __init__(self, user_id: str):
        self.user_id = user_id
        self.tool_manager = ToolManager(user_id)
        self.graph = _build_graph(user_id, self.tool_manager)

    async def submit_agent_task(self, agent_task: AgentTask):
        """主入口：创建会话、驱动状态机并推送事件"""

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

        final_state = initial_state
        async for update in self.graph.astream(initial_state, stream_mode="updates"):
            for node_name, state_update in update.items():

                # 实时推送节点 SSE 事件并合并状态
                for sse_event in state_update.get("events", []):
                    yield sse_event
                final_state = {**final_state, **state_update}

                # 评估结束后，推送统计并持久化
                if node_name == "evaluator":
                    score = final_state.get("eval_score", 0)
                    reasoning = final_state.get("eval_reasoning", "")

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
            config={"callbacks": [UsageMetadataCallback]},
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
