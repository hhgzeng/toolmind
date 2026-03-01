from toolmind.database import async_engine
from toolmind.database.models.mind_config import MindModelConfigTable
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select

class MindModelConfigDao:
    @classmethod
    async def get_config_by_user_id(cls, user_id: str) -> MindModelConfigTable:
        async with AsyncSession(async_engine) as session:
            statement = select(MindModelConfigTable).where(MindModelConfigTable.user_id == user_id)
            result = await session.exec(statement)
            return result.first()

    @classmethod
    async def upsert_config(cls, user_id: str,
                            conversation_model_id: str = None,
                            tool_call_model_id: str = None,
                            reasoning_model_id: str = None):
        async with AsyncSession(async_engine) as session:
            statement = select(MindModelConfigTable).where(MindModelConfigTable.user_id == user_id)
            result = await session.exec(statement)
            config = result.first()
            if config:
                if conversation_model_id is not None:
                    config.conversation_model_id = conversation_model_id
                if tool_call_model_id is not None:
                    config.tool_call_model_id = tool_call_model_id
                if reasoning_model_id is not None:
                    config.reasoning_model_id = reasoning_model_id
                session.add(config)
            else:
                config = MindModelConfigTable(
                    user_id=user_id,
                    conversation_model_id=conversation_model_id,
                    tool_call_model_id=tool_call_model_id,
                    reasoning_model_id=reasoning_model_id
                )
                session.add(config)
            await session.commit()
            return config
