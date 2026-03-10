from sqlmodel import Field
from uuid import uuid4

from toolmind.database.models.base import SQLModelSerializable


class LLMTable(SQLModelSerializable, table=True):
    __tablename__ = "llm"

    llm_id: str = Field(default_factory=lambda: uuid4().hex, primary_key=True)
    model: str = Field(description='大模型的名称')
    base_url: str = Field(description='大模型的base url')
    api_key: str = Field(description='大模型的api key')
    provider: str = Field(description='大模型的提供商')
    user_id: str = Field(description='大模型创建者的ID')


