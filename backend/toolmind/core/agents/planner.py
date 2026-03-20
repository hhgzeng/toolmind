"""
任务规划 Agent

负责将用户 query 拆解为严格串行的子任务列表。
"""

import json
import re
from typing import List

from langchain_core.messages import BaseMessage
from toolmind.core.agents.state import MindState
from toolmind.core.agents.tool_manager import ToolManager
from toolmind.core.callbacks import usage_metadata_callback
from toolmind.core.models.manager import ModelManager
from toolmind.prompts.mind import FixJsonPrompt, GenerateTaskPrompt
from toolmind.schema.mind import MindTaskStep
from toolmind.utils.date_utils import get_beijing_time


class Planner:
    """任务规划 Agent：将用户问题拆解为子任务列表"""

    def __init__(self, user_id: str, tool_manager: ToolManager):
        self.user_id = user_id
        self.tool_manager = tool_manager

    async def plan(self, state: MindState) -> MindState:
        """
        执行任务规划，将结果写入 state.steps 和 state.tasks_show。

        返回更新后的 state。
        """
        tools = await self.tool_manager.obtain_tools(
            state.mcp_servers, state.web_search
        )
        tools_str = json.dumps(tools, ensure_ascii=False, indent=2)

        mind_task_prompt = GenerateTaskPrompt.format(
            tools_str=tools_str,
            query=state.query,
            current_time=get_beijing_time(),
        )

        response_task = await self._generate_tasks(mind_task_prompt)

        # 构建步骤对象
        tasks_graph: dict[str, MindTaskStep] = {}
        tasks_show = []
        raw_steps = response_task.get("steps", [])
        steps: List[MindTaskStep] = []
        for raw_step in raw_steps:
            task_step = MindTaskStep(**raw_step)
            steps.append(task_step)
            tasks_graph[task_step.step_id] = task_step

        # 构建前端展示的简化任务图
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

        state.steps = steps
        state.tasks_show = tasks_show
        return state

    async def _generate_tasks(self, mind_task_prompt) -> dict:
        """调用 LLM 生成任务步骤 JSON"""
        model = await ModelManager.get_conversation_model(user_id=self.user_id)
        conversation_json_model = model.bind(response_format={"type": "json_object"})
        response = await conversation_json_model.ainvoke(
            input=mind_task_prompt, config={"callbacks": [usage_metadata_callback]}
        )

        try:
            return self._extract_and_parse_json(response.content)
        except Exception as err:
            fix_message = FixJsonPrompt.format(
                json_content=response.content, json_error=str(err)
            )
            fix_response = await conversation_json_model.ainvoke(
                input=fix_message, config={"callbacks": [usage_metadata_callback]}
            )
            try:
                return self._extract_and_parse_json(fix_response.content)
            except Exception as fix_err:
                raise ValueError(f"JSON 修复失败: {fix_err}")

    @staticmethod
    def _extract_and_parse_json(text: str) -> dict:
        """从字符串中提取并解析第一个 JSON 对象"""
        json_match = re.search(r"\{.*\}", text, re.DOTALL)
        json_str = json_match.group(0) if json_match else text
        return json.loads(json_str)
