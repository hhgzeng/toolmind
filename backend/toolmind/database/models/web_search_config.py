from datetime import datetime
from typing import Optional
from uuid import uuid4

from sqlalchemy import Column, DateTime, text
from sqlmodel import Field

from toolmind.database.models.base import SQLModelSerializable


class WebSearchConfigTable(SQLModelSerializable, table=True):
    __tablename__ = "web_search_config"

    config_id: str = Field(default_factory=lambda: uuid4().hex, primary_key=True)
    user_id: str = Field(description="用户ID", unique=True, index=True)
    api_key: str = Field(default="", description="Tavily API Key")
    enabled: bool = Field(default=True, description="是否启用联网搜索")

    update_time: Optional[datetime] = Field(sa_column=Column(
        DateTime,
        nullable=False,
        server_default=text('CURRENT_TIMESTAMP'),
        onupdate=text('CURRENT_TIMESTAMP')
    ),
        description="修改时间"
    )
    create_time: Optional[datetime] = Field(
        sa_column=Column(
            DateTime,
            nullable=False,
            server_default=text('CURRENT_TIMESTAMP')
        ),
        description="创建时间"
    )
