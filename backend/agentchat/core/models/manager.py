from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI
from agentchat.core.models.tool_call import ToolCallModel
from agentchat.core.models.reason_model import ReasoningModel
from agentchat.settings import app_settings
from agentchat.database.dao.lingseek_config import LingseekModelConfigDao
from agentchat.database.dao.llm import LLMDao
from typing import Optional


class ModelManager:

    @classmethod
    async def _get_model_config(cls, user_id: str, config_type: str) -> Optional[dict]:
        """ Helper to fetch model config based on type ('conversation', 'tool_call', 'reasoning'). """
        user_config = await LingseekModelConfigDao.get_config_by_user_id(user_id)
        if not user_config:
            return None
        
        llm_id = None
        if config_type == 'conversation':
            llm_id = user_config.conversation_model_id
        elif config_type == 'tool_call':
            llm_id = user_config.tool_call_model_id
        elif config_type == 'reasoning':
            llm_id = user_config.reasoning_model_id
            
        if not llm_id:
            return None
            
        llm_record = await LLMDao.get_llm_by_id(llm_id)
        if not llm_record:
            return None
            
        return llm_record.to_dict()

    @classmethod
    async def get_tool_invocation_model(cls, user_id: str = None, **kwargs) -> BaseChatModel:
        model_config = await cls._get_model_config(user_id, 'tool_call')
        
        if model_config:
            return ChatOpenAI(
                stream_usage=True,
                model=model_config['model'],
                api_key=model_config['api_key'],
                base_url=model_config['base_url'])
                
        # Fallback to local config if not set
        return ChatOpenAI(
            stream_usage=True,
            model=app_settings.multi_models.tool_call_model.model_name,
            api_key=app_settings.multi_models.tool_call_model.api_key,
            base_url=app_settings.multi_models.tool_call_model.base_url)

    @classmethod
    async def get_conversation_model(cls, user_id: str = None, **kwargs) -> BaseChatModel:
        model_config = await cls._get_model_config(user_id, 'conversation')
        
        if model_config:
            return ChatOpenAI(
                stream_usage=True,
                model=model_config['model'],
                api_key=model_config['api_key'],
                base_url=model_config['base_url'])
                
        return ChatOpenAI(
            stream_usage=True,
            model=app_settings.multi_models.conversation_model.model_name,
            api_key=app_settings.multi_models.conversation_model.api_key,
            base_url=app_settings.multi_models.conversation_model.base_url)

    @classmethod
    async def get_reasoning_model(cls, user_id: str = None) -> ReasoningModel:
        model_config = await cls._get_model_config(user_id, 'reasoning')
        
        if model_config:
            return ReasoningModel(
                model_name=model_config['model'],
                api_key=model_config['api_key'],
                base_url=model_config['base_url'])
                
        return ReasoningModel(model_name=app_settings.multi_models.reasoning_model.model_name,
                              api_key=app_settings.multi_models.reasoning_model.api_key,
                              base_url=app_settings.multi_models.reasoning_model.base_url)

    @classmethod
    async def get_lingseek_intent_model(cls, user_id: str = None, **kwargs) -> BaseChatModel:
        model_config = await cls._get_model_config(user_id, 'tool_call')
        
        if model_config:
            return ChatOpenAI(
                stream_usage=True,
                model=model_config['model'],
                api_key=model_config['api_key'],
                base_url=model_config['base_url'])
                
        return ChatOpenAI(
            stream_usage=True,
            model=app_settings.multi_models.tool_call_model.model_name,
            api_key=app_settings.multi_models.tool_call_model.api_key,
            base_url=app_settings.multi_models.tool_call_model.base_url)

    @classmethod
    def get_qwen_vl_model(cls) -> BaseChatModel:
        return ChatOpenAI(model=app_settings.multi_models.qwen_vl.model_name,
                          api_key=app_settings.multi_models.qwen_vl.api_key,
                          base_url=app_settings.multi_models.qwen_vl.base_url)

    @classmethod
    def get_user_model(cls, **kwargs) -> BaseChatModel:
        return ChatOpenAI(
            stream_usage=True,
            model=kwargs.get("model"),
            api_key=kwargs.get("api_key"),
            base_url=kwargs.get("base_url"))

