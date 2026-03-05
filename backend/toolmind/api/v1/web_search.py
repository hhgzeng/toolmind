from pathlib import Path

import yaml
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from toolmind.api.services.user import UserPayload, get_login_user
from toolmind.schema.schemas import resp_200, resp_500
from toolmind.settings import app_settings


router = APIRouter(prefix="/tools", tags=["Tools Config"])


class WebSearchConfigReq(BaseModel):
    api_key: str
    enabled: bool = True


CONFIG_PATH = Path(__file__).resolve().parents[2] / "config.yaml"


def _update_web_search_api_key_in_yaml(api_key: str, enabled: bool) -> None:
    """
    更新后端配置文件中的联网搜索 API Key。
    """
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(f"Config file not found: {CONFIG_PATH}")

    with CONFIG_PATH.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    tools = data.setdefault("tools", {})
    tavily = tools.setdefault("tavily", {})
    tavily["api_key"] = api_key
    tavily["enabled"] = enabled

    with CONFIG_PATH.open("w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, allow_unicode=True)


@router.get("/web_search", summary="获取联网搜索配置")
async def get_web_search_config(login_user: UserPayload = Depends(get_login_user)):
    try:
        api_key = ""
        enabled = True
        if getattr(app_settings, "tools", None) and getattr(
            app_settings.tools, "tavily", None
        ):
            api_key = app_settings.tools.tavily.get("api_key") or ""
            enabled = app_settings.tools.tavily.get("enabled", True)

        return resp_200(data={"api_key": api_key, "enabled": enabled})
    except Exception as e:
        return resp_500(message=str(e))


@router.post("/web_search", summary="更新联网搜索配置")
async def update_web_search_config(req: WebSearchConfigReq, login_user: UserPayload = Depends(get_login_user)):
    try:
        # 更新内存中的配置
        if not getattr(app_settings, "tools", None):
            raise RuntimeError("app_settings.tools is not initialized")

        if not getattr(app_settings.tools, "tavily", None):
            setattr(app_settings.tools, "tavily", {})

        app_settings.tools.tavily["api_key"] = req.api_key
        app_settings.tools.tavily["enabled"] = req.enabled

        # 同步更新到配置文件
        _update_web_search_api_key_in_yaml(req.api_key, req.enabled)

        return resp_200(data={"api_key": req.api_key, "enabled": req.enabled})
    except Exception as e:
        return resp_500(message=str(e))

