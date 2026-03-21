"""
最终汇总 Agent（LangGraph 节点）

负责将所有步骤结果整合为面向用户的最终答案。
"""

import json

from langchain_core.messages import HumanMessage

from toolmind.core.agents.state import AgentState
from toolmind.core.callbacks import usage_metadata_callback
from toolmind.core.models.manager import ModelManager
from toolmind.prompts.agent import FinalSynthesisPrompt


class Synthesizer:
    """最终汇总节点：整合所有步骤结果生成最终答案"""

    def __init__(self, user_id: str):
        self.user_id = user_id

    async def __call__(self, state: AgentState) -> dict:
        """LangGraph 节点函数：生成最终答案，返回状态更新"""
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
            events.append({
                "event": "task_result",
                "data": {"message": chunk.content},
            })

        return {"final_response": final_response, "events": events}
