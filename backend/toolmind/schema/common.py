from pydantic import BaseModel, Field


class CreateLLMRequest(BaseModel):
    """
    创建大模型的请求参数模型
    """

    model: str = Field(..., description="大模型的名称")
    api_key: str = Field(..., description="大模型的 API Key")
    base_url: str = Field(..., description="大模型服务的基础 URL")
    provider: str = Field(..., description="大模型提供商，例如 OpenAI、Anthropic")


class UpdateLLMRequest(BaseModel):
    """
    更新大模型的请求参数模型
    """

    model: str = Field(None, description="大模型的名称")
    api_key: str = Field(None, description="大模型的 API Key")
    base_url: str = Field(None, description="大模型服务的基础 URL")
    llm_id: str = Field(..., description="大模型的ID")
    provider: str = Field(None, description="大模型提供商，例如 OpenAI、Anthropic")


class ModelConfig(BaseModel):
    model_name: str = ""
    api_key: str = ""
    base_url: str = ""


class MultiModels(BaseModel):
    class Config:
        extra = "allow"

    reasoning_model: ModelConfig = Field(default_factory=ModelConfig)
    conversation_model: ModelConfig = Field(default_factory=ModelConfig)
    tool_call_model: ModelConfig = Field(default_factory=ModelConfig)


class Tools(BaseModel):
    class Config:
        extra = "allow"

    tavily: dict = Field(default_factory=dict)


