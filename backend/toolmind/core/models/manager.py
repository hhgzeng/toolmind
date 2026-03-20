from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI
from toolmind.core.models.reason_model import ReasoningModel
from toolmind.settings import app_settings
from toolmind.database.dao.mind_config import MindModelConfigDao
from toolmind.database.dao.llm import LLMDao
from typing import Optional


class ModelManager:

    @classmethod
    async def _get_model_config(cls, user_id: str, config_type: str) -> Optional[dict]:
        """Helper to fetch model config based on type ('conversation', 'tool_call', 'reasoning')."""
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

        return llm_record.to_dict()

    @classmethod
    async def get_tool_invocation_model(
        cls, user_id: str = None, **kwargs
    ) -> BaseChatModel:
        model_config = await cls._get_model_config(user_id, "tool_call")

        if not model_config:
             raise ValueError(f"User {user_id} has no tool_call model configuration in database")

        return ChatOpenAI(
            stream_usage=True,
            model=model_config["model"],
            api_key=model_config["api_key"],
            base_url=model_config["base_url"],
        )

    @classmethod
    async def get_conversation_model(
        cls, user_id: str = None, **kwargs
    ) -> BaseChatModel:
        model_config = await cls._get_model_config(user_id, "conversation")

        if not model_config:
            raise ValueError(f"User {user_id} has no conversation model configuration in database")

        return ChatOpenAI(
            stream_usage=True,
            model=model_config["model"],
            api_key=model_config["api_key"],
            base_url=model_config["base_url"],
        )

    @classmethod
    async def get_reasoning_model(cls, user_id: str = None) -> ReasoningModel:
        model_config = await cls._get_model_config(user_id, "reasoning")

        if not model_config:
            raise ValueError(f"User {user_id} has no reasoning model configuration in database")

        return ReasoningModel(
            model_name=model_config["model"],
            api_key=model_config["api_key"],
            base_url=model_config["base_url"],
        )

    @classmethod
    async def get_mind_intent_model(
        cls, user_id: str = None, **kwargs
    ) -> BaseChatModel:
        model_config = await cls._get_model_config(user_id, "tool_call")

        if not model_config:
            raise ValueError(f"User {user_id} has no tool_call model configuration in database")

        return ChatOpenAI(
            stream_usage=True,
            model=model_config["model"],
            api_key=model_config["api_key"],
            base_url=model_config["base_url"],
        )

    @classmethod
    def get_user_model(cls, **kwargs) -> BaseChatModel:
        return ChatOpenAI(
            stream_usage=True,
            model=kwargs.get("model"),
            api_key=kwargs.get("api_key"),
            base_url=kwargs.get("base_url"),
        )
