from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import create_engine
from toolmind.settings import app_settings
from toolmind.database.redis import redis_client

# 加载本地的env
load_dotenv(override=True)

engine = create_engine(
    app_settings.mysql.get("endpoint"),
    pool_pre_ping=True,  # 连接前检查其有效性
    pool_recycle=3600,  # 每隔1小时进行重连一次
    connect_args={
        "charset": "utf8mb4",
        "use_unicode": True,
        "init_command": "SET SESSION time_zone = '+08:00'",
    },
)

async_engine = create_async_engine(
    app_settings.mysql.get("async_endpoint"),
    pool_pre_ping=True,  # 连接前检查其有效性
    pool_recycle=3600,  # 每隔1小时进行重连一次
    connect_args={
        "charset": "utf8mb4",
        "use_unicode": True,
        "init_command": "SET SESSION time_zone = '+08:00'",
    },
)

__all__ = ["engine", "async_engine", "redis_client"]
