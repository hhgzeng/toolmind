from sqlmodel import SQLModel, create_engine
from sqlalchemy.ext.asyncio import create_async_engine
from toolmind.database.models.agent import AgentTable
from toolmind.database.models.history import HistoryTable
from toolmind.database.models.user import SystemUser
from toolmind.database.models.tool import ToolTable
from toolmind.database.models.dialog import DialogTable
from toolmind.database.models.mcp_server import MCPServerTable, MCPServerStdioTable
from toolmind.database.models.mcp_user_config import MCPUserConfigTable
from toolmind.database.models.mcp_agent import MCPAgentTable
from toolmind.database.models.user_role import UserRole
from toolmind.database.models.llm import LLMTable
from toolmind.database.models.message import MessageDownTable, MessageLikeTable
from toolmind.database.models.role import Role
from toolmind.database.models.workspace_session import WorkSpaceSession
from toolmind.database.models.usage_stats import UsageStats
from toolmind.database.models.mind_config import MindModelConfigTable

from toolmind.settings import app_settings

from dotenv import load_dotenv

# 加载本地的env
load_dotenv(override=True)

engine = create_engine(app_settings.mysql.get('endpoint'),
                       pool_pre_ping=True, # 连接前检查其有效性
                       pool_recycle=3600, # 每隔1小时进行重连一次
                       connect_args={"charset": "utf8mb4",
                                     "use_unicode": True,
                                     'init_command': "SET SESSION time_zone = '+08:00'"})

async_engine = create_async_engine(app_settings.mysql.get('async_endpoint'),
                                   pool_pre_ping=True,  # 连接前检查其有效性
                                   pool_recycle=3600,  # 每隔1小时进行重连一次
                                   connect_args={"charset": "utf8mb4",
                                                 "use_unicode": True,
                                                 'init_command': "SET SESSION time_zone = '+08:00'"})
