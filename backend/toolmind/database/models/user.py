from datetime import datetime
from typing import Optional

from pydantic import validator
from sqlalchemy import Column, DateTime, text
from sqlmodel import Field
from toolmind.database.models.base import SQLModelSerializable

AdminUser = "1"


class UserTable(SQLModelSerializable, table=True):
    __tablename__ = "user"

    user_id: str = Field(primary_key=True)
    user_name: str = Field(index=True, unique=True)
    user_password: str = Field(description="经过加密后的用户密码")
    delete: bool = Field(default=False, description="该用户是否删除")
    create_time: Optional[datetime] = Field(
        sa_column=Column(
            DateTime,
            nullable=False,
            index=True,
            server_default=text("CURRENT_TIMESTAMP"),
        )
    )

    @validator("user_name")
    def validate_str(v):
        if not v:
            raise ValueError("user_name 不能为空")
        return v
