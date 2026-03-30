from fastapi import APIRouter, Depends
from pydantic import BaseModel
from toolmind.api.services import UserPayload, get_login_user
from toolmind.database.dao import WebSearchDao
from toolmind.schema import resp_200, resp_500

router = APIRouter(prefix="/tools", tags=["Tools Config"])


class WebSearchReq(BaseModel):
    api_key: str
    enabled: bool = True


@router.get("/web-search", summary="获取联网搜索配置")
async def get_web_search_config(login_user: UserPayload = Depends(get_login_user)):
    try:
        user_config = await WebSearchDao.get_config_by_user_id(login_user.user_id)
        if user_config:
            return resp_200(
                data={"api_key": user_config.api_key, "enabled": user_config.enabled}
            )

        return resp_200(data={"api_key": "", "enabled": True})
    except Exception as e:
        return resp_500(message=str(e))


@router.put("/web-search", summary="更新联网搜索配置")
async def update_web_search_config(
    req: WebSearchReq, login_user: UserPayload = Depends(get_login_user)
):
    try:
        await WebSearchDao.upsert_config(
            user_id=login_user.user_id, api_key=req.api_key, enabled=req.enabled
        )

        return resp_200(data={"api_key": req.api_key, "enabled": req.enabled})
    except Exception as e:
        return resp_500(message=str(e))
