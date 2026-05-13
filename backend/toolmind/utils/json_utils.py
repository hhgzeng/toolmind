import json
import re
from json import JSONDecodeError


def extract_and_parse_json(text: str) -> dict:
    """从字符串中提取并解析第一个 JSON 对象"""
    if text is None:
        raise ValueError("text 不能为空")

    raw = text.strip()
    if not raw:
        raise ValueError("text 不能为空字符串")

    # 尽量只截取 JSON 对象片段，避免前后自然语言干扰解析。
    # 这里不使用贪婪正则直接匹配，防止多段大括号文本被吞并。
    start = raw.find("{")
    end = raw.rfind("}")
    json_str = raw[start : end + 1] if start != -1 and end != -1 and end > start else raw

    def _loads(s: str) -> dict:
        return json.loads(s)

    try:
        return _loads(json_str)
    except JSONDecodeError:
        repaired = _repair_common_json_issues(json_str)
        return _loads(repaired)


_WHITESPACE_RE = re.compile(r"\s*")


def _repair_common_json_issues(s: str) -> str:
    """
    尝试修复常见的模型输出 JSON 格式问题。

    目前主要处理：字符串值内部出现未转义的双引号，导致 json.loads 失败。
    修复策略：在字符串字面量内遇到 `"` 时，若它看起来不是字符串结束符，就将其转义为 `\"`。
    """
    out: list[str] = []
    i = 0
    in_string = False
    escape = False

    def _looks_like_string_terminator(src: str, quote_idx: int) -> bool:
        # 判断该 `"` 是否是字符串的结束引号。
        # - key 结束：后面（跳过空白）通常是 :
        # - value 结束：后面（跳过空白）通常是 , } ]
        j = quote_idx + 1
        while j < len(src) and src[j] in (" ", "\t", "\r", "\n"):
            j += 1
        if j >= len(src):
            return True
        return src[j] in (":", ",", "}", "]")

    while i < len(s):
        ch = s[i]

        if not in_string:
            if ch == '"':
                in_string = True
                out.append(ch)
            else:
                out.append(ch)
            i += 1
            continue

        # in_string == True
        if escape:
            out.append(ch)
            escape = False
            i += 1
            continue

        if ch == "\\":
            out.append(ch)
            escape = True
            i += 1
            continue

        if ch == '"':
            if _looks_like_string_terminator(s, i):
                in_string = False
                out.append(ch)
            else:
                out.append('\\"')
            i += 1
            continue

        out.append(ch)
        i += 1

    return "".join(out)
