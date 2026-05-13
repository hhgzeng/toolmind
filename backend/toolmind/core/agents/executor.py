"""
步骤执行节点：串行执行子任务，支持多轮工具调用
"""

import json
from typing import List

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from loguru import logger
from toolmind.core.agents.model import ModelManager
from toolmind.core.agents.state import AgentState
from toolmind.core.agents.tool_manager import ToolManager
from toolmind.core.callbacks import UsageMetadataCallback
from toolmind.prompts import ToolCallPrompt


class Executor:
    """子任务执行节点"""

    def __init__(self, user_id: str, tool_manager: ToolManager):
        self.user_id = user_id
        self.tool_manager = tool_manager

    async def __call__(self, state: AgentState) -> dict:
        """执行当前步骤的 AI 推理与工具调用"""
        tools = await self.tool_manager.obtain_tools()
        model = await ModelManager.get_agent_intent_model(user_id=self.user_id)
        tool_call_model = model.bind_tools(tools, parallel_tool_calls=True) if len(tools) else model
        conversation_model = await ModelManager.get_conversation_model(user_id=self.user_id)

        steps = state.get("steps", [])
        context_task = state.get("context_task", [])
        events = []

        if len(context_task) >= len(steps):
            return {}

        # 确定当前执行步骤及其上下文
        step_index = len(context_task)
        step_info = steps[step_index]
        logger.info(f"👉 正在执行步骤 [{step_index + 1}/{len(steps)}]: {step_info.title}")
        tasks_graph = {step.step_id: step for step in steps}

        tools_summary = self.tool_manager.get_tools_summary()
        tools_str = json.dumps(tools_summary, ensure_ascii=False, indent=2)

        step_context = []
        for input_step in step_info.input:
            if input_step in tasks_graph:
                step_context.append(tasks_graph[input_step].model_dump())

        step_prompt = ToolCallPrompt.format(
            step_info=step_info.model_dump(),
            step_context=json.dumps(step_context, ensure_ascii=False, indent=2),
            tools_str=tools_str,
            user_query=state["query"],
        )
        step_messages: List[BaseMessage] = [
            SystemMessage(content=step_prompt),
            HumanMessage(content=state["query"]),
        ]

        # 循环执行直至模型给出最终答复（不再调用工具），限制最多 5 次循环
        step_summary = ""
        max_iterations = 3
        iteration_count = 0
        while iteration_count < max_iterations:
            iteration_count += 1
            response = await tool_call_model.ainvoke(
                input=step_messages,
                config={"callbacks": [UsageMetadataCallback()]},
            )
            step_messages.append(response)

            if response.tool_calls:
                for tc in response.tool_calls:
                    logger.info(f"🛠️  模型请求调用工具: {tc['name']} | 参数: {tc['args']}")
                tool_messages = await self.tool_manager.parse_function_call_response(
                    response
                )
                step_messages.extend(tool_messages)

                if iteration_count >= max_iterations:
                    logger.warning(f"⚠️ 步骤 [{step_info.title}] 达到最大工具调用循环次数 ({max_iterations})")

                    tool_results = []
                    for msg in step_messages:
                        if getattr(msg, "type", "") == "tool":
                            tool_results.append(str(msg.content))

                    gathered_content = "\n\n".join(tool_results)
                    # 达到最大工具循环次数后：用已获得的工具结果做一次“收尾生成”，产出最终 step_summary（不再调用工具）
                    finalization_prompt = (
                        "你正在执行一个子任务步骤。由于工具调用轮次已达到上限，不能再调用任何工具。\n"
                        "请基于【用户问题】、【步骤信息】以及【已获得的工具结果】输出该步骤的最终结论（step_summary）。\n"
                        "要求：\n"
                        "- 直接给出可用的最终答案/结论/产出，不要写“执行中断/达到上限/无法继续”等过程性话术。\n"
                        "- 如果工具结果不足以完全确定，请给出最合理的推断，并明确列出仍缺失的关键信息（用简短要点）。\n"
                        "- 不要再提出要调用什么工具。\n\n"
                        f"【用户问题】\n{state['query']}\n\n"
                        f"【步骤信息】\n{json.dumps(step_info.model_dump(), ensure_ascii=False, indent=2)}\n\n"
                        f"【已获得的工具结果】\n{gathered_content.strip() or '(无)'}\n"
                    )
                    final_response = await conversation_model.ainvoke(
                        input=[SystemMessage(content=finalization_prompt)],
                        config={"callbacks": [UsageMetadataCallback()]},
                    )
                    step_summary = (getattr(final_response, "content", "") or "").strip()
                    if not step_summary:
                        # 极端兜底：如果模型没有返回内容，则退化为工具结果汇总
                        step_summary = gathered_content.strip() or "未能生成该步骤的最终结论。"
                    break
            else:
                step_summary = response.content or ""
                logger.info(f"✅ 步骤 [{step_info.title}] 执行完成")
                break

        step_info.result = step_summary
        new_context_task = context_task + [step_info.model_dump()]

        events.append(
            {
                "event": "step_result",
                "data": {
                    "message": step_info.result or " ",
                    "title": step_info.title,
                },
            }
        )

        return {"context_task": new_context_task, "events": events, "steps": steps}
