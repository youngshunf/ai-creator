from typing import Dict, Any

from .base import ToolInterface, ToolMetadata, ToolResult, ToolCapability
from agent_core.runtime.interfaces import RuntimeType

class MockSearchTool(ToolInterface):
    """
    Mock 搜索工具 (用于开发/测试)
    """
    
    metadata = ToolMetadata(
        name="web_search",
        description="模拟联网搜索工具，返回预定义的结果。",
        capabilities=[ToolCapability.WEB_SEARCH],
        supported_runtimes=[RuntimeType.LOCAL],
    )
    
    async def execute(self, context: Any, **kwargs) -> ToolResult:
        query = kwargs.get("query", "")
        
        # 简单模拟返回
        mock_results = f"Search Results for '{query}':\n"
        mock_results += "1. [Official Docs] Python 3.13 Released: New features include subinterpreters, etc.\n"
        mock_results += "2. [Blog] What's new in AI? Agentic workflows are trending.\n"
        mock_results += "3. [Weather] Beijing Weather: Sunny, 25°C.\n"
        
        return ToolResult(success=True, data={"content": mock_results})

    def get_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string", 
                    "description": "搜索关键词"
                }
            },
            "required": ["query"]
        }
