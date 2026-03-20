"""
结果评估 Agent

负责评估最终答案的质量，可自主调用工具进行事实核查。
"""

import json
import re
from typing import List

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from toolmind.core.agents.state import MindState
from toolmind.core.agents.tool_manager import ToolManager
from toolmind.core.callbacks import usage_metadata_callback
from toolmind.core.models.manager import ModelManager
from toolmind.prompts.mind import EvaluateResultPrompt
from toolmind.utils.date_utils import get_beijing_time


class Evaluator:
    """结果评估 Agent：对最终答案进行质量评分"""

    def __init__(self, user_id: str, tool_manager: ToolManager):
        self.user_id = user_id
        self.tool_manager = tool_manager

    async def evaluate(self, state: MindState) -> MindState:
        """
        评估 state.final_response 是否准确回答了 state.query。

        将评分结果写入 state.eval_score 和 state.eval_reasoning。
        """
        print(f"[{get_beijing_time()}] [Evaluator] Start _evaluate_result...")

        eval_prompt = EvaluateResultPrompt.format(
            query=state.query, answer=state.final_response
        )
        messages: List[BaseMessage] = [
            SystemMessage(content="你是一个专业的结果评判助手。"),
            HumanMessage(content=eval_prompt),
        ]

        tools = await self.tool_manager.obtain_tools(
            state.mcp_servers, state.web_search
        )
        model = await ModelManager.get_reasoning_model(user_id=self.user_id)
        eval_model = model.bind_tools(tools) if len(tools) else model

        # 多轮工具调用循环
        while True:
            response = await eval_model.ainvoke(
                input=messages, config={"callbacks": [usage_metadata_callback]}
            )
            messages.append(response)

            if response.tool_calls:
                tool_messages = await self.tool_manager.parse_function_call_response(
                    response
                )
                messages.extend(tool_messages)
            else:
                break

        content = response.content.strip()
        eval_res = self._extract_and_parse_json(content)

        state.eval_score = eval_res.get("score", 100)
        state.eval_reasoning = eval_res.get("reasoning", "")

        print(
            f"[{get_beijing_time()}] [Evaluator] Score: {state.eval_score}, "
            f"Reasoning: {state.eval_reasoning}"
        )

        return state

    @staticmethod
    def _extract_and_parse_json(text: str) -> dict:
        """从字符串中提取并解析第一个 JSON 对象"""
        json_match = re.search(r"\{.*\}", text, re.DOTALL)
        json_str = json_match.group(0) if json_match else text
        return json.loads(json_str)
