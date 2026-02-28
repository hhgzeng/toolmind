from pydantic import BaseModel
from langchain.agents import create_agent
from langchain.agents.structured_output import ToolStrategy

from toolmind.core.models.manager import ModelManager


class StructuredResponseAgent:
    def __init__(self, response_format, user_id: str = None):
        self.response_format = response_format
        self.user_id = user_id

    async def _create_structured_agent(self):
        model = await ModelManager.get_conversation_model(user_id=self.user_id)
        return create_agent(
            model=model, response_format=ToolStrategy(self.response_format)
        )

    async def get_structured_response(self, messages):
        structured_agent = await self._create_structured_agent()
        result = await structured_agent.ainvoke({"messages": messages})
        return result["structured_response"]
