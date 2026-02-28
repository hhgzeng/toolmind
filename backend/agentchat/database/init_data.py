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

