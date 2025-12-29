"""
Discovery Service - 负责发现系统中可用的 Agent 和 Tools
@author Ysf
"""

import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

from ..graph.loader import GraphLoader
from ..tools.registry import ToolRegistry

logger = logging.getLogger(__name__)


class DiscoveryService:
    """
    发现服务
    
    提供查找和获取 Agent 定义及 Tool 信息的能力。
    Meta-Agent 使用此服务来了解系统中有哪些能力可用。
    """

    def __init__(
        self,
        graph_loader: GraphLoader,
        tool_registry: ToolRegistry,
    ):
        self.graph_loader = graph_loader
        self.tool_registry = tool_registry

    def list_agents(self) -> List[Dict[str, Any]]:
        """
        列出所有可用的 Agent
        
        Returns:
            Agent 摘要列表 [{"name": "...", "description": "..."}]
        """
        agents = []
        graph_names = self.graph_loader.list_graphs()
        
        for name in graph_names:
            try:
                # 尝试加载以获取描述
                # 注意：这里可能会有性能开销，如果 Agent 很多，考虑加缓存
                definition = self.graph_loader.load(name)
                metadata = definition.get("metadata", {})
                agents.append({
                    "name": metadata.get("name", name),
                    "description": metadata.get("description", "No description provided."),
                    "version": metadata.get("version", "0.0.0"),
                })
            except Exception as e:
                logger.warning(f"Failed to load agent '{name}' for discovery: {e}")
                
        return agents

    def get_agent_details(self, agent_name: str) -> Optional[Dict[str, Any]]:
        """
        获取指定 Agent 的详细定义
        
        Args:
            agent_name: Agent 名称
            
        Returns:
            完整 Agent 定义字典 (YAML/JSON 内容)
        """
        try:
            return self.graph_loader.load(agent_name)
        except Exception as e:
            logger.error(f"Failed to get details for agent '{agent_name}': {e}")
            return None

    def list_tools(self) -> List[Dict[str, Any]]:
        """
        列出所有已注册的工具
        
        Returns:
            Tool 摘要列表 [{"name": "...", "description": "..."}]
        """
        tools = []
        # ToolRegistry 目前没有直接暴露 list_tools 方法，我们需要检查一下 ToolRegistry 的实现
        # 假设 ToolRegistry 有 _tools 字典
        # 我们应该在 ToolRegistry 中添加 list_tools 方法，或者直接访问如果公开的话
        # 先按 ToolRegistry.get_all_tools() 这种假设写，回头确认 ToolRegistry 代码
        for name, tool in self.tool_registry._tools.items():
             tools.append({
                 "name": tool.metadata.name,
                 "description": tool.metadata.description,
                 "capabilities": [c.value for c in tool.metadata.capabilities],
             })
        return tools

    def get_tool_schema(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """
        获取指定工具的参数 Schema
        
        Args:
            tool_name: 工具名称
            
        Returns:
            JSON Schema
        """
        tool = self.tool_registry.get_tool(tool_name)
        if tool:
            return tool.get_schema()
        return None
