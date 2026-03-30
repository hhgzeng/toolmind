"""
模型管理器
"""

from typing import Optional

from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI
from toolmind.database.dao import AgentConfigDao, LLMDao


class ModelManager:

    @classmethod
    async def _get_model_config(cls, user_id: str, config_type: str) -> Optional[dict]:
        """获取模型配置"""
        user_config = await AgentConfigDao.get_config_by_user_id(user_id)
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
        return result

    @classmethod
    async def _get_or_create_chat_model(
        cls, user_id: str, config_type: str
    ) -> BaseChatModel:
        """获取 ChatOpenAI 实例"""

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
    async def get_reasoning_model(cls, user_id: str = None, **kwargs) -> BaseChatModel:
        return await cls._get_or_create_chat_model(user_id, "reasoning")

    @classmethod
    async def get_agent_intent_model(
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
