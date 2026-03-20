from toolmind.database.dao.session import Session, SessionDao
from toolmind.database.models.session import SessionCreate


class SessionService:
    @classmethod
    async def create_session(cls, session_create: SessionCreate):
        session = Session(**session_create.model_dump())
        return await SessionDao.create_session(session)

    @classmethod
    async def get_sessions(cls, user_id):
        results = await SessionDao.get_sessions(user_id)
        results.sort(key=lambda x: x.update_time, reverse=True)
        return [result.to_dict() for result in results]

    @classmethod
    async def delete_session(cls, session_ids, user_id):
        await SessionDao.delete_session(session_ids, user_id)

    @classmethod
    async def update_session_contexts(cls, session_id, session_context):
        return await SessionDao.update_session_contexts(session_id, session_context)

    @classmethod
    async def update_session(cls, session_id, user_id, title=None, is_pinned=None):
        return await SessionDao.update_session(session_id, user_id, title, is_pinned)

    @classmethod
    async def clear_session_contexts(cls, session_id):
        return await SessionDao.clear_session_contexts(session_id)

    @classmethod
    async def get_session_from_id(cls, session_id, user_id):
        result = await SessionDao.get_session_from_id(session_id)
        if result is None:
            return None
        return result.to_dict()

    @classmethod
    async def generate_session_title(cls, user_query):
        pass
