from typing import Optional

from pydantic import BaseModel


class UsageStatsRequest(BaseModel):
    model: Optional[str] = None
    delta_days: int = 10000
