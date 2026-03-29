"""
步骤执行节点：串行执行子任务，支持多轮工具调用
"""

import json
from typing import List

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from loguru import logger
from toolmind.core.agents.state import AgentState
from toolmind.core.agents.tool_manager import ToolManager
from toolmind.core.callbacks import usage_metadata_callback
from toolmind.core.agents.model import ModelManager
from toolmind.prompts.agent import ToolCallPrompt


class Executor:
    """子任务执行节点"""

    def __init__(self, user_id: str, tool_manager: ToolManager):
        self.user_id = user_id
        self.tool_manager = tool_manager

    async def __call__(self, state: AgentState) -> dict:
        """执行当前步骤的 AI 推理与工具调用"""
        tools = await self.tool_manager.obtain_tools()
        model = await ModelManager.get_agent_intent_model(user_id=self.user_id)
        tool_call_model = model.bind_tools(tools) if len(tools) else model

        steps = state.get("steps", [])
        context_task = state.get("context_task", [])
        events = []

        if len(context_task) >= len(steps):
            return {}

        # 确定当前执行步骤及其上下文
        step_index = len(context_task)
        step_info = steps[step_index]
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

        # 循环执行直至模型给出最终答复（不再调用工具）
        step_summary = ""
        while True:
            response = await tool_call_model.ainvoke(
                input=step_messages,
                config={"callbacks": [usage_metadata_callback]},
            )
            step_messages.append(response)

            if response.tool_calls:
                tool_messages = await self.tool_manager.parse_function_call_response(
                    response
                )
                step_messages.extend(tool_messages)
            else:
                step_summary = response.content or ""
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
