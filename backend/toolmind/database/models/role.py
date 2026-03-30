from datetime import datetime
from typing import Optional

from sqlalchemy import Column, DateTime, UniqueConstraint, text
from sqlmodel import Field, SQLModel

# 默认普通用户角色的ID
DefaultRole = "2"
# 超级管理员角色ID
AdminRole = "1"


class RoleBase(SQLModel):
    role_name: str = Field(index=False, description="前端展示名称")
    remark: Optional[str] = Field(index=False)
    group_id: int = Field(index=True, description="所属分组ID")
    create_time: Optional[datetime] = Field(
        sa_column=Column(
            DateTime,
            nullable=False,
            index=True,
            server_default=text("CURRENT_TIMESTAMP"),
        )
    )
    update_time: Optional[datetime] = Field(
        sa_column=Column(
            DateTime,
            nullable=False,
            server_default=text("CURRENT_TIMESTAMP"),
            onupdate=text("CURRENT_TIMESTAMP"),
        )
    )


class Role(RoleBase, table=True):
    __table_args__ = (
        UniqueConstraint("role_name", "group_id", name="group_role_name_uniq"),
    )
    id: Optional[int] = Field(default=None, primary_key=True)


class RoleCreate(RoleBase):
    pass


class RoleRead(RoleBase):
    id: Optional[int]


class RoleUpdate(RoleBase):
    role_name: Optional[str]
    remark: Optional[str]
    group_id: Optional[int]
