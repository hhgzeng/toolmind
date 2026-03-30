"""
任务规划节点：将用户 query 拆解为子任务列表
"""

import json
from typing import List

from loguru import logger
from toolmind.core.agents.model import ModelManager
from toolmind.core.agents.state import AgentState
from toolmind.core.agents.tool_manager import ToolManager
from toolmind.core.callbacks import UsageMetadataCallback
from toolmind.prompts import FixJsonPrompt, GenerateTaskPrompt
from toolmind.schema import AgentTaskStep
from toolmind.utils import extract_and_parse_json


class Planner:
    """任务规划节点"""

    def __init__(self, user_id: str, tool_manager: ToolManager):
        self.user_id = user_id
        self.tool_manager = tool_manager

    async def __call__(self, state: AgentState) -> dict:
        """执行规划，更新任务流"""
        await self.tool_manager.obtain_tools()
        # 仅传递工具摘要以节省 Token
        tools_summary = self.tool_manager.get_tools_summary()
        logger.info(f"Available tools for Planner ({len(tools_summary)}):")
        for t in tools_summary:
            logger.info(f"  - {t.get('name')}: {t.get('description')}")

        tools_str = json.dumps(tools_summary, ensure_ascii=False, indent=2)

        agent_task_prompt = GenerateTaskPrompt.format(
            tools_str=tools_str,
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

        # 转换并构建前端展示的任务图数据
        for step_info in steps:
            if not step_info.input:
                tasks_show.append({"start": "用户问题", "end": step_info.title})
            else:
                for input_step in step_info.input:
                    if input_step in tasks_graph:
                        tasks_show.append(
                            {
                                "start": tasks_graph[input_step].title,
                                "end": step_info.title,
                            }
                        )
                    else:
                        tasks_show.append({"start": "用户问题", "end": step_info.title})

        return {
            "steps": steps,
            "tasks_show": tasks_show,
            "events": [{"event": "generate_tasks", "data": {"graph": tasks_show}}],
        }

    async def _generate_tasks(self, agent_task_prompt) -> dict:
        """调用 LLM 生成任务 JSON"""
        conversation_model = await ModelManager.get_conversation_model(
            user_id=self.user_id
        )
        response = await conversation_model.ainvoke(
            input=agent_task_prompt, config={"callbacks": [UsageMetadataCallback]}
        )

        try:
            return extract_and_parse_json(response.content)
        except Exception as err:
            fix_message = FixJsonPrompt.format(
                json_content=response.content, json_error=str(err)
            )
            fix_response = await conversation_model.ainvoke(
                input=fix_message, config={"callbacks": [UsageMetadataCallback]}
            )
            try:
                return extract_and_parse_json(fix_response.content)
            except Exception as fix_err:
                raise ValueError(f"JSON 修复失败: {fix_err}")
