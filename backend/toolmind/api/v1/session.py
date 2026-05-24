import asyncio
import json

from fastapi import APIRouter, Body, Depends, Request, HTTPException
from starlette.responses import StreamingResponse
from toolmind.api.services import SessionService, UserPayload, get_login_user
from toolmind.core.agents import Agent
from toolmind.core.agents.registry import agent_registry
from toolmind.schema import AgentTask, resp_200
from toolmind.utils import set_user_id_context

router = APIRouter(tags=["Session"])


@router.get("/sessions", summary="获取所有会话列表")
async def get_sessions(login_user: UserPayload = Depends(get_login_user)):
    results = await SessionService.get_sessions(login_user.user_id)
    return resp_200(data=results)


@router.post("/sessions", summary="创建会话并开始执行 Agent 任务")
async def create_session(
    *, task: AgentTask, login_user: UserPayload = Depends(get_login_user)
):
    # 设置全局变量统计调用
    set_user_id_context(login_user.user_id)

    # 检查模型是否配置
    from toolmind.core.agents.model import ModelManager
    try:
        await ModelManager.get_conversation_model(login_user.user_id)
        await ModelManager.get_tool_invocation_model(login_user.user_id)
        await ModelManager.get_reasoning_model(login_user.user_id)
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail="模型配置缺失，请先在“设置 -> 模型配置”中配置 Agent 模型后再发送消息"
        )

    agent_instance = Agent(login_user.user_id)

    async def general_generate():
        current_task = asyncio.current_task()
        session_id = None
        try:
            async for chunk in agent_instance.submit_agent_task(task):
                if chunk.get("event") == "session_started":
                    session_id = chunk["data"]["session_id"]
                    agent_registry.register(session_id, current_task)
                yield f"data: {json.dumps(chunk)}\n\n"
        except asyncio.CancelledError:
            pass
        finally:
            if session_id:
                agent_registry.unregister(session_id)

    return StreamingResponse(general_generate(), media_type="text/event-stream")


@router.get("/sessions/{session_id}", summary="进入会话")
async def session_info(
    session_id: str,
    login_user: UserPayload = Depends(get_login_user),
):
    try:
        result = await SessionService.get_session_from_id(
            session_id, login_user.user_id
        )
        return resp_200(data=result)
    except Exception as err:
        raise HTTPException(status_code=500, detail=str(err))


@router.delete("/sessions/{session_id}", summary="删除会话")
async def delete_session(
    session_id: str,
    login_user: UserPayload = Depends(get_login_user),
):
    try:
        agent_registry.cancel(session_id)
        await SessionService.delete_session([session_id], login_user.user_id)
        return resp_200()
    except Exception as err:
        raise HTTPException(status_code=500, detail=str(err))


@router.patch("/sessions/{session_id}", summary="更新会话")
async def update_session(
    session_id: str,
    data: dict = Body(...),
    login_user: UserPayload = Depends(get_login_user),
):
    try:
        title = data.get("title")
        is_pinned = data.get("is_pinned")
        result = await SessionService.update_session(
            session_id, login_user.user_id, title, is_pinned
        )
        if not result:
            raise HTTPException(status_code=404, detail="Session not found")
        return resp_200(data=result.to_dict())
    except Exception as err:
        raise HTTPException(status_code=500, detail=str(err))
