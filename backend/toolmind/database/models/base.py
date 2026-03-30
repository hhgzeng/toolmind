from datetime import datetime
from typing import ClassVar

import orjson
from pydantic import ConfigDict
from sqlmodel import SQLModel


def orjson_dumps(v, *, default=None, sort_keys=False, indent_2=True):
    option = orjson.OPT_SORT_KEYS if sort_keys else None
    if indent_2:
        # orjson 返回 bytes，需解码为字符串以匹配标准 json.dumps
        if option is None:
            option = orjson.OPT_INDENT_2
        else:
            option |= orjson.OPT_INDENT_2
    if default is None:
        return orjson.dumps(v, option=option).decode()
    return orjson.dumps(v, default=default, option=option).decode()


class SQLModelSerializable(SQLModel):
    model_config = ConfigDict(from_attributes=True)

    # ClassVar 标注的类变量不会被视为数据库字段
    hide_fields: ClassVar[list[str]] = []  # 隐藏字段，如 "api_key"

    def to_dict(self):
        result = self.model_dump(exclude=self.hide_fields)
        for column in result:
            value = getattr(self, column)
            if isinstance(value, datetime):
                # 转换 datetime 对象为字符串
                value = value.isoformat()
            result[column] = value
        return result
