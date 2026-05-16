"""
结果评估节点：评估最终答案质量，支持自主事实核查
"""

from typing import List

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from loguru import logger
from toolmind.core.agents.model import ModelManager
from toolmind.core.agents.state import AgentState
from toolmind.core.agents.tool_manager import ToolManager
from toolmind.core.callbacks import UsageMetadataCallback
from toolmind.prompts import EvaluateResultPrompt
from toolmind.utils import extract_and_parse_json


def _message_text_content(msg: BaseMessage) -> str:
    """提取助手消息的可见文本；纯 tool_calls 时多为空。"""
    c = getattr(msg, "content", None)
    if c is None:
        return ""
    if isinstance(c, str):
        return c.strip()
    if isinstance(c, list):
        parts: list[str] = []
        for block in c:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict) and block.get("type") == "text":
                parts.append(str(block.get("text", "")))
        return "".join(parts).strip()
    return str(c).strip()


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
        eval_model = model.bind_tools(tools, parallel_tool_calls=False) if len(tools) else model

        # 循环调用工具进行事实核查，直至给出最终评分，限制最多 5 次循环
        max_iterations = 5
        iteration_count = 0
        while iteration_count < max_iterations:
            iteration_count += 1
            response = await eval_model.ainvoke(
                input=messages, config={"callbacks": [UsageMetadataCallback()]}
            )
            messages.append(response)

            if response.tool_calls:
                for tc in response.tool_calls:
                    logger.info(f"🛠️  [Evaluator] 模型请求调用工具: {tc['name']} | 参数: {tc['args']}")
                tool_messages = await self.tool_manager.parse_function_call_response(
                    response
                )
                messages.extend(tool_messages)

                if iteration_count >= max_iterations:
                    logger.warning(f"⚠️ [Evaluator] 达到最大工具调用循环次数 ({max_iterations})")
                    break
            else:
                break

        content = _message_text_content(response)
        # 触达工具次数上限时，最后一轮往往只有 tool_calls、content 为空，无法解析 JSON
        if not content:
            logger.warning(
                "[Evaluator] 末轮无可见正文（常见于触达工具次数上限后仍以工具调用收尾），"
                "追加一轮纯文本评估（不再绑定工具）"
            )
            messages.append(
                HumanMessage(
                    content=(
                        "已达到工具核查次数上限。请根据对话中已有的工具返回结果，"
                        "直接输出最终评估的 JSON 对象（含 score 与 reasoning 字段），"
                        "不要再调用任何工具。"
                    )
                )
            )
            response = await model.ainvoke(
                input=messages, config={"callbacks": [UsageMetadataCallback()]}
            )
            messages.append(response)
            content = _message_text_content(response)

        if not content:
            logger.warning("[Evaluator] 模型仍无文本输出，尝试解析将失败")

        try:
            eval_res = extract_and_parse_json(content)
            if eval_res is None:
                eval_res = {"score": 0, "reasoning": "评估结果为 null"}
        except Exception as e:
            logger.error(f"[Evaluator] 解析 JSON 失败: {e}\n模型输出: {content}")
            eval_res = {"score": 0, "reasoning": "评估结果 JSON 解析失败"}

        if not isinstance(eval_res, dict):
            eval_res = {"score": 0, "reasoning": f"评估结果类型错误: {type(eval_res)}"}

        score = eval_res.get("score", 100)
        reasoning = eval_res.get("reasoning", "")

        logger.info(f"[Evaluator] Score: {score}, Reasoning: {reasoning}")

        return {
            "eval_score": score,
            "eval_reasoning": reasoning,
            "events": [],
        }
