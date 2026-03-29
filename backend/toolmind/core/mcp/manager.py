import asyncio
import logging
from typing import Any, Dict, List

from langchain_core.tools import BaseTool
from toolmind.core.mcp.multi_client import MultiServerMCPClient
from toolmind.schema.mcp import MCPBaseConfig

logger = logging.getLogger(__name__)


class MCPManager:
    def __init__(self, mcp_configs: List[MCPBaseConfig], timeout=10):

        connection_info = {
            mcp_config.server_name: mcp_config.model_dump(
                exclude={"server_name", "personal_config"}
            )
            for mcp_config in mcp_configs
        }

        self.multi_server_client = MultiServerMCPClient(connection_info)
        self.mcp_configs = mcp_configs

        self.timeout = timeout

    async def get_mcp_tools(self) -> list[BaseTool]:
        tools = await self.multi_server_client.get_tools()
        return tools

    async def show_mcp_tools(self) -> dict:
        result = {}
        try:
            for mcp_config in self.mcp_configs:
                server_tools = await self.multi_server_client.get_tools(
                    server_name=mcp_config.server_name
                )
                tool_list = []
                for tool in server_tools:
                    input_schema = tool.args_schema
                    tool_dict = {
                        "name": tool.name,
                        "description": tool.description,
                        "input_schema": input_schema,
                    }
                    tool_list.append(tool_dict)
                result[mcp_config.server_name] = tool_list
            return result
        except Exception as err:
            logger.info(f"Error getting MCP service tool list: {err}")
            return {}

    async def call_mcp_tools(self, tools_info: List[Dict[str, Any]]):
        """异步并发调用多个 MCP 工具"""
        # Get tool list
        tools = await self.get_mcp_tools()
        tool_dict = {tool.name: tool for tool in tools}

        # Async concurrency
        async def execute_tool(tool_name: str, args: Dict[str, Any]):
            # Create async task list
            if tool_name not in tool_dict:
                return f"Tool {tool_name} does not exist"

            tool = tool_dict[tool_name]
            try:
                if asyncio.iscoroutinefunction(tool.coroutine):
                    result = await tool.coroutine(**args)
                else:
                    result = await asyncio.to_thread(tool.coroutine, **args)
                return result
            except Exception as e:
                logger.error(f"Error executing tool: {e}")
                return f"Error executing tool {tool_name}: {e}"

        # 构造并执行并发任务
        tasks = [execute_tool(t.get("tool_name"), t.get("tool_args")) for t in tools_info]
        try:
            tool_results = await asyncio.gather(*tasks, return_exceptions=True)
            for i, result in enumerate(tool_results):
                if isinstance(result, Exception):
                    tool_results[i] = (
                        f"Error executing tool {tools_info[i].get("tool_name")}: {result}"
                    )
                    logger.error(
                        f"Error executing tool {tools_info[i].get("tool_name")}: {result}"
                    )
            return tool_results
        except Exception as err:
            logger.error(f"Error calling tools: {err}")
            return []
