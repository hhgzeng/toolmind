import inspect
import json
from typing import List

from langchain_core.messages import ToolCall
from openai.types.chat import ChatCompletionMessageToolCall
from toolmind.schema.mcp import MCPSSEConfig


def convert_mcp_config(servers_info: dict | list):

    def convert_single_mcp(server_info):
        if isinstance(server_info, dict):
            # 当前产品只支持 SSE（前端也只暴露 sse 配置）。
            # 兼容历史字段：remote 视为 sse。
            type_ = server_info.get("type")
            if type_ in ["sse", "remote", None, ""]:
                return MCPSSEConfig(
                    url=server_info.get("url", ""),
                    server_name=server_info.get("server_name"),
                )

            raise ValueError(
                f"Unsupported MCP server type '{type_}'. Only 'sse' is supported."
            )

    if isinstance(servers_info, dict):
        return convert_single_mcp(servers_info)
    else:
        return [convert_single_mcp(server_info) for server_info in servers_info]


def mcp_tool_to_args_schema(name, description, args_schema) -> dict:
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": args_schema,
        },
    }


