"""
网络搜索工具 - 使用 Tavily API 进行网络搜索
@author Ysf
"""

from typing import Optional, List, Dict, Any

from ..base import (
    ToolInterface,
    ToolMetadata,
    ToolResult,
    ToolCapability,
    ToolExecutionError,
)
from ...runtime.interfaces import RuntimeType
from ...runtime.context import RuntimeContext


class WebSearchTool(ToolInterface):
    """
    网络搜索工具

    使用 Tavily API 进行网络搜索，返回搜索结果摘要。
    支持本地和云端运行环境。

    Tavily API 文档: https://tavily.com/
    """

    metadata = ToolMetadata(
        name="web_search",
        description="使用网络搜索引擎搜索信息",
        capabilities=[ToolCapability.WEB_SEARCH],
        supported_runtimes=[RuntimeType.LOCAL, RuntimeType.CLOUD],
    )

    def __init__(self):
        """初始化工具"""
        self._client = None

    async def execute(self, ctx: RuntimeContext, **kwargs) -> ToolResult:
        """
        执行网络搜索

        Args:
            ctx: 运行时上下文
            **kwargs: 工具参数
                - query (str): 搜索关键词
                - max_results (int, optional): 最大结果数量，默认 5
                - search_depth (str, optional): 搜索深度 "basic" 或 "advanced"
                - include_domains (List[str], optional): 限定搜索的域名列表
                - exclude_domains (List[str], optional): 排除的域名列表

        Returns:
            ToolResult: 包含搜索结果列表

        Raises:
            ToolExecutionError: 执行失败
        """
        try:
            # 尝试导入 tavily
            try:
                from tavily import TavilyClient
            except ImportError:
                return ToolResult(
                    success=False,
                    data=None,
                    error="未安装 tavily-python 库，请运行: pip install tavily-python",
                )

            # 提取参数
            query = kwargs.get("query")
            if not query:
                raise ToolExecutionError("缺少必填参数: query")

            max_results = kwargs.get("max_results", 5)
            search_depth = kwargs.get("search_depth", "basic")
            include_domains = kwargs.get("include_domains", [])
            exclude_domains = kwargs.get("exclude_domains", [])

            # 获取 API 密钥
            api_key = ctx.get_api_key("tavily")
            if not api_key:
                raise ToolExecutionError("未配置 Tavily API 密钥")

            # 创建客户端
            client = TavilyClient(api_key=api_key)

            # 执行搜索
            search_params = {
                "query": query,
                "max_results": max_results,
                "search_depth": search_depth,
            }

            if include_domains:
                search_params["include_domains"] = include_domains
            if exclude_domains:
                search_params["exclude_domains"] = exclude_domains

            response = client.search(**search_params)

            # 处理结果
            results = self._process_results(response)

            return ToolResult(
                success=True,
                data={
                    "query": query,
                    "results": results,
                    "total": len(results),
                },
                metadata={
                    "search_depth": search_depth,
                    "max_results": max_results,
                },
            )

        except ToolExecutionError:
            raise
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"网络搜索失败: {e}",
            )

    def _process_results(self, response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        处理搜索结果

        Args:
            response: Tavily API 响应

        Returns:
            处理后的结果列表
        """
        results = []

        for item in response.get("results", []):
            results.append({
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "content": item.get("content", ""),
                "score": item.get("score", 0.0),
            })

        return results

    def get_schema(self) -> dict:
        """
        获取工具参数 Schema

        Returns:
            JSON Schema 定义
        """
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "搜索关键词",
                },
                "max_results": {
                    "type": "integer",
                    "description": "最大结果数量",
                    "default": 5,
                    "minimum": 1,
                    "maximum": 20,
                },
                "search_depth": {
                    "type": "string",
                    "description": "搜索深度: basic（快速）或 advanced（深度）",
                    "enum": ["basic", "advanced"],
                    "default": "basic",
                },
                "include_domains": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "限定搜索的域名列表（可选）",
                },
                "exclude_domains": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "排除的域名列表（可选）",
                },
            },
            "required": ["query"],
        }
