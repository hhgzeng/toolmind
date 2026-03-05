from fastapi import APIRouter, Depends
from pydantic import BaseModel

from toolmind.api.services.user import UserPayload, get_login_user
from toolmind.schema.schemas import resp_200, resp_500
from toolmind.settings import app_settings
from toolmind.database.dao.web_search_config import WebSearchConfigDao


router = APIRouter(prefix="/tools", tags=["Tools Config"])


class WebSearchConfigReq(BaseModel):
    api_key: str
    enabled: bool = True


@router.get("/web_search", summary="获取联网搜索配置")
async def get_web_search_config(login_user: UserPayload = Depends(get_login_user)):
    try:
        user_config = await WebSearchConfigDao.get_config_by_user_id(login_user.user_id)
        if user_config:
            return resp_200(data={"api_key": user_config.api_key, "enabled": user_config.enabled})
        
        return resp_200(data={"api_key": "", "enabled": True})
    except Exception as e:
        return resp_500(message=str(e))


@router.post("/web_search", summary="更新联网搜索配置")
async def update_web_search_config(req: WebSearchConfigReq, login_user: UserPayload = Depends(get_login_user)):
    try:
        await WebSearchConfigDao.upsert_config(
            user_id=login_user.user_id,
            api_key=req.api_key,
            enabled=req.enabled
        )

        return resp_200(data={"api_key": req.api_key, "enabled": req.enabled})
    except Exception as e:
        return resp_500(message=str(e))

