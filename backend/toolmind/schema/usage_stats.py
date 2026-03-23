from typing import Optional
from enum import Enum
from pydantic import BaseModel

class UsageStatsRequest(BaseModel):
    model: Optional[str] = None
    delta_days: int = 10000

