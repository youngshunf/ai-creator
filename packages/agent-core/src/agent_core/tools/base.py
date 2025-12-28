"""
工具接口 - 定义工具抽象基类
@author Ysf
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, List, Optional, ClassVar, Dict

from ..runtime.interfaces import RuntimeType


class ToolCapability(str, Enum):
    """
    工具能力枚举

    定义工具提供的核心能力类型。
    """

    LLM_GENERATE = "llm_generate"
    WEB_SEARCH = "web_search"
    IMAGE_GEN = "image_gen"
    BROWSER_AUTOMATION = "browser_automation"
    FILE_STORAGE = "file_storage"
    CREDENTIAL_STORE = "credential_store"
    HOT_TOPIC_DISCOVERY = "hot_topic_discovery"
    SENTIMENT_ANALYSIS = "sentiment_analysis"
    CONTENT_FORMATTING = "content_formatting"
    CONTENT_VALIDATION = "content_validation"


@dataclass
class ToolMetadata:
    """
    工具元数据

    描述工具的基本信息、能力、支持的运行环境等。
    """

    # 工具名称（唯一标识）
    name: str

    # 工具描述
    description: str

    # 工具能力
    capabilities: List[ToolCapability]

    # 支持的运行环境
    supported_runtimes: List[RuntimeType]

    # 备用工具（如果当前工具不可用）
    fallback_tool: Optional[str] = None

    # 是否需要认证
    requires_auth: bool = False

    # 额外元数据
    extra: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ToolResult:
    """
    工具执行结果

    封装工具执行的返回值、错误信息和元数据。
    """

    # 是否成功
    success: bool

    # 返回数据
    data: Any

    # 错误信息（失败时）
    error: Optional[str] = None

    # 执行元数据（如耗时、Token 数等）
    metadata: Dict[str, Any] = field(default_factory=dict)


class ToolInterface(ABC):
    """
    工具接口

    所有工具必须继承此接口，并实现核心方法。

    工具的生命周期：
    1. 注册到 ToolRegistry
    2. Compiler 为节点创建执行函数时获取工具
    3. 节点执行时调用 execute() 方法
    4. 返回 ToolResult

    示例:
        class MyTool(ToolInterface):
            metadata = ToolMetadata(
                name="my_tool",
                description="我的工具",
                capabilities=[ToolCapability.LLM_GENERATE],
                supported_runtimes=[RuntimeType.LOCAL, RuntimeType.CLOUD],
            )

            async def execute(self, ctx, **kwargs) -> ToolResult:
                # 实现逻辑
                return ToolResult(success=True, data="result")

            def get_schema(self) -> dict:
                return {
                    "type": "object",
                    "properties": {
                        "param1": {"type": "string"},
                    },
                }

            def is_available(self, ctx) -> bool:
                return True
    """

    # 工具元数据（类变量，子类必须定义）
    metadata: ClassVar[ToolMetadata]

    @abstractmethod
    async def execute(self, ctx: "RuntimeContext", **kwargs) -> ToolResult:
        """
        执行工具

        Args:
            ctx: 运行时上下文
            **kwargs: 工具参数（从 Graph 定义中解析）

        Returns:
            ToolResult: 执行结果

        Raises:
            ToolExecutionError: 执行失败
        """
        pass

    @abstractmethod
    def get_schema(self) -> Dict[str, Any]:
        """
        获取工具参数 Schema

        返回 JSON Schema 格式的参数定义，用于验证和文档生成。

        Returns:
            参数 Schema 字典

        示例:
            {
                "type": "object",
                "properties": {
                    "prompt": {"type": "string", "description": "提示词"},
                    "max_tokens": {"type": "integer", "default": 1000},
                },
                "required": ["prompt"],
            }
        """
        pass

    def is_available(self, ctx: "RuntimeContext") -> bool:
        """
        检查工具是否可用

        Args:
            ctx: 运行时上下文

        Returns:
            True 表示可用，False 表示不可用

        默认实现：检查运行时是否被支持
        """
        return ctx.runtime_type in self.metadata.supported_runtimes

    def get_name(self) -> str:
        """
        获取工具名称

        Returns:
            工具名称
        """
        return self.metadata.name


class ToolExecutionError(Exception):
    """工具执行错误"""

    pass

