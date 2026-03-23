import json
import os
import re
from datetime import datetime, timedelta, timezone

from loguru import logger


def fix_json_text(text: str):
    """
    Json字符串不允许出现 ' 单引号
    修复Json字符串"""
    return text.replace("'", '"')


def get_cache_key(client_id, chat_id):
    return f"{client_id}_{chat_id}"


def check_or_create(path):
    if os.path.exists(path):
        pass
    else:
        os.makedirs(path)


def init_dir(path):
    try:
        if not os.path.exists(path):
            os.makedirs(path)
    except Exception as err:
        logger.error(f"create dir appear: {err}")





def check_input(user_input):
    # 定义正则表达式，匹配大小写字母、数字
    alphabet_pattern = re.compile(r"^[a-zA-Z0-9]+$")

    # 检查输入是否只包含大小写字母、数字
    if alphabet_pattern.match(user_input):
        return True
    else:
        return False


def filename_to_classname(filename):
    """
    Convert a snake_case filename to a CamelCase class name.

    Args:
    filename (str): The filename in snake_case, without the .py extension.

    Returns:
    str: The converted CamelCase class name.
    """
    parts = filename.split("_")
    class_name = "".join(part.capitalize() for part in parts)
    return class_name


def extract_json_from_string(input_string):
    """
    JSON抽取函数
    返回包含JSON对象的列表
    """
    try:
        # 正则表达式假设JSON对象由花括号括起来
        matches = re.findall(r"\{.*?\}", input_string, re.DOTALL)

        # 验证找到的每个匹配项是否为有效的JSON
        valid_jsons = []
        for match in matches:
            try:
                json_obj = json.loads(match)
                valid_jsons.append(json_obj)
            except json.JSONDecodeError:
                # If not valid JSON, try to fix it
                try:
                    valid_jsons.append(fix_json(match))
                except Exception:
                    continue  # If still not valid JSON, skip this match

        return valid_jsons
    except Exception as e:
        print(f"Error occurred: {e}")
        return []


def fix_json(bad_json):
    # 首先，用双引号替换掉所有的单引号
    fixed_json = bad_json.replace("'", '"')
    try:
        # 然后尝试解析
        return json.loads(fixed_json)
    except json.JSONDecodeError:
        # 如果解析失败，打印错误信息，但不会崩溃
        print("给定的字符串不是有效的 JSON 格式。")
