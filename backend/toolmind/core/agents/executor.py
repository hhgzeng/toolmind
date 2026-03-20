"""
步骤执行 Agent（LangGraph 节点）

负责逐步串行执行所有 MindTaskStep，每步内部允许多轮工具调用。
"""

import json
from typing import List

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage

from toolmind.core.agents.state import MindState
from toolmind.core.agents.tool_manager import ToolManager
from toolmind.core.callbacks import usage_metadata_callback
from toolmind.core.models.manager import ModelManager
from toolmind.prompts.mind import ToolCallPrompt


class Executor:
    """步骤执行节点：逐步执行子任务并产出结果"""

    def __init__(self, user_id: str, tool_manager: ToolManager):
        self.user_id = user_id
        self.tool_manager = tool_manager

    async def __call__(self, state: MindState) -> dict:
        """LangGraph 节点函数：执行所有步骤，返回状态更新"""
        tools = await self.tool_manager.obtain_tools(
            state["mcp_servers"], state.get("web_search", True)
        )
        model = await ModelManager.get_mind_intent_model(user_id=self.user_id)
        tool_call_model = model.bind_tools(tools) if len(tools) else model

        tasks_graph = {step.step_id: step for step in state["steps"]}
        context_task = []
        events = []

        for step_info in state["steps"]:
            # 构建前置上下文
            step_context = []
            for input_step in step_info.input:
                if input_step in tasks_graph:
                    step_context.append(tasks_graph[input_step].model_dump())

            # 构建步骤 prompt
            step_prompt = ToolCallPrompt.format(
                step_info=step_info.model_dump(),
                step_context=json.dumps(step_context, ensure_ascii=False, indent=2),
                user_query=state["query"],
            )
            step_messages: List[BaseMessage] = [
                SystemMessage(content=step_prompt),
                HumanMessage(content=state["query"]),
            ]

            # 多轮工具调用循环
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
            context_task.append(step_info.model_dump())

            events.append({
                "event": "step_result",
                "data": {
                    "message": step_info.result or " ",
                    "title": step_info.title,
                },
            })

        return {"context_task": context_task, "events": events}
