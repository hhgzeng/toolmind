from fastapi import APIRouter, Body, Depends
from loguru import logger
from toolmind.api.services import MCPService, UserPayload, get_login_user
from toolmind.core.mcp import MCPManager
from toolmind.schema import resp_200, resp_500
from toolmind.utils import convert_mcp_config

router = APIRouter(tags=["MCP-Server"])


@router.post("/mcp-servers/test")
async def test_mcp_server(
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
        
        # Test connection by fetching tools directly, raising error if fails
        server_tools = await mcp_manager.multi_server_client.get_tools(
            server_name=server_name
        )
        return resp_200(data={"status": "success", "tools_count": len(server_tools)})
    except Exception as err:
        logger.error(f"MCP Server connection test failed: {err}")
        return resp_500(message=f"连接测试失败: {str(err)}")

@router.post("/mcp-servers")
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
        if not tools_params:
            raise ValueError(f"无法连接到 MCP 服务器或服务器未提供工具: {server_name}")
            
        tools_name_str = []
        for key, tools in tools_params.items():
            for tool in tools:
                tools_name_str.append(tool["name"])

        is_active = True

        await MCPService.create_mcp_server(
            server_name,
            login_user.user_id,
            url_str,
            type_str,
            config,
            tools_name_str,
            tools_params.get(server_name, []),
            is_active,
        )
        return resp_200()
    except Exception as err:
        logger.exception(err)
        return resp_500(message=str(err))


@router.get("/mcp-servers")
async def get_mcp_servers(login_user: UserPayload = Depends(get_login_user)):
    try:
        mcp_servers = await MCPService.get_all_servers(login_user.user_id)
        return resp_200(data=mcp_servers)
    except Exception as err:
        logger.error(err)
        return resp_500(message=str(err))


@router.delete("/mcp-servers/{server_id}")
async def delete_mcp_server(
    server_id: str,
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


@router.get("/mcp-servers/{server_id}/tools")
async def get_mcp_tools(
    server_id: str,
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


@router.put("/mcp-servers/{server_id}")
async def update_mcp_server(
    server_id: str,
    config: dict = Body(None, description="MCP Server的JSON配置"),
    is_active: bool = Body(None, description="连接状态"),
    tools: list[str] | None = Body(
        None, description="当前启用的工具名称列表，例如 ['search', 'browse']"
    ),
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
            if not tools_params:
                raise ValueError(f"无法连接到 MCP 服务器或服务器未提供工具: {server_name}")

            tools_str = []
            for key, tools in tools_params.items():
                for tool in tools:
                    tools_str.append(tool["name"])

            await MCPService.update_mcp_server(
                mcp_server_id=server_id,
                server_name=server_name,
                url=url_str,
                type=type_str,
                config=config,
                tools=tools_str,
                params=tools_params.get(server_name, []),
                is_active=is_active,
            )
        else:
            await MCPService.update_mcp_server(
                mcp_server_id=server_id,
                is_active=is_active,
                tools=tools,
            )
        return resp_200()
    except Exception as err:
        logger.error(err)
        return resp_500()
