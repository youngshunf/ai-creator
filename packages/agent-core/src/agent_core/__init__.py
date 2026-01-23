"""
AI Creator Agent 核心共享包

提供端云统一的 Agent Runtime 抽象层。

三层架构：
- Layer 1: Agent Definition Layer (Graph 定义层)
- Layer 2: Agent Runtime Layer (执行器层)
- Layer 3: Tool Layer (工具层)

@author Ysf
@date 2025-12-28
"""

__version__ = "0.1.0"

# 运行时接口
from .runtime import (
    RuntimeType,
    ExecutionRequest,
    ExecutionResponse,
    ExecutorInterface,
    RuntimeContext,
    AgentEvent,
    EventType,
    RuntimeRouter,
    RoutingContext,
    RoutingDecision,
)

# Graph 相关
from .graph import (
    GraphLoader,
    GraphCompiler,
    GraphValidator,
)

# 工具相关
from .tools import (
    ToolInterface,
    ToolMetadata,
    ToolCapability,
    ToolResult,
    ToolRegistry,
)

# LLM 相关
from .llm import (
    LLMClientInterface,
    LLMConfig,
    LLMMessage,
    LLMResponse,
    CloudLLMClient,
    DirectLLMClient,
    LLMConfigManager,
)

from .topic_recommender import (
    HotTopic,
    TopicCard,
    TopicRecommender,
    HotTopicProvider,
    TopicAnalyzer,
)

__all__ = [
    # 版本
    "__version__",
    # 运行时
    "RuntimeType",
    "ExecutionRequest",
    "ExecutionResponse",
    "ExecutorInterface",
    "RuntimeContext",
    "AgentEvent",
    "EventType",
    "RuntimeRouter",
    "RoutingContext",
    "RoutingDecision",
    # Graph
    "GraphLoader",
    "GraphCompiler",
    "GraphValidator",
    # 工具
    "ToolInterface",
    "ToolMetadata",
    "ToolCapability",
    "ToolResult",
    "ToolRegistry",
    # LLM
    "LLMClientInterface",
    "LLMConfig",
    "LLMMessage",
    "LLMResponse",
    "CloudLLMClient",
    "DirectLLMClient",
    "LLMConfigManager",
    # Topic recommender
    "HotTopic",
    "TopicCard",
    "TopicRecommender",
    "HotTopicProvider",
    "TopicAnalyzer",
]
