from typing import List

from sqlmodel import select, and_, delete

from toolmind.database.models.session import Session
from toolmind.database.session import async_session_getter


class SessionDao:
    @classmethod
    async def get_sessions(cls, user_id):
        async with async_session_getter() as session:
            statement = select(Session).where(Session.user_id == user_id)
            result = await session.exec(statement)
            return result.all()

    @classmethod
    async def create_session(cls, session_model: Session):
        async with async_session_getter() as session:
            if not session_model.session_id:
                from uuid import uuid4

                session_model.session_id = uuid4().hex
            session.add(session_model)
            await session.commit()
            await session.refresh(session_model)
        return session_model

    @classmethod
    async def delete_session(cls, session_ids: List[str], user_id):
        async with async_session_getter() as session:
            statement = delete(Session).where(
                and_(Session.session_id.in_(session_ids), Session.user_id == user_id)
            )
            await session.exec(statement)
            await session.commit()

    @classmethod
    async def update_session_contexts(cls, session_id, session_context):
        async with async_session_getter() as session:
            session_model = await session.get(Session, session_id)
            new_contexts = session_model.contexts.copy()
            new_contexts.append(session_context)
            session_model.contexts = new_contexts

            await session.commit()
            await session.refresh(session_model)
        return session_model

    @classmethod
    async def update_session(cls, session_id, user_id, title=None, is_pinned=None):
        async with async_session_getter() as session:
            statement = select(Session).where(
                and_(Session.session_id == session_id, Session.user_id == user_id)
            )
            result = await session.exec(statement)
            session_model = result.first()
            if not session_model:
                return None

            if title is not None:
                session_model.title = title
            if is_pinned is not None:
                session_model.is_pinned = is_pinned

            await session.commit()
            await session.refresh(session_model)
        return session_model

    @classmethod
    async def get_session_from_id(cls, session_id):
        async with async_session_getter() as session:
            return await session.get(Session, session_id)

    @classmethod
    async def clear_session_contexts(cls, session_id):
        async with async_session_getter() as session:
            session_model = await session.get(Session, session_id)
            session_model.contexts = []

            await session.commit()
            await session.refresh(session_model)
        return session_model

