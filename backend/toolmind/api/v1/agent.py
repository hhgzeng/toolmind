import json

from fastapi import APIRouter, Depends
from starlette.responses import StreamingResponse
from toolmind.api.services.user import UserPayload, get_login_user
from toolmind.core.agents import Agent
from toolmind.schema.agent import AgentTask
from toolmind.schema.usage_stats import UsageStatsAgentType
from toolmind.utils.contexts import set_agent_name_context, set_user_id_context

router = APIRouter(tags=["Agent"])


@router.post("/agent/tasks", summary="Agent 开始执行任务")
async def submit_agent_task(
    *, task: AgentTask, login_user: UserPayload = Depends(get_login_user)
):
    # 设置全局变量统计调用
    set_user_id_context(login_user.user_id)
    set_agent_name_context(UsageStatsAgentType.agent)

    agent_instance = Agent(login_user.user_id)

    async def general_generate():
        async for chunk in agent_instance.submit_agent_task(task):
            yield f"data: {json.dumps(chunk)}\n\n"

    return StreamingResponse(general_generate(), media_type="text/event-stream")
