from sqlmodel import select
from toolmind.database.session import session_getter
from toolmind.database.models.agent import AgentTable


class AgentDao:

    @classmethod
    async def get_agent_by_id(cls, agent_id: str):
        with session_getter() as session:
            sql = select(AgentTable).where(AgentTable.id == agent_id)
            result = session.exec(sql).first()
            return result
