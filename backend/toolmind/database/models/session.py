from datetime import datetime
from typing import Optional, List
from sqlmodel import Field
from uuid import uuid4
from pydantic import BaseModel
from sqlalchemy import Column, JSON, DateTime, Boolean, text
from toolmind.database.models.base import SQLModelSerializable


class SessionBase(SQLModelSerializable):
    title: str = Field(..., description="会话标题")
    user_id: str = Field(..., description="会话对应的 User ID")
    contexts: List[dict] = Field(
        [],
        sa_column=Column(JSON),
        description="JSON, 含 tasks、questions、answers 等字段的结构化对话上下文",
    )
    is_pinned: bool = Field(
        default=False,
        sa_column=Column(
            Boolean,
            nullable=False,
            server_default=text("0"),
        ),
        description="是否置顶该会话",
    )

class Session(SessionBase, table=True):
    # 保持表名不变，避免隐式引入数据库迁移
    __tablename__ = "workspace_session"

    session_id: str = Field(
        default_factory=lambda: uuid4().hex,
        primary_key=True,
        description="会话 ID",
    )
    update_time: Optional[datetime] = Field(
        sa_column=Column(
            DateTime,
            nullable=False,
            server_default=text("CURRENT_TIMESTAMP"),
            onupdate=text("CURRENT_TIMESTAMP"),
        ),
        description="修改时间",
    )
    create_time: Optional[datetime] = Field(
        sa_column=Column(
            DateTime,
            nullable=False,
            server_default=text("CURRENT_TIMESTAMP"),
        ),
        description="创建时间",
    )


class SessionCreate(BaseModel):
    title: str
    user_id: str
    session_id: str = None  # 允许传入 session_id，如果为 None 则自动生成
    contexts: list[dict] = []
    is_pinned: bool = False


class SessionContext(BaseModel):
    query: str
    task: list[dict] = []
    task_graph: list[dict] = []
    answer: str
