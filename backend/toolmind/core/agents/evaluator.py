"""
结果评估节点：评估最终答案质量，支持自主事实核查
"""

from typing import List

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from loguru import logger
from toolmind.core.agents.state import AgentState
from toolmind.core.agents.tool_manager import ToolManager
from toolmind.core.callbacks import usage_metadata_callback
from toolmind.core.agents.model import ModelManager
from toolmind.prompts.agent import EvaluateResultPrompt
from toolmind.utils.json_utils import extract_and_parse_json


class Evaluator:
    """结果评估节点"""

    def __init__(self, user_id: str, tool_manager: ToolManager):
        self.user_id = user_id
        self.tool_manager = tool_manager

    async def __call__(self, state: AgentState) -> dict:
        """运行评估逻辑，支持多轮工具调用核查事实"""
        logger.info("[Evaluator] Start _evaluate_result...")

        eval_prompt = EvaluateResultPrompt.format(
            query=state["query"], answer=state["final_response"]
        )
        messages: List[BaseMessage] = [
            SystemMessage(content="你是一个专业的结果评判助手。"),
            HumanMessage(content=eval_prompt),
        ]

        tools = await self.tool_manager.obtain_tools()
        model = await ModelManager.get_reasoning_model(user_id=self.user_id)
        eval_model = model.bind_tools(tools) if len(tools) else model

        # 循环调用工具进行事实核查，直至给出最终评分
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
        eval_res = extract_and_parse_json(content)

        score = eval_res.get("score", 100)
        reasoning = eval_res.get("reasoning", "")

        logger.info(f"[Evaluator] Score: {score}, Reasoning: {reasoning}")

        return {
            "eval_score": score,
            "eval_reasoning": reasoning,
            "events": [],
        }
