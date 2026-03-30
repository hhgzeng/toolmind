from typing import Literal, Optional

from langchain.tools import tool
from tavily import TavilyClient


@tool("web_search", parse_docstring=True)
def web_search(
    query: str,
    topic: Optional[str],
    max_results: Optional[int],
    time_range: Optional[Literal["day", "week", "month", "year"]],
):
    """
    根据用户的问题以及查询参数进行联网搜索（使用 Tavily Search）

    Args:
        query: 用户想要搜索的问题
        topic: 搜索主题领域，general为通用，news为新闻，finance为财经
        max_results: 最大返回结果数量，控制结果数量上限
        time_range: 时间范围，筛选过去一天、一周、一个月或一年的内容

    Returns:
        将联网搜索到的信息返回给用户
    """
    # Note: `web_search` is typically called via LangChain agent.
    # The actual executing logic is mostly handled in `_process_tools_result` in `agent.py` where we bypass normal tool execution.
    return _web_search(query, topic, max_results, time_range)


def _web_search(query, topic, max_results, time_range, api_key: str = None):
    """使用 Tavily Search 工具进行联网搜索"""
    if not api_key:
        raise ValueError("Tavily API key is required")

    tavily_client = TavilyClient(api_key=api_key)
    response = tavily_client.search(
        query=query,
        country="china",
        topic=topic,
        time_range=time_range,
        max_results=max_results,
    )

    return "\n\n".join(
        [
            f'网址:{result["url"]}, 内容: {result["content"]}'
            for result in response["results"]
        ]
    )
