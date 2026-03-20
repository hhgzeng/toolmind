"""
Client for connecting to multiple MCP servers and loading LangChain tools.

This module provides the MultiServerMCPClient class for managing connections to multiple
MCP servers and loading tools from them.
"""

import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from types import TracebackType

from langchain_core.tools import BaseTool
from mcp import ClientSession
from toolmind.core.mcp.sessions import (
    Connection,
    McpHttpClientFactory,
    SSEConnection,
    create_session,
)
from toolmind.core.mcp.tools import load_mcp_tools

ASYNC_CONTEXT_MANAGER_ERROR = (
    "context manager (e.g., async with MultiServerMCPClient(...)). "
    "Instead, you can do one of the following:\n"
    "1. client = MultiServerMCPClient(...)\n"
    "   tools = await client.get_tools()\n"
    "2. client = MultiServerMCPClient(...)\n"
    "   async with client.session(server_name) as session:\n"
    "       tools = await load_mcp_tools(session)"
)


class MultiServerMCPClient:
    """Client for connecting to multiple MCP servers.

    Loads LangChain-compatible tools from MCP servers.
    """

    def __init__(self, connections: dict[str, Connection] | None = None) -> None:
        """Initialize a MultiServerMCPClient with MCP servers connections.

        Args:
            connections: A dictionary mapping server names to connection configurations.
                If None, no initial connections are established.

        Example: basic usage (starting a new session on each tool call)

        ```python
        from toolmind.core.mcp.multi_client import MultiServerMCPClient

        client = MultiServerMCPClient(
            {
                "my-mcp-server": {
                    "url": "http://localhost:3000",
                    "transport": "sse",
                }
            }
        )
        all_tools = await client.get_tools()
        ```

        Example: explicitly starting a session

        ```python
        from toolmind.core.mcp.multi_client import MultiServerMCPClient
        from toolmind.core.mcp.tools import load_mcp_tools

        client = MultiServerMCPClient({...})
        async with client.session("math") as session:
            tools = await load_mcp_tools(session)
        ```

        """
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
        """Connect to an MCP server and initialize a session.

        Args:
            server_name: Name to identify this server connection
            auto_initialize: Whether to automatically initialize the session

        Raises:
            ValueError: If the server name is not found in the connections

        Yields:
            An initialized ClientSession

        """
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
        """Get a list of all tools from all connected servers.

        Args:
            server_name: Optional name of the server to get tools from.
                If None, all tools from all servers will be returned (default).

        NOTE: a new session will be created for each tool call

        Returns:
            A list of LangChain tools

        """
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

    async def __aenter__(self) -> "MultiServerMCPClient":
        """Async context manager entry point.

        Raises:
            NotImplementedError: Context manager support has been removed.
        """
        raise NotImplementedError(ASYNC_CONTEXT_MANAGER_ERROR)

    def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Async context manager exit point.

        Args:
            exc_type: Exception type if an exception occurred.
            exc_val: Exception value if an exception occurred.
            exc_tb: Exception traceback if an exception occurred.

        Raises:
            NotImplementedError: Context manager support has been removed.
        """
        raise NotImplementedError(ASYNC_CONTEXT_MANAGER_ERROR)


__all__ = [
    "McpHttpClientFactory",
    "MultiServerMCPClient",
    "SSEConnection",
]
