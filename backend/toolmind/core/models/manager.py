"""
模型管理器 — 带请求级缓存

使用 TTLCache 避免同一 user_id 在短时间内反复查 DB + 创建模型实例。
"""

import time
from typing import Optional

from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI
from toolmind.core.models.reason_model import ReasoningModel
from toolmind.database.dao.llm import LLMDao
from toolmind.database.dao.mind_config import MindModelConfigDao


class _TTLCache:
    """简易 TTL 缓存，key → (value, expire_at)"""

    def __init__(self, ttl: int = 60):
        self._store: dict[str, tuple] = {}
        self._ttl = ttl

    def get(self, key: str):
        entry = self._store.get(key)
        if entry and entry[1] > time.monotonic():
            return entry[0]
        self._store.pop(key, None)
        return None

    def set(self, key: str, value):
        self._store[key] = (value, time.monotonic() + self._ttl)


class ModelManager:

    # 模型配置缓存（60s TTL），避免频繁查 DB
    _config_cache = _TTLCache(ttl=60)
    # 模型实例缓存（60s TTL），避免重复创建 ChatOpenAI
    _model_cache = _TTLCache(ttl=60)

    @classmethod
    async def _get_model_config(cls, user_id: str, config_type: str) -> Optional[dict]:
        """获取模型配置，带 TTL 缓存"""
        cache_key = f"{user_id}:{config_type}"
        cached = cls._config_cache.get(cache_key)
        if cached is not None:
            return cached

        user_config = await MindModelConfigDao.get_config_by_user_id(user_id)
        if not user_config:
            return None

        llm_id = None
        if config_type == "conversation":
            llm_id = user_config.conversation_model_id
        elif config_type == "tool_call":
            llm_id = user_config.tool_call_model_id
        elif config_type == "reasoning":
            llm_id = user_config.reasoning_model_id

        if not llm_id:
            return None

        llm_record = await LLMDao.get_llm_by_id(llm_id)
        if not llm_record:
            return None

        result = llm_record.to_dict()
        cls._config_cache.set(cache_key, result)
        return result

    @classmethod
    async def _get_or_create_chat_model(
        cls, user_id: str, config_type: str
    ) -> BaseChatModel:
        """获取或创建 ChatOpenAI 实例（带缓存）"""
        cache_key = f"model:{user_id}:{config_type}"
        cached = cls._model_cache.get(cache_key)
        if cached is not None:
            return cached

        model_config = await cls._get_model_config(user_id, config_type)
        if not model_config:
            raise ValueError(
                f"User {user_id} has no {config_type} model configuration in database"
            )

        model = ChatOpenAI(
            stream_usage=True,
            model=model_config["model"],
            api_key=model_config["api_key"],
            base_url=model_config["base_url"],
        )
        cls._model_cache.set(cache_key, model)
        return model

    @classmethod
    async def get_tool_invocation_model(
        cls, user_id: str = None, **kwargs
    ) -> BaseChatModel:
        return await cls._get_or_create_chat_model(user_id, "tool_call")

    @classmethod
    async def get_conversation_model(
        cls, user_id: str = None, **kwargs
    ) -> BaseChatModel:
        return await cls._get_or_create_chat_model(user_id, "conversation")

    @classmethod
    async def get_reasoning_model(cls, user_id: str = None) -> ReasoningModel:
        cache_key = f"model:{user_id}:reasoning"
        cached = cls._model_cache.get(cache_key)
        if cached is not None:
            return cached

        model_config = await cls._get_model_config(user_id, "reasoning")
        if not model_config:
            raise ValueError(
                f"User {user_id} has no reasoning model configuration in database"
            )

        model = ReasoningModel(
            model_name=model_config["model"],
            api_key=model_config["api_key"],
            base_url=model_config["base_url"],
        )
        cls._model_cache.set(cache_key, model)
        return model

    @classmethod
    async def get_mind_intent_model(
        cls, user_id: str = None, **kwargs
    ) -> BaseChatModel:
        return await cls._get_or_create_chat_model(user_id, "tool_call")

    @classmethod
    def get_user_model(cls, **kwargs) -> BaseChatModel:
        return ChatOpenAI(
            stream_usage=True,
            model=kwargs.get("model"),
            api_key=kwargs.get("api_key"),
            base_url=kwargs.get("base_url"),
        )
