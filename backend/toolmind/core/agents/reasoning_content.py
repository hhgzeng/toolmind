"""
Compatibility helpers for OpenAI-compatible thinking models.

Some providers require assistant ``reasoning_content`` to be sent back on the
next request. langchain-openai 1.0.2 drops that provider-specific field when
converting between raw OpenAI payloads and LangChain messages, so tool-call
loops can fail on their second model call.
"""

from __future__ import annotations

from typing import Any, Mapping

from langchain_core.messages import AIMessage, BaseMessage
from langchain_openai.chat_models import base as openai_chat_base


_PATCHED = False


def _extract_reasoning_content(source: Any) -> Any:
    """Return provider reasoning content from common LangChain/OpenAI shapes."""
    if isinstance(source, Mapping):
        if source.get("reasoning_content") is not None:
            return source["reasoning_content"]

    value = getattr(source, "reasoning_content", None)
    if value is not None:
        return value

    model_extra = getattr(source, "model_extra", None)
    if isinstance(model_extra, Mapping):
        return model_extra.get("reasoning_content")

    return None


def patch_langchain_openai_reasoning_content() -> None:
    """Preserve ``reasoning_content`` across LangChain message round-trips."""
    global _PATCHED
    if _PATCHED:
        return

    original_dict_to_message = openai_chat_base._convert_dict_to_message
    original_message_to_dict = openai_chat_base._convert_message_to_dict

    def _convert_dict_to_message_with_reasoning(
        _dict: Mapping[str, Any],
    ) -> BaseMessage:
        message = original_dict_to_message(_dict)
        reasoning_content = _extract_reasoning_content(_dict)
        if (
            isinstance(message, AIMessage)
            and reasoning_content is not None
            and "reasoning_content" not in message.additional_kwargs
        ):
            message.additional_kwargs["reasoning_content"] = reasoning_content
        return message

    def _convert_message_to_dict_with_reasoning(
        message: BaseMessage,
        api: str = "chat/completions",
    ) -> dict:
        message_dict = original_message_to_dict(message, api=api)
        if isinstance(message, AIMessage):
            reasoning_content = _extract_reasoning_content(message.additional_kwargs)
            if reasoning_content is None:
                reasoning_content = _extract_reasoning_content(message)
            if reasoning_content is not None:
                message_dict["reasoning_content"] = reasoning_content
        return message_dict

    openai_chat_base._convert_dict_to_message = _convert_dict_to_message_with_reasoning
    openai_chat_base._convert_message_to_dict = _convert_message_to_dict_with_reasoning
    _PATCHED = True
