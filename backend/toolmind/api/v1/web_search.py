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
    from tavily import TavilyClient
    from tavily.errors import MissingAPIKeyError, InvalidAPIKeyError, UsageLimitExceededError

    error_msg = None
    # 仅当传了 api_key 时才测试
    if req.api_key:
        try:
            tavily_client = TavilyClient(api_key=req.api_key)
            tavily_client.search(query="test", max_results=1)
        except MissingAPIKeyError:
            error_msg = "Tavily API Key 为空"
            req.enabled = False
        except InvalidAPIKeyError:
            error_msg = "Tavily API Key 无效"
            req.enabled = False
        except UsageLimitExceededError:
            error_msg = "Tavily API Key 额度已达上限"
            req.enabled = False
        except Exception as e:
            error_msg = f"Tavily API Key 验证失败: {e}"
            req.enabled = False

    try:
        await WebSearchDao.upsert_config(
            user_id=login_user.user_id, api_key=req.api_key, enabled=req.enabled
        )

        if error_msg:
            return resp_500(message=error_msg)
            
        return resp_200(data={"api_key": req.api_key, "enabled": req.enabled})
    except Exception as e:
        return resp_500(message=str(e))
