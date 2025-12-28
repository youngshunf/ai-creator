"""
运行时接口 - 定义执行器抽象基类
@author Ysf
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Dict, Any, AsyncIterator


class RuntimeType(str, Enum):
    """运行时类型"""
    LOCAL = "local"
    CLOUD = "cloud"


@dataclass
class ExecutionRequest:
    """
    Graph 执行请求

    封装执行 Graph 所需的所有参数，包括 Graph 名称、输入参数、
    用户标识、会话信息等。
    """

    # 必填参数
    graph_name: str
    inputs: Dict[str, Any]
    user_id: str

    # 可选参数
    session_id: Optional[str] = None
    timeout: int = 300  # 超时时间（秒）
    trace_id: Optional[str] = None

    # 额外配置
    extra: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExecutionResponse:
    """
    Graph 执行响应

    包含执行结果、错误信息、执行统计等。
    """

    # 执行结果
    success: bool
    outputs: Any
    error: Optional[str] = None

    # 执行标识
    execution_id: str = ""
    trace_id: str = ""

    # 执行统计
    execution_time: float = 0.0  # 执行时长（秒）
    tokens_used: int = 0  # 消耗的 token 数
    cost_cents: int = 0  # 成本（分）

    # 运行时信息
    runtime_type: RuntimeType = RuntimeType.LOCAL

    # 额外元数据
    metadata: Dict[str, Any] = field(default_factory=dict)


class ExecutorInterface(ABC):
    """
    执行器接口

    定义 Graph 执行器的标准接口，所有执行器（本地/云端）
    必须实现此接口。
    """

    runtime_type: RuntimeType

    @abstractmethod
    async def execute(self, request: ExecutionRequest) -> ExecutionResponse:
        """
        执行 Graph（同步模式）

        Args:
            request: 执行请求

        Returns:
            执行响应

        Raises:
            GraphNotFoundError: Graph 不存在
            GraphValidationError: Graph 验证失败
            GraphExecutionError: Graph 执行失败
            TimeoutError: 执行超时
        """
        pass

    @abstractmethod
    async def execute_stream(
        self, request: ExecutionRequest
    ) -> AsyncIterator["AgentEvent"]:
        """
        执行 Graph（流式模式）

        Args:
            request: 执行请求

        Yields:
            AgentEvent: 执行过程中的事件流

        Raises:
            同 execute() 方法
        """
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """
        健康检查

        Returns:
            True 表示执行器健康，False 表示异常
        """
        pass
