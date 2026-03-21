"""
任务规划 Agent（LangGraph 节点）

负责将用户 query 拆解为严格串行的子任务列表。
"""

import json
from typing import List

from toolmind.core.agents.state import AgentState
from toolmind.core.agents.tool_manager import ToolManager
from toolmind.core.callbacks import usage_metadata_callback
from toolmind.core.models.manager import ModelManager
from toolmind.prompts.agent import FixJsonPrompt, GenerateTaskPrompt
from toolmind.schema.agent import AgentTaskStep
from toolmind.utils.date_utils import get_beijing_time
from toolmind.utils.json_utils import extract_and_parse_json


class Planner:
    """任务规划节点：将用户问题拆解为子任务列表"""

    def __init__(self, user_id: str, tool_manager: ToolManager):
        self.user_id = user_id
        self.tool_manager = tool_manager

    async def __call__(self, state: AgentState) -> dict:
        """LangGraph 节点函数：执行规划，返回状态更新"""
        # 确保工具已加载（利用缓存，不会重复获取）
        await self.tool_manager.obtain_tools(
            state["mcp_servers"], state.get("web_search", True)
        )
        # 只传精简的工具摘要给 Planner prompt，大幅减少 token
        tools_summary = self.tool_manager.get_tools_summary()
        tools_str = json.dumps(tools_summary, ensure_ascii=False, indent=2)

        agent_task_prompt = GenerateTaskPrompt.format(
            current_time=get_beijing_time(),
            tools_str=await self.tool_manager.get_tools_info(),
            query=state["query"],
        )

        response_task = await self._generate_tasks(agent_task_prompt)

        # 构建步骤对象
        tasks_graph: dict[str, AgentTaskStep] = {}
        tasks_show = []
        raw_steps = response_task.get("steps", [])
        steps: List[AgentTaskStep] = []
        for raw_step in raw_steps:
            task_step = AgentTaskStep(**raw_step)
            steps.append(task_step)
            tasks_graph[task_step.step_id] = task_step

        # 构建前端展示的简化任务图
        for step_info in steps:
            if not step_info.input:
                tasks_show.append({"start": "用户问题", "end": step_info.title})
            else:
                for input_step in step_info.input:
                    if input_step in tasks_graph:
                        tasks_show.append({
                            "start": tasks_graph[input_step].title,
                            "end": step_info.title,
                        })
                    else:
                        tasks_show.append({"start": "用户问题", "end": step_info.title})

        return {
            "steps": steps,
            "tasks_show": tasks_show,
            "events": [{"event": "generate_tasks", "data": {"graph": tasks_show}}],
        }

    async def _generate_tasks(self, agent_task_prompt) -> dict:
        """调用模型进行任务规划"""
        conversation_model = await ModelManager.get_conversation_model(
            user_id=self.user_id
        )
        response = await conversation_model.ainvoke(
            input=agent_task_prompt, config={"callbacks": [usage_metadata_callback]}
        )

        try:
            return extract_and_parse_json(response.content)
        except Exception as err:
            fix_message = FixJsonPrompt.format(
                json_content=response.content, json_error=str(err)
            )
            fix_response = await conversation_json_model.ainvoke(
                input=fix_message, config={"callbacks": [usage_metadata_callback]}
            )
            try:
                return extract_and_parse_json(fix_response.content)
            except Exception as fix_err:
                raise ValueError(f"JSON 修复失败: {fix_err}")
