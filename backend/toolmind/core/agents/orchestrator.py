"""
编排器 — MindAgent 的核心入口

驱动 Planner → Executor → Synthesizer → Evaluator 的状态流转，
处理自我反馈重试循环和会话持久化。
"""

from toolmind.api.services.session import SessionService
from toolmind.core.agents.evaluator import Evaluator
from toolmind.core.agents.executor import Executor
from toolmind.core.agents.planner import Planner
from toolmind.core.agents.state import MindState
from toolmind.core.agents.synthesizer import Synthesizer
from toolmind.core.agents.tool_manager import ToolManager
from toolmind.core.callbacks import usage_metadata_callback
from toolmind.core.models.manager import ModelManager
from toolmind.database.models.session import SessionContext, SessionCreate
from toolmind.prompts.mind import GenerateTitlePrompt
from toolmind.schema.mind import MindTask


class MindAgent:
    """
    MindAgent 编排器

    对外 API 保持不变，内部委托给各子 Agent 完成工作。
    """

    def __init__(self, user_id: str):
        self.user_id = user_id

        # 初始化共享的工具管理器
        self.tool_manager = ToolManager(user_id)

        # 初始化各子 Agent
        self.planner = Planner(user_id, self.tool_manager)
        self.executor = Executor(user_id, self.tool_manager)
        self.synthesizer = Synthesizer(user_id)
        self.evaluator = Evaluator(user_id, self.tool_manager)

    async def submit_mind_task(self, mind_task: MindTask):
        """主入口：接收 MindTask，驱动状态机流转，yield SSE 事件"""

        # ── 初始化状态 ──
        state = MindState(
            query=mind_task.query,
            mcp_servers=mind_task.mcp_servers,
            web_search=mind_task.web_search,
            user_id=self.user_id,
        )

        # ── 创建会话 ──
        session_model = await SessionService.create_session(
            SessionCreate(
                title="新对话",
                user_id=self.user_id,
                contexts=[],
            )
        )
        state.session_model = session_model

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

        # ── 状态机主循环（最多 max_loop 次） ──
        while state.loop_count < state.max_loop:
            state.loop_count += 1

            if state.loop_count > 1:
                yield {
                    "event": "step_result",
                    "data": {
                        "message": "正在重新规划任务并重头执行...",
                        "title": f"第 {state.loop_count} 次重跑",
                    },
                }

            # ── 1. 规划 ──
            state = await self.planner.plan(state)
            yield {"event": "generate_tasks", "data": {"graph": state.tasks_show}}

            # ── 2. 执行 ──
            async for event in self.executor.execute(state):
                yield event

            # ── 3. 汇总 ──
            async for event in self.synthesizer.synthesize(state):
                yield event

            # ── 4. 评估 ──
            yield {"event": "evaluating_result", "data": {}}
            state = await self.evaluator.evaluate(state)

            score = state.eval_score
            reasoning = state.eval_reasoning

            if score >= 80 or state.loop_count == state.max_loop:
                # 评估通过（或达到最大重试次数）
                pass_msg = (
                    f"\n\n\n> **✅ 自我反馈通过** (匹配度: {score}/100)\n"
                    f"> **理由**: {reasoning}\n\n---\n\n"
                )
                yield {"event": "task_result", "data": {"message": pass_msg}}
                final_response_with_feedback = state.final_response + pass_msg

                # 持久化会话上下文
                await SessionService.update_session_contexts(
                    session_model.session_id,
                    SessionContext(
                        query=state.query,
                        task=state.context_task,
                        task_graph=state.tasks_show,
                        answer=final_response_with_feedback,
                    ).model_dump(),
                )

                # 流式生成会话标题
                async for event in self._stream_title(state):
                    yield event

                break
            else:
                # 评估未通过，准备重跑
                retry_msg = (
                    f"\n\n\n> **⚠️ 自我反馈未通过** (匹配度: {score}/100)\n"
                    f"> **理由**: {reasoning}\n"
                    f"> \n> __系统正在进行第 {state.loop_count + 1} 次重跑尝试...__\n\n---\n\n"
                )
                yield {"event": "task_result", "data": {"message": retry_msg}}
                final_response_with_feedback = state.final_response + retry_msg

                await SessionService.update_session_contexts(
                    session_model.session_id,
                    SessionContext(
                        query=state.query,
                        task=state.context_task,
                        task_graph=state.tasks_show,
                        answer=final_response_with_feedback,
                    ).model_dump(),
                )

    async def _stream_title(self, state: MindState):
        """流式生成会话标题并持久化"""
        session_model = state.session_model
        title_prompt = GenerateTitlePrompt.format(query=state.query)
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
