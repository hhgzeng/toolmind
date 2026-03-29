"""
最终汇总节点：将所有子任务结果整合为最终回答
"""

import json

from langchain_core.messages import HumanMessage
from toolmind.core.agents.state import AgentState
from toolmind.core.callbacks import usage_metadata_callback
from toolmind.core.agents.model import ModelManager
from toolmind.prompts.agent import FinalSynthesisPrompt


class Synthesizer:
    """最终汇总节点"""

    def __init__(self, user_id: str):
        self.user_id = user_id

    async def __call__(self, state: AgentState) -> dict:
        """执行聚合逻辑并流式返回结果"""
        final_steps_payload = [
            {
                "step_id": step.step_id,
                "title": step.title,
                "target": step.target,
                "result": step.result,
            }
            for step in state["steps"]
        ]

        synthesis_prompt = FinalSynthesisPrompt.format(
            query=state["query"],
            steps_json=json.dumps(final_steps_payload, ensure_ascii=False, indent=2),
        )

        final_response = ""
        events = []
        conversation_model = await ModelManager.get_conversation_model(
            user_id=self.user_id
        )
        async for chunk in conversation_model.astream(
            [HumanMessage(content=synthesis_prompt)],
            config={"callbacks": [usage_metadata_callback]},
        ):
            final_response += chunk.content
            events.append(
                {
                    "event": "task_result",
                    "data": {"message": chunk.content},
                }
            )

        events.append({"event": "evaluating_result", "data": {}})
        return {"final_response": final_response, "events": events}
