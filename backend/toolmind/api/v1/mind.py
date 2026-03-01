import json
from fastapi import APIRouter, Depends
from starlette.responses import StreamingResponse

from toolmind.api.services.user import UserPayload, get_login_user
from toolmind.schema.mind import MindGuidePrompt, MindGuidePromptFeedBack, MindTask
from toolmind.schema.usage_stats import UsageStatsAgentType
from toolmind.services.mind.agent import MindAgent
from toolmind.utils.contexts import set_user_id_context, set_agent_name_context

router = APIRouter(prefix="/workspace/mind", tags=["Mind"])


@router.post("/guide_prompt", summary="生成 Mind 的指导提示")
async def generate_mind_guide_prompt(*,
                                         mind_info: MindGuidePrompt,
                                         login_user: UserPayload = Depends(get_login_user)):
    # 设置全局变量统计调用
    set_user_id_context(login_user.user_id)
    set_agent_name_context(UsageStatsAgentType.mind_agent)

    mind_agent = MindAgent(login_user.user_id)

    async def general_generate():
        async for chunk in mind_agent.generate_guide_prompt(mind_info):
            yield f"data: {json.dumps(chunk)}\n\n"

    return StreamingResponse(general_generate(), media_type="text/event-stream")


@router.post("/guide_prompt/feedback", summary="根据用户的反馈进行重新生成")
async def rebuild_generate_mind_guide_prompt(*,
                                                 feedback_guide_prompt: MindGuidePromptFeedBack,
                                                 login_user: UserPayload = Depends(get_login_user)):
    # 设置全局变量统计调用
    set_user_id_context(login_user.user_id)
    set_agent_name_context(UsageStatsAgentType.mind_agent)

    mind_agent = MindAgent(login_user.user_id)

    async def general_generate():
        async for chunk in mind_agent.generate_guide_prompt(feedback_guide_prompt, True):
            yield f"data: {json.dumps(chunk)}\n\n"

    return StreamingResponse(general_generate(), media_type="text/event-stream")


@router.post("/task", summary="Mind 生成的任务列表")
async def generate_mind_tasks(*,
                                  task: MindTask,
                                  login_user: UserPayload = Depends(get_login_user)):
    mind_agent = MindAgent(login_user.user_id)

    async def general_generate():
        async for chunk in mind_agent.generate_tasks(task):
            yield chunk

    return StreamingResponse(general_generate(), media_type="text/event-stream")


@router.post("/task_start", summary="Mind 开始执行任务")
async def submit_mind_task(*,
                            task: MindTask,
                            login_user: UserPayload = Depends(get_login_user)):
    # 设置全局变量统计调用
    set_user_id_context(login_user.user_id)
    set_agent_name_context(UsageStatsAgentType.mind_agent)

    mind_agent = MindAgent(login_user.user_id)

    async def general_generate():
        async for chunk in mind_agent.submit_mind_task(task):
            yield f"data: {json.dumps(chunk)}\n\n"
    return StreamingResponse(general_generate(), media_type="text/event-stream")
