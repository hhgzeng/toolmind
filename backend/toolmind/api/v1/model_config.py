from fastapi import APIRouter, Depends
from toolmind.api.services.user import UserPayload, get_login_user
from toolmind.schema.schemas import resp_200, resp_500
from toolmind.database.dao.mind_config import MindModelConfigDao

from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/model", tags=["Model Config"])

class MindConfigReq(BaseModel):
    conversation_model_id: Optional[str] = None
    tool_call_model_id: Optional[str] = None
    reasoning_model_id: Optional[str] = None

@router.get("/mind_config", summary="获取用户的 Mind 模型配置")
async def get_mind_config(login_user: UserPayload = Depends(get_login_user)):
    try:
        config = await MindModelConfigDao.get_config_by_user_id(login_user.user_id)
        if config:
            return resp_200(data=config.to_dict())
        return resp_200(data={})
    except Exception as e:
        return resp_500(message=str(e))

@router.post("/mind_config", summary="更新用户的 Mind 模型配置")
async def update_mind_config(req: MindConfigReq, login_user: UserPayload = Depends(get_login_user)):
    try:
        config = await MindModelConfigDao.upsert_config(
            user_id=login_user.user_id,
            conversation_model_id=req.conversation_model_id,
            tool_call_model_id=req.tool_call_model_id,
            reasoning_model_id=req.reasoning_model_id
        )
        return resp_200(data=config.to_dict())
    except Exception as e:
        return resp_500(message=str(e))
