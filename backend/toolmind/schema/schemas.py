from typing import Any, Generic, TypeVar, Union

from pydantic import BaseModel
from sqlmodel import Field

# 创建泛型变量
DataT = TypeVar("DataT")


class CreateUserReq(BaseModel):
    user_name: str = Field(max_length=20, description="创建用户时的名称")
    password: str = Field(description="创建用户时的密码")


class UpdateUserPasswordReq(BaseModel):
    user_id: str = Field(description="用户ID")
    new_password: str = Field(description="新密码")


class UpdateUserRoleReq(BaseModel):
    user_id: str = Field(description="用户ID")
    role: str = Field(description="角色分配（admin 或 user）")


class ToggleUserStatusReq(BaseModel):
    user_id: str = Field(description="用户ID")
    enable: bool = Field(description="是否解禁")


class UnifiedResponseModel(BaseModel, Generic[DataT]):
    """统一响应模型"""

    status_code: int
    status_message: str
    data: DataT = None


def resp_200(
    data: Union[list, dict, str, Any] = None, message: str = "SUCCESS"
) -> UnifiedResponseModel:
    """成功的代码"""
    return UnifiedResponseModel(status_code=200, status_message=message, data=data)


def resp_500(
    code: int = 500,
    data: Union[list, dict, str, Any] = None,
    message: str = "BAD REQUEST",
) -> UnifiedResponseModel:
    """错误的逻辑回复"""
    return UnifiedResponseModel(status_code=code, status_message=message, data=data)
