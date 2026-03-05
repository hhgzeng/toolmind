from typing import List, Any, Optional
from pydantic import BaseModel


class MindAttachment(BaseModel):
    """前端上传到 OSS 的附件元信息"""

    name: str
    url: str
    size: Optional[str] = None


class MindTask(BaseModel):
    query: str
    web_search: bool = True
    mcp_servers: List[str] = []
    # 上传到 OSS 的附件列表，供 MindAgent 在提示词中使用
    attachments: List[MindAttachment] = []


class MindTaskStep(BaseModel):
    thought: str
    step_id: str
    title: str
    target: str
    workflow: Any
    precautions: str
    input_thought: str
    input: List[str] = []

    result: str = ""
