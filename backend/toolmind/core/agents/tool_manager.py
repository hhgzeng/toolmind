"""
工具管理模块

负责 MCP 工具和内置工具（web_search）的获取、缓存和执行。
"""

import json
from typing import List, Optional

from langchain_core.messages import AIMessage, ToolMessage
from langchain_core.tools.base import ToolException
from langchain_core.utils.function_calling import convert_to_openai_tool
from toolmind.api.services.mcp_server import MCPService
from toolmind.api.services.web_search import tavily_search as web_search
from toolmind.core.mcp.manager import MCPManager
from toolmind.schema.mcp import MCPConfig
from toolmind.utils.convert import convert_mcp_config, mcp_tool_to_args_schema


class ToolManager:
    """管理 MCP 工具和内置工具的获取与执行"""

    def __init__(self, user_id: str):
        self.user_id = user_id
        self.mcp_manager: Optional[MCPManager] = None
        self.mcp_tools = []
        self.tool_mcp_server_dict = {}

    async def obtain_tools(
        self, mcp_servers: List[str], enable_web_search: bool = False
    ) -> list:
        """获取可用工具列表（MCP + web_search）"""
        tools = []

        # 内置搜索工具
        from toolmind.database.dao.web_search_config import WebSearchConfigDao

        user_config = await WebSearchConfigDao.get_config_by_user_id(self.user_id)

        if user_config:
            global_web_search_enabled = user_config.enabled
        else:
            global_web_search_enabled = True

        if enable_web_search and global_web_search_enabled:
            tools.append(convert_to_openai_tool(web_search))

        # MCP 工具
        mcp_tools = await self._get_mcp_tools(mcp_servers)
        mcp_tools = [
            mcp_tool_to_args_schema(tool.name, tool.description, tool.args_schema)
            for tool in mcp_tools
        ]
        tools.extend(mcp_tools)

        return tools

    async def _get_mcp_tools(self, mcp_servers: List[str]):
        """获取并缓存 MCP 工具"""
        if self.mcp_tools:
            return self.mcp_tools

        servers_config = []
        enabled_tools = set()
        for mcp_id in mcp_servers:
            mcp_server = await MCPService.get_mcp_server_from_id(mcp_id)
            mcp_config = MCPConfig(**mcp_server)

            if mcp_config.tools:
                enabled_tools.update(mcp_config.tools)
                self.tool_mcp_server_dict.update(
                    {tool: mcp_config.mcp_server_id for tool in mcp_config.tools}
                )
            servers_config.append(convert_mcp_config(mcp_config.model_dump()))

        self.mcp_manager = MCPManager(servers_config)
        all_mcp_tools = await self.mcp_manager.get_mcp_tools()

        if enabled_tools:
            filtered_tools = [
                tool for tool in all_mcp_tools if tool.name in enabled_tools
            ]
        else:
            filtered_tools = all_mcp_tools
            for mcp_id in mcp_servers:
                mcp_server = await MCPService.get_mcp_server_from_id(mcp_id)
                mcp_config = MCPConfig(**mcp_server)
                for tool in filtered_tools:
                    self.tool_mcp_server_dict.setdefault(
                        tool.name, mcp_config.mcp_server_id
                    )

        self.mcp_tools = filtered_tools
        return filtered_tools

    async def process_tool_result(self, tool_name: str, tool_args: dict) -> str:
        """执行单个工具调用并返回文本结果"""

        def find_mcp_tool(name):
            for tool in self.mcp_tools:
                if tool.name == name:
                    return tool
            return None

        if tool := find_mcp_tool(tool_name):
            try:
                text_content, no_text_content = await tool.coroutine(**tool_args)
            except ToolException as e:
                text_content = f"[工具执行失败] {tool_name}: {e}"
            except Exception as e:
                text_content = f"[工具执行失败] {tool_name}: {type(e).__name__} - {e}"
        else:
            if tool_name == "web_search":
                from toolmind.api.services.web_search import _tavily_search
                from toolmind.database.dao.web_search_config import WebSearchConfigDao

                user_config = await WebSearchConfigDao.get_config_by_user_id(
                    self.user_id
                )
                api_key = user_config.api_key if user_config else None
                text_content = _tavily_search(**tool_args, api_key=api_key)
            else:
                text_content = f"[工具执行失败] 未知内置工具 {tool_name}"

        return text_content

    async def parse_function_call_response(
        self, message: AIMessage
    ) -> List[ToolMessage]:
        """解析 AI 的 tool_calls 并批量执行，返回 ToolMessage 列表"""
        tool_messages = []
        if message.tool_calls:
            for tool_call in message.tool_calls:
                tool_name = tool_call.get("name")
                tool_args = tool_call.get("args")
                tool_call_id = tool_call.get("id")

                content = await self.process_tool_result(tool_name, tool_args)
                tool_messages.append(
                    ToolMessage(
                        content=content, name=tool_name, tool_call_id=tool_call_id
                    )
                )
        return tool_messages
