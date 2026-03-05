import json
from typing import List, Dict, Any, Union, Optional

from langchain_core.messages import (
    BaseMessage,
    ChatMessage,
    HumanMessage,
    AIMessage,
    FunctionMessage,
    ToolMessage,
    SystemMessage,
    ToolCall,
)
from openai import AsyncOpenAI
from openai.types.chat import ChatCompletionMessageToolCall
from openai.types.chat.chat_completion_message_tool_call import Function


class ReasoningModel:
    def __init__(self, base_url: str, api_key: str, model_name: str):
        self.model_name = model_name
        self.client = AsyncOpenAI(base_url=base_url, api_key=api_key)
        self._tools: Optional[list] = None

    def bind_tools(self, tools: Union[dict, list]) -> "ReasoningModel":
        """绑定工具定义，返回 self 以支持链式调用。"""
        self._tools = tools if tools else None
        return self

    async def ainvoke(
        self, input: List[BaseMessage], config: Optional[dict] = None
    ) -> AIMessage:
        """
        调用推理模型 API，将响应转为 LangChain AIMessage。
        支持工具调用：如果绑定了 tools 则传入 API。
        正确保留 reasoning_content 到 additional_kwargs 中，
        以便后续多轮对话时 convert_message_to_dict 能将其序列化回请求体。
        """
        user_messages = [self.convert_message_to_dict(msg) for msg in input]

        kwargs: Dict[str, Any] = {
            "model": self.model_name,
            "messages": user_messages,
        }
        if self._tools:
            kwargs["tools"] = self._tools

        response = await self.client.chat.completions.create(**kwargs)
        choice = response.choices[0]
        message = choice.message

        # 构建 tool_calls
        tool_calls = []
        if message.tool_calls:
            for tc in message.tool_calls:
                try:
                    args = json.loads(tc.function.arguments)
                except (json.JSONDecodeError, TypeError):
                    args = {}
                tool_calls.append(
                    ToolCall(name=tc.function.name, args=args, id=tc.id)
                )

        # 保留 reasoning_content 到 additional_kwargs
        additional_kwargs: Dict[str, Any] = {}
        reasoning_content = getattr(message, "reasoning_content", None)
        if reasoning_content is not None:
            additional_kwargs["reasoning_content"] = reasoning_content

        ai_message = AIMessage(
            content=message.content or "",
            tool_calls=tool_calls,
            additional_kwargs=additional_kwargs,
        )

        # 触发 usage_metadata 回调（如果有配置）
        if config and "callbacks" in config:
            usage = response.usage
            if usage:
                ai_message.usage_metadata = {
                    "input_tokens": usage.prompt_tokens,
                    "output_tokens": usage.completion_tokens,
                    "total_tokens": usage.total_tokens,
                }
                for callback in config["callbacks"]:
                    if hasattr(callback, "record_token_usage"):
                        callback.record_token_usage(
                            self.model_name, ai_message.usage_metadata
                        )

        return ai_message

    async def astream(self, messages: List[BaseMessage]):
        user_messages = [self.convert_message_to_dict(message) for message in messages]

        response = await self.client.chat.completions.create(
            model=self.model_name, messages=user_messages, stream=True
        )
        return response

    def convert_message_to_dict(self, message: BaseMessage) -> dict:
        """Convert a message to a dictionary that can be passed to the API."""
        message_dict: Dict[str, Any]
        if isinstance(message, ChatMessage):
            message_dict = {"role": message.role, "content": message.content}
        elif isinstance(message, HumanMessage):
            message_dict = {"role": "user", "content": message.content}
        elif isinstance(message, SystemMessage):
            message_dict = {"role": "user", "content": message.content}
        elif isinstance(message, AIMessage):
            message_dict = {"role": "assistant", "content": message.content}
            # DeepSeek Reasoner 要求多轮对话中 assistant 消息携带 reasoning_content
            reasoning_content = message.additional_kwargs.get("reasoning_content")
            if reasoning_content is not None:
                message_dict["reasoning_content"] = reasoning_content
            if message.tool_calls:
                message_dict["tool_calls"] = self.convert_openai_tool_calls(
                    message.tool_calls
                )
        elif isinstance(message, (FunctionMessage, ToolMessage)):
            message_dict = {
                "role": "tool",
                "content": self._create_tool_content(message.content),
                "name": message.name or message.additional_kwargs.get("name"),
                "tool_call_id": message.tool_call_id,
            }
        else:
            raise TypeError(f"Got unknown type {message}")

        return message_dict

    # 将 Langchain 的格式转为 OpenAI 的格式适配
    def convert_openai_tool_calls(self, tool_calls: List[ToolCall]):
        openai_tool_calls: List[ChatCompletionMessageToolCall] = []

        for tool_call in tool_calls:
            openai_tool_calls.append(
                ChatCompletionMessageToolCall(
                    id=tool_call["id"],
                    type="function",
                    function=Function(
                        arguments=json.dumps(tool_call["args"]),
                        name=tool_call["name"],
                    ),
                )
            )

        return openai_tool_calls

    def _create_tool_content(
        self, content: Union[str, List[Union[str, Dict[Any, Any]]]]
    ) -> str:
        """Convert tool content to dict scheme."""
        if isinstance(content, str):
            try:
                if isinstance(json.loads(content), dict):
                    return content
                else:
                    return json.dumps({"tool_result": content})
            except json.JSONDecodeError:
                return json.dumps({"tool_result": content})
        else:
            return json.dumps({"tool_result": content})