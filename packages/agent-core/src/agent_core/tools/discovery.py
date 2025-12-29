from typing import Any, Dict, Optional, List, Type
from pydantic import BaseModel, Field

from agent_core.tools.base import ToolInterface, ToolMetadata, ToolResult, ToolCapability
from agent_core.runtime.interfaces import RuntimeType
from agent_core.discovery.service import DiscoveryService

# -----------------------------------------------------------------------------
# Base Discovery Tool
# -----------------------------------------------------------------------------

class BaseDiscoveryTool(ToolInterface):
    """发现工具基类"""
    
    def _get_service(self, context: Any) -> DiscoveryService:
        """从 RuntimeContext 获取 DiscoveryService"""
        service = context.extra.get("discovery_service")
        if not service:
            raise ValueError("DiscoveryService not found in RuntimeContext.extra")
        return service

# -----------------------------------------------------------------------------
# Agent Discovery Tools
# -----------------------------------------------------------------------------

class ListAgentsTool(BaseDiscoveryTool):
    metadata = ToolMetadata(
        name="discovery_list_agents",
        description="列出系统中所有可用的 Agent",
        capabilities=[],
        supported_runtimes=[RuntimeType.LOCAL, RuntimeType.CLOUD],
    )
    
    async def execute(self, ctx: Any, **kwargs) -> ToolResult:
        try:
            service = self._get_service(ctx)
            agents = service.list_agents()
            return ToolResult(success=True, data={"agents": agents})
        except Exception as e:
            return ToolResult(success=False, error=str(e))

    def get_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {},
        }

class GetAgentArgs(BaseModel):
    name: str = Field(..., description="Agent 名称")

class GetAgentDetailsTool(BaseDiscoveryTool):
    metadata = ToolMetadata(
        name="discovery_get_agent",
        description="获取指定 Agent 的详细定义 (Inputs, Outputs, Description)",
        capabilities=[],
        supported_runtimes=[RuntimeType.LOCAL, RuntimeType.CLOUD],
    )
    
    async def execute(self, ctx: Any, **kwargs) -> ToolResult:
        name = kwargs.get("name")
        if not name:
            return ToolResult(success=False, error="Missing 'name'")
            
        try:
            service = self._get_service(ctx)
            details = service.get_agent_details(name)
            if not details:
                return ToolResult(success=False, error=f"Agent '{name}' not found")
            return ToolResult(success=True, data={"agent": details})
        except Exception as e:
            return ToolResult(success=False, error=str(e))

    def get_schema(self) -> Dict[str, Any]:
        return GetAgentArgs.model_json_schema()

# -----------------------------------------------------------------------------
# Tool Discovery Tools
# -----------------------------------------------------------------------------

class ListToolsTool(BaseDiscoveryTool):
    metadata = ToolMetadata(
        name="discovery_list_tools",
        description="列出系统中所有可用的工具",
        capabilities=[],
        supported_runtimes=[RuntimeType.LOCAL, RuntimeType.CLOUD],
    )
    
    async def execute(self, ctx: Any, **kwargs) -> ToolResult:
        try:
            service = self._get_service(ctx)
            tools = service.list_tools()
            return ToolResult(success=True, data={"tools": tools})
        except Exception as e:
            return ToolResult(success=False, error=str(e))

    def get_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {},
        }

class GetToolArgs(BaseModel):
    name: str = Field(..., description="工具名称")

class GetToolDetailsTool(BaseDiscoveryTool):
    metadata = ToolMetadata(
        name="discovery_get_tool",
        description="获取指定工具的参数定义 (Schema)",
        capabilities=[],
        supported_runtimes=[RuntimeType.LOCAL, RuntimeType.CLOUD],
    )
    
    async def execute(self, ctx: Any, **kwargs) -> ToolResult:
        name = kwargs.get("name")
        if not name:
            return ToolResult(success=False, error="Missing 'name'")
            
        try:
            service = self._get_service(ctx)
            schema = service.get_tool_schema(name)
            if not schema:
                return ToolResult(success=False, error=f"Tool '{name}' not found")
            return ToolResult(success=True, data={"schema": schema})
        except Exception as e:
            return ToolResult(success=False, error=str(e))

    def get_schema(self) -> Dict[str, Any]:
        return GetToolArgs.model_json_schema()
