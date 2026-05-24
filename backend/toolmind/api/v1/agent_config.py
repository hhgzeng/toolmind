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
            config_dict = config.to_dict()
            # 校验绑定的 llm 是否实际存在于 llm 表中，若不存在则置为 None
            from toolmind.database.dao import LLMDao
            for key in ["conversation_model_id", "tool_call_model_id", "reasoning_model_id"]:
                llm_id = config_dict.get(key)
                if llm_id:
                    llm_record = await LLMDao.get_llm_by_id(llm_id)
                    if not llm_record:
                        config_dict[key] = None
            return resp_200(data=config_dict)
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
