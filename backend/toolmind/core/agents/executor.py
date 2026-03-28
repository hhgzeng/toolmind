"""
步骤执行 Agent（LangGraph 节点）

负责逐步串行执行所有 AgentTaskStep，每步内部允许多轮工具调用。
"""

import json
from typing import List

from loguru import logger
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from toolmind.core.agents.state import AgentState
from toolmind.core.agents.tool_manager import ToolManager
from toolmind.core.callbacks import usage_metadata_callback
from toolmind.core.models.manager import ModelManager
from toolmind.prompts.agent import ToolCallPrompt


class Executor:
    """步骤执行节点：逐步执行子任务并产出结果"""

    def __init__(self, user_id: str, tool_manager: ToolManager):
        self.user_id = user_id
        self.tool_manager = tool_manager

    async def __call__(self, state: AgentState) -> dict:
        """LangGraph 节点函数：执行所有步骤，返回状态更新"""
        tools = await self.tool_manager.obtain_tools()
        model = await ModelManager.get_agent_intent_model(user_id=self.user_id)
        tool_call_model = model.bind_tools(tools) if len(tools) else model

        logger.info(f"[DEBUG] Executor available tools: {[t.get('function', {}).get('name', t.get('name')) for t in tools]}")

        steps = state.get("steps", [])
        context_task = state.get("context_task", [])
        events = []

        # 如果所有步骤已执行完毕，直接返回
        if len(context_task) >= len(steps):
            return {}

        # 提取当前需要执行的步骤
        step_index = len(context_task)
        step_info = steps[step_index]

        tasks_graph = {step.step_id: step for step in steps}

        # 准备工具摘要供 Prompt 使用
        tools_summary = self.tool_manager.get_tools_summary()
        tools_str = json.dumps(tools_summary, ensure_ascii=False, indent=2)

        # 构建前置上下文
        step_context = []
        for input_step in step_info.input:
            if input_step in tasks_graph:
                step_context.append(tasks_graph[input_step].model_dump())

        # 构建步骤 prompt
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

        # 多轮工具调用循环
        step_summary = ""
        while True:
            response = await tool_call_model.ainvoke(
                input=step_messages,
                config={"callbacks": [usage_metadata_callback]},
            )
            step_messages.append(response)

            if response.tool_calls:
                for tool_call in response.tool_calls:
                    logger.info(f"[DEBUG] Agent calling tool: {tool_call.get('name')} | Args: {tool_call.get('args')}")
                tool_messages = (
                    await self.tool_manager.parse_function_call_response(response)
                )
                step_messages.extend(tool_messages)
            else:
                step_summary = response.content or ""
                break

        step_info.result = step_summary
        
        # 将新结果追加到 context_task
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
