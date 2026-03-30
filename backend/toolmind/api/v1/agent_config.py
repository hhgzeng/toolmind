from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from toolmind.api.services import UserPayload, get_login_user
from toolmind.database.dao import AgentConfigDao
from toolmind.schema import resp_200, resp_500

router = APIRouter(tags=["Agent Config"])


class AgentConfigReq(BaseModel):
    conversation_model_id: Optional[str] = None
    tool_call_model_id: Optional[str] = None
    reasoning_model_id: Optional[str] = None


@router.get("/agent-config", summary="获取用户的 Agent 模型配置")
async def get_agent_config(login_user: UserPayload = Depends(get_login_user)):
    try:
        config = await AgentConfigDao.get_config_by_user_id(login_user.user_id)
        if config:
            return resp_200(data=config.to_dict())
        return resp_200(data={})
    except Exception as e:
        return resp_500(message=str(e))


@router.put("/agent-config", summary="更新用户的 Agent 模型配置")
async def update_agent_config(
    req: AgentConfigReq, login_user: UserPayload = Depends(get_login_user)
):
    try:
        config = await AgentConfigDao.upsert_config(
            user_id=login_user.user_id,
            conversation_model_id=req.conversation_model_id,
            tool_call_model_id=req.tool_call_model_id,
            reasoning_model_id=req.reasoning_model_id,
        )
        return resp_200(data=config.to_dict())
    except Exception as e:
        return resp_500(message=str(e))
