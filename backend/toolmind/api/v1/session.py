from fastapi import APIRouter, Body, Depends, HTTPException
from toolmind.api.services.session import SessionService
from toolmind.api.services.user import UserPayload, get_login_user
from toolmind.schema.schemas import resp_200

router = APIRouter(tags=["Session"])


@router.get("/sessions", summary="获取所有会话列表")
async def get_sessions(login_user: UserPayload = Depends(get_login_user)):
    results = await SessionService.get_sessions(login_user.user_id)
    return resp_200(data=results)


@router.post("/sessions", summary="创建会话")
async def create_session(
    *,
    title: str = "",
    contexts: dict = {},
    login_user: UserPayload = Depends(get_login_user),
):
    # TODO: 后端创建会话逻辑待补齐
    pass


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
