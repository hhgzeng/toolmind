import json

from loguru import logger
from sqlmodel import SQLModel

from agentchat.database import engine, SystemUser

# from agentchat.api.services.agent import AgentService
from agentchat.api.services.llm import LLMService

# from agentchat.api.services.tool import ToolService
from agentchat.api.services.mcp_server import MCPService
from agentchat.database.models.user import AdminUser
from agentchat.prompts.mcp import McpAsToolPrompt
from agentchat.schema.mcp import MCPResponseFormat
from agentchat.core.agents.structured_response_agent import StructuredResponseAgent
from agentchat.services.mcp.manager import MCPManager
from agentchat.settings import app_settings
from agentchat.utils.convert import convert_mcp_config


# 创建MySQL数据表
async def init_database():
    try:
        SQLModel.metadata.create_all(engine)
        logger.info("Create MySQL Table Successful")
    except Exception as err:
        logger.error(f"Create MySQL Table Error: {err}")


# 初始化默认工具
# async def init_default_agent():
#     try:
#         # if redis_client.setNx('init_default_agent', '1'):
#         result = await AgentService.get_agent()
#         if len(result) == 0:
#             logger.info("Begin Init Agent In Mysql")

#             await insert_tools_to_mysql()  # 初始化工具
#             await insert_llm_to_mysql()  # 初始化LLM
#             await insert_agent_to_mysql()  # 初始化Agent
#         else:
#             logger.info("Init Agent Already")
#     except Exception as err:
#         logger.error(f"Init Default Agent Error: {err}")


async def load_default_tool():
    with open("./agentchat/config/tool.json", "r", encoding="utf-8") as f:
        result = json.load(f)
    return result
