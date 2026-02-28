import yaml
from loguru import logger
from types import SimpleNamespace
from pydantic.v1 import BaseSettings, Field

from toolmind.schema.common import Tools, MultiModels, ModelConfig


class Settings(BaseSettings):
    aliyun_oss: dict = {}
    redis: dict = {}
    mysql: dict = {}
    server: dict = {}
    langfuse: dict = {}
    whitelist_paths: list = []
    wechat_config: dict = {}

    default_config: dict = {}

    tools: Tools = Tools()

    multi_models: MultiModels = MultiModels()


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

            if "multi_models" in data:
                models_config = SimpleNamespace()
                for model_name, model_config in data["multi_models"].items():
                    setattr(models_config, model_name, ModelConfig(**model_config))
                data["multi_models"] = models_config

            if "tools" in data:
                tools_config = SimpleNamespace()
                for tool_name, tool_config in data["tools"].items():
                    setattr(tools_config, tool_name, tool_config)
                data["tools"] = tools_config

            for key, value in data.items():
                if hasattr(app_settings, key):
                    setattr(app_settings, key, value)
    except Exception as e:
        logger.error(f"Yaml file loading error: {e}")
