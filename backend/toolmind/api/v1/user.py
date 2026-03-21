from typing import Optional

from fastapi import APIRouter, Body, Depends, HTTPException
from fastapi_jwt_auth import AuthJWT
from loguru import logger
from toolmind.api.errcode.user import UserValidateError
from toolmind.api.services.redis import redis_client
from toolmind.api.services.user import UserService, get_user_jwt
from toolmind.database.dao.user import UserDao
from toolmind.database.models.user import AdminUser
from toolmind.schema.schemas import UnifiedResponseModel, resp_200
from toolmind.utils.constants import USER_CURRENT_SESSION
from toolmind.api.JWT import ACCESS_TOKEN_EXPIRE_TIME

router = APIRouter(tags=["User"])


@router.post("/user/register", response_model=UnifiedResponseModel)
async def register(
    user_name: str = Body(description="用户名"),
    user_password: str = Body(description="用户密码"),
):

    exist_user = UserDao.get_user_by_username(user_name)
    if exist_user:
        raise HTTPException(status_code=500, detail="用户名重复")
    if len(user_name) > 20:
        raise HTTPException(status_code=500, detail="用户名长度不应该超过20")
    try:
        user_password = UserService.encrypt_sha256_password(user_password)
        admin = UserDao.get_user(AdminUser)

        if admin:
            UserDao.add_user_and_default_role(user_name, user_password)
        else:
            user_id = AdminUser
            UserDao.add_user_and_admin_role(user_id, user_name, user_password)
    except Exception as e:
        logger.error(f"register user is appear error: {e}")
        raise HTTPException(
            status_code=500, detail=f"register user is appear error: {e}"
        )
    return resp_200()


@router.post("/user/login", response_model=UnifiedResponseModel)
async def login(
    user_name: str = Body(description="用户名"),
    user_password: str = Body(description="用户密码"),
    Authorize: AuthJWT = Depends(),
):

    db_user = UserDao.get_user_by_username(user_name)
    # 检查密码
    if not db_user or not UserService.verify_password(
        user_password, db_user.user_password
    ):
        return UserValidateError.return_resp()

    if db_user.delete:
        raise HTTPException(status_code=500, detail="该账号已被禁用，请联系管理员")

    access_token, refresh_token, role = get_user_jwt(db_user)

    # Set the JWT cookies in the response
    Authorize.set_access_cookies(access_token)
    Authorize.set_refresh_cookies(refresh_token)

    # 设置登录用户当前的cookie, 比jwt有效期多一个小时
    redis_client.set(
        USER_CURRENT_SESSION.format(db_user.user_id),
        access_token,
        ACCESS_TOKEN_EXPIRE_TIME + 3600,
    )

    return resp_200(
        data={"user_id": db_user.user_id, "access_token": access_token, "role": role}
    )


@router.get("/user/info", response_model=UnifiedResponseModel)
async def get_user_info(user_id: str):
    result = UserService.get_user_info_by_id(user_id)

    return resp_200(result)


from toolmind.api.services.user import UserPayload, get_login_user
from toolmind.api.services.user_management import UserManagementService
from toolmind.schema.schemas import (
    ToggleUserStatusReq,
    UpdateUserPasswordReq,
    UpdateUserRoleReq,
    resp_500,
)


def require_admin(user: UserPayload = Depends(get_login_user)):
    """验证当前用户是否是管理员"""
    if not user.is_admin():
        raise HTTPException(status_code=403, detail="需要管理员权限")
    return user


@router.get("/user/list", response_model=UnifiedResponseModel)
async def get_user_list(
    page: int = 1, limit: int = 20, admin_user: UserPayload = Depends(require_admin)
):
    """管理员获取用户列表"""
    data = UserManagementService.get_user_list(page, limit)
    return resp_200(data)


@router.post("/user/reset_password", response_model=UnifiedResponseModel)
async def reset_user_password(
    req: UpdateUserPasswordReq, admin_user: UserPayload = Depends(require_admin)
):
    """管理员修改任意用户密码"""
    return UserManagementService.update_user_password(req.user_id, req.new_password)


@router.post("/user/role", response_model=UnifiedResponseModel)
async def update_user_role(
    req: UpdateUserRoleReq, admin_user: UserPayload = Depends(require_admin)
):
    """分配或取消管理员角色"""
    if req.user_id == admin_user.user_id:
        return resp_500(message="你不能修改你自己的角色")

    return UserManagementService.update_user_role(req.user_id, req.role)


@router.post("/user/toggle_status", response_model=UnifiedResponseModel)
async def toggle_user_status(
    req: ToggleUserStatusReq, admin_user: UserPayload = Depends(require_admin)
):
    """启用或禁用应用层账号"""
    if req.user_id == admin_user.user_id:
        return resp_500(message="你不能禁用你自己的账号")

    return UserManagementService.toggle_user_status(req.user_id, req.enable)
