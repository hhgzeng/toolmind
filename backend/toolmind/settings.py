import yaml
from loguru import logger
from pydantic.v1 import BaseSettings


class Settings(BaseSettings):
    redis: dict = {}
    mysql: dict = {}
    server: dict = {}


app_settings = Settings()


async def initialize_app_settings(file_path: str = None):
    global app_settings

    file_path = file_path or "toolmind/config.yaml"
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            if data is None:
                logger.error("YAML 文件解析为空")
                return

            for key, value in data.items():
                if hasattr(app_settings, key):
                    setattr(app_settings, key, value)
    except Exception as e:
        logger.error(f"Yaml file loading error: {e}")
