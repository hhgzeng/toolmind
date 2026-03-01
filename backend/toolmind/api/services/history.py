from typing import List

from langchain_core.messages import BaseMessage, AIMessage, HumanMessage

from toolmind.database.dao.history import HistoryDao

Assistant_Role = "assistant"
User_Role = "user"


class HistoryService:

    @classmethod
    async def create_history(cls, role: str, content: str, events: List[dict], dialog_id: str):
        try:
            await HistoryDao.create_history(role, content, events, dialog_id)
        except Exception as err:
            raise ValueError(f"Add history data appear error: {err}")

    @classmethod
    async def select_history(cls, dialog_id: str, top_k: int = 4) -> List[BaseMessage] | None:
        try:
            result = await HistoryDao.select_history_from_time(dialog_id, top_k)
            messages: List[BaseMessage] = []
            for data in result:
                if data.role == Assistant_Role:
                    messages.append(AIMessage(content=data.content))
                elif data.role == User_Role:
                    messages.append(HumanMessage(content=data.content))
            return messages
        except Exception as err:
            raise ValueError(f"Select history is appear error: {err}")

    @classmethod
    async def get_dialog_history(cls, dialog_id: str):
        try:
            results = await HistoryDao.get_dialog_history(dialog_id)
            return [res.to_dict() for res in results]
        except Exception as err:
            raise ValueError(f"Get dialog history is appear error: {err}")

    @classmethod
    async def save_chat_history(cls, role: str, content: str, events: List[dict], dialog_id: str):
        await cls.create_history(role, content, events, dialog_id)
