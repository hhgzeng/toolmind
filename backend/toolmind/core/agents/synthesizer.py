"""
最终汇总 Agent

负责将所有步骤结果整合为面向用户的最终答案，支持流式输出。
"""

import json
from typing import AsyncGenerator, List

from langchain_core.messages import HumanMessage
from toolmind.core.agents.state import MindState
from toolmind.core.callbacks import usage_metadata_callback
from toolmind.core.models.manager import ModelManager
from toolmind.prompts.mind import FinalSynthesisPrompt


class Synthesizer:
    """最终汇总 Agent：整合所有步骤结果生成最终答案"""

    def __init__(self, user_id: str):
        self.user_id = user_id

    async def synthesize(self, state: MindState) -> AsyncGenerator[dict, None]:
        """
        基于 state.steps 的执行结果生成最终汇总答案。

        流式 yield SSE 事件，完成后 state.final_response 被填充。
        """
        final_steps_payload = [
            {
                "step_id": step.step_id,
                "title": step.title,
                "target": step.target,
                "result": step.result,
            }
            for step in state.steps
        ]

        synthesis_prompt = FinalSynthesisPrompt.format(
            query=state.query,
            steps_json=json.dumps(final_steps_payload, ensure_ascii=False, indent=2),
        )

        final_response = ""
        conversation_model = await ModelManager.get_conversation_model(
            user_id=self.user_id
        )
        async for chunk in conversation_model.astream(
            [HumanMessage(content=synthesis_prompt)],
            config={"callbacks": [usage_metadata_callback]},
        ):
            final_response += chunk.content
            yield {
                "event": "task_result",
                "data": {"message": chunk.content},
            }

        state.final_response = final_response
