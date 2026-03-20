from typing import List, Optional
from uuid import UUID, uuid4

from sqlalchemy import JSON, VARCHAR, Column
from sqlmodel import Field
from toolmind.database.models.base import SQLModelSerializable


class MCPServerTable(SQLModelSerializable, table=True):
    __tablename__ = "mcp_server"

    mcp_server_id: str = Field(default_factory=lambda: uuid4().hex, primary_key=True)
    server_name: str = Field(default="MCP Server", description="MCP Server名称")
    user_id: str = Field(description="MCP Server对应的创建用户")
    description: str = Field(description="该MCP Server的描述，用来当作sub-agent使用")
    mcp_as_tool_name: str = Field(description="用来当作sub-agent使用时的名称")
    url: Optional[str] = Field(None, description="MCP Server的连接地址")
    type: str = Field(
        sa_column=Column(VARCHAR(255), nullable=False),
        description="连接类型，只允许三种，sse、websocket、stdio",
    )
    config: dict = Field(
        sa_column=Column(JSON),
        description="配置，如果是远程或者stdio可以在这里存储对应的信息",
    )
    tools: List[str] = Field(
        default=[], sa_column=Column(JSON), description="MCP Server的工具列表"
    )
    params: List[dict] = Field(sa_column=Column(JSON), description="输入参数")
    is_active: bool = Field(True, description="是否启用配置")
