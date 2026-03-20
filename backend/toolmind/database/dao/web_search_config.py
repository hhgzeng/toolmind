from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from toolmind.database import async_engine
from toolmind.database.models.web_search_config import WebSearchConfigTable


class WebSearchConfigDao:
    @classmethod
    async def get_config_by_user_id(cls, user_id: str) -> WebSearchConfigTable:
        async with AsyncSession(async_engine) as session:
            statement = select(WebSearchConfigTable).where(
                WebSearchConfigTable.user_id == user_id
            )
            result = await session.exec(statement)
            return result.first()

    @classmethod
    async def upsert_config(cls, user_id: str, api_key: str, enabled: bool):
        async with AsyncSession(async_engine) as session:
            statement = select(WebSearchConfigTable).where(
                WebSearchConfigTable.user_id == user_id
            )
            result = await session.exec(statement)
            config = result.first()
            if config:
                if api_key is not None:
                    config.api_key = api_key
                if enabled is not None:
                    config.enabled = enabled
                session.add(config)
            else:
                config = WebSearchConfigTable(
                    user_id=user_id,
                    api_key=api_key if api_key is not None else "",
                    enabled=enabled if enabled is not None else True,
                )
                session.add(config)
            await session.commit()
            return config
