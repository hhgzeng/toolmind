"""
工具管理模块

负责 MCP 工具和内置工具（web_search）的获取、缓存和执行。
"""

import asyncio
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
        # —— 工具列表缓存 ——
        self._cached_tools: Optional[list] = None
        self._cached_tools_key: Optional[tuple] = None
        # —— web search 配置缓存 ——
        self._web_search_config_cached = False
        self._web_search_enabled: bool = True
        self._web_search_api_key: Optional[str] = None

    async def _ensure_web_search_config(self):
        """查询并缓存 web search 配置（整个生命周期只查一次 DB）"""
        if self._web_search_config_cached:
            return
        from toolmind.database.dao.web_search import WebSearchConfigDao

        user_config = await WebSearchConfigDao.get_config_by_user_id(self.user_id)
        if user_config:
            self._web_search_enabled = user_config.enabled
            self._web_search_api_key = user_config.api_key
        else:
            self._web_search_enabled = True
            self._web_search_api_key = None
        self._web_search_config_cached = True

    async def obtain_tools(
        self, mcp_servers: List[str], enable_web_search: bool = False
    ) -> list:
        """获取可用工具列表（MCP + web_search），带实例级缓存"""
        cache_key = (tuple(sorted(mcp_servers)), enable_web_search)
        if self._cached_tools is not None and self._cached_tools_key == cache_key:
            return self._cached_tools

        tools = []

        # 内置搜索工具
        await self._ensure_web_search_config()
        if enable_web_search and self._web_search_enabled:
            tools.append(convert_to_openai_tool(web_search))

        # MCP 工具
        mcp_tools = await self._get_mcp_tools(mcp_servers)
        mcp_tools = [
            mcp_tool_to_args_schema(tool.name, tool.description, tool.args_schema)
            for tool in mcp_tools
        ]
        tools.extend(mcp_tools)

        self._cached_tools = tools
        self._cached_tools_key = cache_key
        return tools

    def get_tools_summary(self) -> list[dict]:
        """返回工具的精简摘要（仅 name + description），供 Planner prompt 使用"""
        if not self._cached_tools:
            return []
        summary = []
        for tool in self._cached_tools:
            func = tool.get("function", tool)
            summary.append({
                "name": func.get("name", ""),
                "description": func.get("description", ""),
            })
        return summary

    async def _get_mcp_tools(self, mcp_servers: List[str]):
        """获取并缓存 MCP 工具"""
        if self.mcp_tools:
            return self.mcp_tools

        servers_config = []
        enabled_tools = set()
        # 批量获取 MCP 配置，记录到 dict 中避免后续重复查询
        mcp_configs: dict[str, MCPConfig] = {}
        for mcp_id in mcp_servers:
            mcp_server = await MCPService.get_mcp_server_from_id(mcp_id)
            mcp_config = MCPConfig(**mcp_server)
            mcp_configs[mcp_id] = mcp_config

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
            # 使用已缓存的 mcp_configs，不再重复查 DB
            for mcp_id, mcp_config in mcp_configs.items():
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

                await self._ensure_web_search_config()
                text_content = _tavily_search(
                    **tool_args, api_key=self._web_search_api_key
                )
            else:
                text_content = f"[工具执行失败] 未知内置工具 {tool_name}"

        return text_content

    async def parse_function_call_response(
        self, message: AIMessage
    ) -> List[ToolMessage]:
        """解析 AI 的 tool_calls 并并发执行，返回 ToolMessage 列表"""
        if not message.tool_calls:
            return []

        # 并发执行所有工具调用
        async def _run_one(tool_call: dict) -> ToolMessage:
            tool_name = tool_call.get("name")
            tool_args = tool_call.get("args")
            tool_call_id = tool_call.get("id")
            content = await self.process_tool_result(tool_name, tool_args)
            return ToolMessage(
                content=content, name=tool_name, tool_call_id=tool_call_id
            )

        tool_messages = await asyncio.gather(
            *[_run_one(tc) for tc in message.tool_calls]
        )
        return list(tool_messages)
