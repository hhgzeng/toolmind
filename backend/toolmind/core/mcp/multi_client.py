"""
多 MCP 服务客户端，支持连接多个服务端并加载 LangChain 工具。
"""

import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from langchain_core.tools import BaseTool
from mcp import ClientSession
from toolmind.core.mcp.sessions import Connection, create_session
from toolmind.core.mcp.tools import load_mcp_tools


class MultiServerMCPClient:
    """管理多个 MCP 服务端的客户端，加载兼容 LangChain 的工具"""

    def __init__(self, connections: dict[str, Connection] | None = None) -> None:
        """初始化客户端，可以传入多个服务端的连接配置"""
        self.connections: dict[str, Connection] = (
            connections if connections is not None else {}
        )

    @asynccontextmanager
    async def session(
        self,
        server_name: str,
        *,
        auto_initialize: bool = True,
    ) -> AsyncIterator[ClientSession]:
        """连接指定的 MCP 服务端并初始化会话"""
        if server_name not in self.connections:
            msg = (
                f"Couldn't find a server with name '{server_name}', "
                f"expected one of '{list(self.connections.keys())}'"
            )
            raise ValueError(msg)

        async with create_session(self.connections[server_name]) as session:
            if auto_initialize:
                await session.initialize()
            yield session

    async def get_tools(self, *, server_name: str | None = None) -> list[BaseTool]:
        """从所有或指定的连接中获取工具列表（每个工具调用都会创建新会话）"""
        if server_name is not None:
            if server_name not in self.connections:
                msg = (
                    f"Couldn't find a server with name '{server_name}', "
                    f"expected one of '{list(self.connections.keys())}'"
                )
                raise ValueError(msg)
            return await load_mcp_tools(None, connection=self.connections[server_name])

        all_tools: list[BaseTool] = []
        load_mcp_tool_tasks = []
        for connection in self.connections.values():
            load_mcp_tool_task = asyncio.create_task(
                load_mcp_tools(None, connection=connection)
            )
            load_mcp_tool_tasks.append(load_mcp_tool_task)
        tools_list = await asyncio.gather(*load_mcp_tool_tasks)
        for tools in tools_list:
            all_tools.extend(tools)
        return all_tools

__all__ = ["MultiServerMCPClient"]
