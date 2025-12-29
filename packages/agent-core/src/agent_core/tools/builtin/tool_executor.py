import json
import logging
from typing import Any, Dict, List

from ..base import ToolInterface, ToolMetadata, ToolResult, ToolCapability
from ...runtime.context import RuntimeContext
from ...runtime.interfaces import RuntimeType
from ...llm.interface import LLMMessage

logger = logging.getLogger(__name__)

class ToolExecutionTool(ToolInterface):
    """
    工具执行器 - 执行 LLM 返回的 Tool Calls
    """
    
    metadata = ToolMetadata(
        name="tool_executor",
        description="执行工具调用列表",
        capabilities=[ToolCapability.TOOL_CALL],
        supported_runtimes=[RuntimeType.LOCAL, RuntimeType.CLOUD],
    )
    
    async def execute(self, ctx: RuntimeContext, **kwargs) -> ToolResult:
        """
        执行工具调用
        
        Args:
            ctx: 运行时上下文
            **kwargs: 参数
                - tool_calls: 工具调用列表 (OpenAI 格式)
                
        Returns:
            ToolResult: 执行结果列表
        """
        tool_calls = kwargs.get("tool_calls", [])
        if not tool_calls:
            return ToolResult(success=True, data=[])
            
        registry = ctx.extra.get("tool_registry")
        if not registry:
            return ToolResult(success=False, error="Tool registry not found in context")
            
        results = []
        for call in tool_calls:
            try:
                function_def = call.get("function", {})
                name = function_def.get("name")
                arguments_str = function_def.get("arguments", "{}")
                
                logger.info(f"[ToolExecutor] Executing tool: {name}")
                
                if isinstance(arguments_str, str):
                    try:
                        arguments = json.loads(arguments_str)
                    except json.JSONDecodeError:
                        arguments = {}
                else:
                    arguments = arguments_str or {}
                
                tool = registry.get_tool(name)
                if not tool:
                    results.append({
                        "id": call.get("id"),
                        "name": name,
                        "success": False,
                        "error": f"Tool '{name}' not found"
                    })
                    continue
                    
                # 执行工具
                result = await tool.execute(ctx, **arguments)
                
                results.append({
                    "id": call.get("id"),
                    "name": name,
                    "success": result.success,
                    "data": result.data,
                    "error": result.error
                })
                
            except Exception as e:
                logger.error(f"[ToolExecutor] Execution failed: {e}")
                results.append({
                    "id": call.get("id"),
                    "success": False,
                    "error": str(e)
                })
        
        # 构造 LLMMessage 列表 (role='tool')
        messages = []
        for res in results:
            content_str = json.dumps(res["data"]) if res["success"] else f"Error: {res['error']}"
            messages.append(LLMMessage(
                role="tool",
                content=content_str,
                tool_call_id=res["id"],
                name=res["name"]
            ))

        return ToolResult(success=True, data={"results": results, "messages": messages})

    def get_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "tool_calls": {
                    "type": "array",
                    "description": "工具调用列表",
                    "items": {"type": "object"}
                }
            }
        }
