import json

from loguru import logger
from sqlmodel import SQLModel

from toolmind.database import engine, SystemUser
from toolmind.api.services.llm import LLMService
from toolmind.api.services.mcp_server import MCPService
from toolmind.database.models.user import AdminUser
from toolmind.prompts.mcp import McpAsToolPrompt
from toolmind.schema.mcp import MCPResponseFormat
from toolmind.core.agents.structured_response_agent import StructuredResponseAgent
from toolmind.services.mcp.manager import MCPManager
from toolmind.settings import app_settings
from toolmind.utils.convert import convert_mcp_config


# 创建MySQL数据表
async def init_database():
    try:
        SQLModel.metadata.create_all(engine)
        logger.info("Create MySQL Table Successful")
    except Exception as err:
        logger.error(f"Create MySQL Table Error: {err}")

