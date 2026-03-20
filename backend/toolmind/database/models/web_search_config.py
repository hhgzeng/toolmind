from uuid import uuid4

from sqlmodel import Field
from toolmind.database.models.base import SQLModelSerializable


class WebSearchConfigTable(SQLModelSerializable, table=True):
    __tablename__ = "web_search_config"

    config_id: str = Field(default_factory=lambda: uuid4().hex, primary_key=True)
    user_id: str = Field(description="用户ID", unique=True, index=True)
    api_key: str = Field(default="", description="Tavily API Key")
    enabled: bool = Field(default=True, description="是否启用联网搜索")
