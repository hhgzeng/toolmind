from typing import Optional
from uuid import uuid4

from sqlmodel import Field
from toolmind.database.models.base import SQLModelSerializable


class MindModelConfigTable(SQLModelSerializable, table=True):
    __tablename__ = "mind_model_config"

    config_id: str = Field(default_factory=lambda: uuid4().hex, primary_key=True)
    user_id: str = Field(description="用户ID", unique=True, index=True)
    conversation_model_id: Optional[str] = Field(
        default=None, description="对话和任务生成模型所属的llm_id"
    )
    tool_call_model_id: Optional[str] = Field(
        default=None, description="工具调用模型所属的llm_id"
    )
    reasoning_model_id: Optional[str] = Field(
        default=None, description="推理/评估模型所属的llm_id"
    )
