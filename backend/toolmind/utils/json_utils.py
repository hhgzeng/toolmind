"""
JSON 解析工具函数
"""

import json
import re


def extract_and_parse_json(text: str) -> dict:
    """从字符串中提取并解析第一个 JSON 对象"""
    json_match = re.search(r"\{.*\}", text, re.DOTALL)
    json_str = json_match.group(0) if json_match else text
    return json.loads(json_str)
