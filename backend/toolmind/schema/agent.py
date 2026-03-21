from typing import Any, List

from pydantic import BaseModel


class AgentTask(BaseModel):
    query: str
    web_search: bool = True
    mcp_servers: List[str] = []


class AgentTaskStep(BaseModel):
    thought: str
    step_id: str
    title: str
    target: str
    workflow: Any
    precautions: str
    input_thought: str
    input: List[str] = []
    result: str = ""
