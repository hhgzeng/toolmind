from pydantic import BaseModel, Field
from typing import Any, Dict, Optional, Literal

class MCPBaseConfig(BaseModel):
    server_name: str
    transport: str
    personal_config: Optional[Dict[str, Any]] = None

class MCPSSEConfig(MCPBaseConfig):
    transport: Literal["sse"] = "sse"
    url: str
    headers: Optional[Dict[str, Any]] = None
    timeout: Optional[float] = None
    sse_read_timeout: Optional[float] = None
    session_kwargs: Optional[Dict[str, Any]] = None


class MCPResponseFormat(BaseModel):
    mcp_as_tool_name: str = Field(..., description="根据该mcp服务下提供的工具描述生成一个工具名称，要求是2-4个英文单词组成，用下划线_隔开")
    description: str = Field(..., description="根据该mcp服务下提供的工具描述生成一个子Agent描述，当主Agent在什么场景下能够调用这个Agent的描述，描述需要加上：子智能体可以调用多个自身工具，所以将用户问题整合询问一次即可。字数在100字符以内")