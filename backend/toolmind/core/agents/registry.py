import asyncio
from loguru import logger


class AgentRegistry:
    def __init__(self):
        self.tasks = {}

    def register(self, session_id: str, task: asyncio.Task):
        self.tasks[session_id] = task

    def cancel(self, session_id: str):
        task = self.tasks.get(session_id)
        if task:
            logger.info(f"Cancelling agent task for session {session_id}")
            task.cancel()

    def unregister(self, session_id: str):
        self.tasks.pop(session_id, None)


agent_registry = AgentRegistry()
