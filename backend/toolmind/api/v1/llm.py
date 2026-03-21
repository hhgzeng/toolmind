from typing import Optional

from fastapi import APIRouter, Body, Depends
from loguru import logger
from toolmind.api.services.llm import LLMService
from toolmind.api.services.user import UserPayload, get_login_user
from toolmind.schema.common import CreateLLMRequest, UpdateLLMRequest
from toolmind.schema.schemas import UnifiedResponseModel, resp_200, resp_500

router = APIRouter(tags=["LLM"])


@router.post("/llms", response_model=UnifiedResponseModel)
async def create_llm(
    *,
    llm_request: CreateLLMRequest = Body(),
    login_user: UserPayload = Depends(get_login_user)
):
    try:
        await LLMService.create_llm(
            model=llm_request.model,
            api_key=llm_request.api_key,
            base_url=llm_request.base_url,
            user_id=login_user.user_id,
            provider=llm_request.provider,
        )
        return resp_200()
    except Exception as err:
        logger.error(err)
        return resp_500(message=str(err))


@router.delete("/llms/{llm_id}", response_model=UnifiedResponseModel)
async def delete_llm(
    llm_id: str,
    login_user: UserPayload = Depends(get_login_user),
):
    try:
        # 验证用户权限
        await LLMService.verify_user_permission(llm_id, login_user.user_id)

        await LLMService.delete_llm(llm_id=llm_id)
        return resp_200()
    except Exception as err:
        logger.error(err)
        return resp_500(message=str(err))


@router.put("/llms/{llm_id}", response_model=UnifiedResponseModel)
async def update_llm(
    llm_id: str,
    llm_request: UpdateLLMRequest = Body(),
    login_user: UserPayload = Depends(get_login_user)
):
    try:
        # 验证用户权限
        await LLMService.verify_user_permission(llm_id, login_user.user_id)

        await LLMService.update_llm(
            model=llm_request.model,
            api_key=llm_request.api_key,
            llm_id=llm_id,
            provider=llm_request.provider,
            base_url=llm_request.base_url,
        )

        return resp_200()
    except Exception as err:
        logger.error(err)
        return resp_500(message=str(err))


@router.get("/llms/visible", response_model=UnifiedResponseModel)
async def get_visible_llm(login_user: UserPayload = Depends(get_login_user)):
    try:
        result = await LLMService.get_visible_llm(user_id=login_user.user_id)
        return resp_200(data=result)
    except Exception as err:
        logger.error(err)
        return resp_500(message=str(err))
