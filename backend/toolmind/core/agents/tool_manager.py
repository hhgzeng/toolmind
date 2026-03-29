"""
工具管理：负责 MCP 与内置工具的获取与调度执行
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
    """工具管理器"""

    def __init__(self, user_id: str):
        self.user_id = user_id
        self.mcp_manager: Optional[MCPManager] = None
        self.mcp_tools = []
        self.tool_mcp_server_dict = {}
        self.tools = []
        self._web_search_enabled: bool = True
        self._web_search_api_key: Optional[str] = None

    async def _ensure_web_search_config(self):
        """获取并同步 Web 搜索配置"""
        from toolmind.database.dao.web_search import WebSearchConfigDao

        user_config = await WebSearchConfigDao.get_config_by_user_id(self.user_id)
        if user_config:
            self._web_search_enabled = user_config.enabled
            self._web_search_api_key = user_config.api_key
        else:
            self._web_search_enabled = True
            self._web_search_api_key = None

    async def obtain_tools(self) -> list:
        """汇总所有可用工具（内置 + MCP）"""
        tools = []

        # 内置搜索工具
        await self._ensure_web_search_config()
        if self._web_search_enabled:
            tools.append(convert_to_openai_tool(web_search))

        mcp_tools = await self._get_mcp_tools()
        mcp_tools = [
            mcp_tool_to_args_schema(tool.name, tool.description, tool.args_schema)
            for tool in mcp_tools
        ]
        tools.extend(mcp_tools)

        self.tools = tools
        return tools

    def get_tools_summary(self) -> list[dict]:
        """提取工具摘要给 Planner（仅 name/description）"""
        if not self.tools:
            return []
        summary = []
        for tool in self.tools:
            func = tool.get("function", tool)
            summary.append(
                {
                    "name": func.get("name", ""),
                    "description": func.get("description", ""),
                }
            )
        return summary

    async def _get_mcp_tools(self):
        """从 MCP 服务中加载工具"""
        self.tool_mcp_server_dict = {}
        servers_config = []
        enabled_tools = set()

        all_servers = await MCPService.get_all_servers(self.user_id)
        mcp_servers = [
            server["mcp_server_id"]
            for server in all_servers
            if server.get("is_active")
        ]

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
            for mcp_id, mcp_config in mcp_configs.items():
                for tool in filtered_tools:
                    self.tool_mcp_server_dict.setdefault(
                        tool.name, mcp_config.mcp_server_id
                    )

        self.mcp_tools = filtered_tools
        return filtered_tools

    async def process_tool_result(self, tool_name: str, tool_args: dict) -> str:
        """调用工具并统一返回文本结果"""

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
        """并行执行模型返回的所有 tool_calls"""
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
