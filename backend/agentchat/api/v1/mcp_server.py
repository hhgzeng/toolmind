import json
from typing import Optional

from fastapi import APIRouter, Body, Depends

from agentchat.api.services.mcp_server import MCPService
from agentchat.api.services.user import UserPayload, get_login_user
from agentchat.prompts.mcp import McpAsToolPrompt
from agentchat.schema.mcp import MCPResponseFormat
from agentchat.schema.schemas import resp_500, resp_200
from agentchat.core.agents.structured_response_agent import StructuredResponseAgent
from agentchat.services.mcp.manager import MCPManager
from loguru import logger

from agentchat.utils.convert import convert_mcp_config

router = APIRouter(tags=["MCP-Server"])


@router.post("/mcp_server")
async def create_mcp_server(
    config: dict = Body(..., description="MCP Server的JSON配置", embed=True),
    login_user: UserPayload = Depends(get_login_user),
):
    try:
        mcp_servers_config = config.get("mcpServers", {})
        if not mcp_servers_config:
            raise ValueError("Invalid config format: missing 'mcpServers'")

        server_name = list(mcp_servers_config.keys())[0]
        server_details = mcp_servers_config[server_name]

        type_str = server_details.get("type", "remote")
        url_str = server_details.get("url", "")

        server_info = {"server_name": server_name, **server_details}
        mcp_manager = MCPManager([convert_mcp_config(server_info)])
        tools_params = await mcp_manager.show_mcp_tools()
        tools_name_str = []
        for key, tools in tools_params.items():
            for tool in tools:
                tools_name_str.append(tool["name"])

        is_active = True
        logo_url = server_details.get("logo_url", "")

        structured_agent = StructuredResponseAgent(
            MCPResponseFormat, user_id=login_user.user_id
        )
        structured_response = await structured_agent.get_structured_response(
            McpAsToolPrompt.format(tools_info=json.dumps(tools_params, indent=4))
        )

        await MCPService.create_mcp_server(
            server_name,
            login_user.user_id,
            login_user.user_name,
            url_str,
            type_str,
            config,
            tools_name_str,
            tools_params.get(server_name, []),
            is_active,
            logo_url,
            structured_response.mcp_as_tool_name,
            structured_response.description,
        )
        return resp_200()
    except Exception as err:
        logger.exception(err)
        return resp_500(message=str(err))


@router.get("/mcp_server")
async def get_mcp_servers(login_user: UserPayload = Depends(get_login_user)):
    try:
        mcp_servers = await MCPService.get_all_servers(login_user.user_id)
        return resp_200(data=mcp_servers)
    except Exception as err:
        logger.error(err)
        return resp_500(message=str(err))


@router.delete("/mcp_server")
async def delete_mcp_server(
    server_id: str = Body(..., description="MCP Server 的ID", embed=True),
    login_user: UserPayload = Depends(get_login_user),
):
    try:
        # 验证是否有权限
        await MCPService.verify_user_permission(server_id, login_user.user_id)

        await MCPService.delete_server_from_id(server_id)
        return resp_200()
    except Exception as err:
        logger.error(err)
        return resp_500(message=str(err))


@router.get("/mcp_tools")
async def get_mcp_tools(
    server_id: str = Body(..., description="MCP Server 的ID", embed=True),
    login_user: UserPayload = Depends(get_login_user),
):
    try:
        # 验证是否有权限
        await MCPService.verify_user_permission(server_id, login_user.user_id)

        results = await MCPService.get_mcp_tools_info(server_id)
        return resp_200(results)
    except Exception as err:
        logger.error(err)
        return resp_500(message=str(err))


@router.put("/mcp_server")
async def update_mcp_server(
    server_id: str = Body(..., description="MCP Server 的ID"),
    config: dict = Body(None, description="MCP Server的JSON配置"),
    is_active: bool = Body(None, description="连接状态"),
    login_user: UserPayload = Depends(get_login_user),
):
    try:
        # 验证是否有权限
        await MCPService.verify_user_permission(server_id, login_user.user_id)
        mcp_server = await MCPService.get_mcp_server_from_id(server_id)

        if config is not None:
            mcp_servers_config = config.get("mcpServers", {})
            if not mcp_servers_config:
                raise ValueError("Invalid config format: missing 'mcpServers'")

            server_name = list(mcp_servers_config.keys())[0]
            server_details = mcp_servers_config[server_name]

            type_str = server_details.get("type", mcp_server.get("type", "remote"))
            url_str = server_details.get("url", mcp_server.get("url", ""))

            server_info = {
                "server_name": server_name,
                "type": type_str,
                "url": url_str,
                **server_details,
            }
            mcp_manager = MCPManager([convert_mcp_config(server_info)])
            tools_params = await mcp_manager.show_mcp_tools()
            tools_str = []
            for key, tools in tools_params.items():
                for tool in tools:
                    tools_str.append(tool["name"])

            structured_agent = StructuredResponseAgent(
                MCPResponseFormat, user_id=login_user.user_id
            )
            structured_response = await structured_agent.get_structured_response(
                McpAsToolPrompt.format(tools_info=json.dumps(tools_params, indent=4))
            )

            logo_url = server_details.get("logo_url", mcp_server.get("logo_url", ""))

            await MCPService.update_mcp_server(
                mcp_server_id=server_id,
                server_name=server_name,
                url=url_str,
                type=type_str,
                mcp_as_tool_name=structured_response.mcp_as_tool_name,
                description=structured_response.description,
                config=config,
                tools=tools_str,
                params=tools_params.get(server_name, []),
                logo_url=logo_url,
                is_active=is_active,
            )
        else:
            await MCPService.update_mcp_server(
                mcp_server_id=server_id, is_active=is_active
            )
        return resp_200()
    except Exception as err:
        logger.error(err)
        return resp_500()
