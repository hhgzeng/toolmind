from typing import Optional
from enum import Enum
from pydantic import BaseModel

class UsageStatsRequest(BaseModel):
    agent: Optional[str] = None
    model: Optional[str] = None
    delta_days: int = 10000

class UsageStatsAgentType(str, Enum):
    mind_agent = "Mind-Agent"

class UsageStatsModelType(str, Enum):
    tool_call_model = "tool_call_model"
    conversation_model = "conversation_model"
