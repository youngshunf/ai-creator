"""
智能路由器 - 决定 Graph 在本地还是云端执行

根据预算、队列、风控、能力四个维度进行路由决策。

@author Ysf
@date 2025-12-28
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List, Dict, Any

from .interfaces import RuntimeType, ExecutionRequest


class RiskLevel(str, Enum):
    """风险等级"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class BudgetConfig:
    """预算配置"""
    max_cost_cents: int = 1000  # 单次执行最大成本(分)
    max_tokens: int = 100000  # 最大 Token 消耗
    max_steps: int = 50  # 最大执行步数


@dataclass
class QueueState:
    """队列状态"""
    queue_length: int = 0  # 当前排队长度
    estimated_wait_seconds: int = 0  # 预估等待时间
    user_concurrency_remaining: int = 3  # 用户并发配额剩余


@dataclass
class RoutingContext:
    """路由上下文"""
    # 设备信息
    device_type: str = "desktop"  # desktop | mobile
    has_local_sidecar: bool = True  # 是否有本地 Sidecar

    # 风险等级
    risk_level: RiskLevel = RiskLevel.LOW

    # 预算配置
    budget: BudgetConfig = field(default_factory=BudgetConfig)

    # 队列状态
    queue_state: QueueState = field(default_factory=QueueState)

    # 本地可用工具
    local_tools: List[str] = field(default_factory=list)

    # 云端可用工具
    cloud_tools: List[str] = field(default_factory=list)


@dataclass
class RoutingDecision:
    """路由决策"""
    runtime: RuntimeType
    reason: str
    requires_confirmation: bool = False
    budget_warning: bool = False
    estimated_cost: int = 0
    fallback_runtime: Optional[RuntimeType] = None


class RuntimeRouter:
    """
    智能路由器

    根据四个维度进行路由决策：
    1. 预算维度 (Budget)
    2. 队列维度 (Queue)
    3. 风控维度 (Risk)
    4. 能力维度 (Capability)
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化路由器

        Args:
            config: 路由配置
        """
        self.config = config or {}

        # 高风险操作列表
        self._high_risk_tools = {
            "browser_publish",
            "credential_manager",
            "account_operation",
        }

        # 仅本地可用的工具
        self._local_only_tools = {
            "local_file_access",
            "local_browser",
        }

        # 仅云端可用的工具
        self._cloud_only_tools = {
            "cloud_storage",
            "cloud_browser_pool",
        }

    def route(
        self,
        request: ExecutionRequest,
        ctx: RoutingContext,
    ) -> RoutingDecision:
        """
        综合决策执行环境

        Args:
            request: 执行请求
            ctx: 路由上下文

        Returns:
            RoutingDecision: 路由决策
        """
        # 1. 移动端强制云端
        if ctx.device_type == "mobile":
            return RoutingDecision(
                runtime=RuntimeType.CLOUD,
                reason="移动端仅支持云端执行",
            )

        # 2. 关键操作优先本地
        if ctx.risk_level == RiskLevel.CRITICAL:
            if ctx.has_local_sidecar:
                return RoutingDecision(
                    runtime=RuntimeType.LOCAL,
                    reason="关键操作优先本地执行",
                )
            return RoutingDecision(
                runtime=RuntimeType.CLOUD,
                reason="关键操作需要云端执行（无本地 Sidecar）",
                requires_confirmation=True,
            )

        # 3. 预算检查
        estimated_cost = self._estimate_cost(request)
        if estimated_cost > ctx.budget.max_cost_cents:
            return RoutingDecision(
                runtime=RuntimeType.LOCAL if ctx.has_local_sidecar else RuntimeType.CLOUD,
                reason="预算超限，优先本地执行",
                budget_warning=True,
                estimated_cost=estimated_cost,
            )

        # 4. 队列拥塞检查
        if ctx.queue_state.estimated_wait_seconds > 60:
            if ctx.has_local_sidecar and self._can_run_locally(request, ctx):
                return RoutingDecision(
                    runtime=RuntimeType.LOCAL,
                    reason=f"云端队列拥塞（预估等待 {ctx.queue_state.estimated_wait_seconds}s），切换本地执行",
                )

        # 5. 能力匹配检查
        can_local = self._can_run_locally(request, ctx)
        can_cloud = self._can_run_in_cloud(request, ctx)

        if not can_local and not can_cloud:
            return RoutingDecision(
                runtime=RuntimeType.LOCAL,
                reason="所需工具不可用",
                requires_confirmation=True,
            )

        if not can_local and can_cloud:
            return RoutingDecision(
                runtime=RuntimeType.CLOUD,
                reason="所需工具仅云端可用",
            )

        if can_local and not can_cloud:
            return RoutingDecision(
                runtime=RuntimeType.LOCAL,
                reason="所需工具仅本地可用",
            )

        # 6. 默认本地优先
        if ctx.has_local_sidecar:
            return RoutingDecision(
                runtime=RuntimeType.LOCAL,
                reason="默认本地执行",
                fallback_runtime=RuntimeType.CLOUD,
            )

        return RoutingDecision(
            runtime=RuntimeType.CLOUD,
            reason="无本地 Sidecar，使用云端执行",
        )

    def _estimate_cost(self, request: ExecutionRequest) -> int:
        """
        估算执行成本

        Args:
            request: 执行请求

        Returns:
            预估成本（分）
        """
        # 简化的成本估算
        # 实际应该根据 Graph 定义和历史数据估算
        base_cost = 10  # 基础成本 10 分

        # 根据输入大小调整
        input_size = len(str(request.inputs))
        input_cost = input_size // 1000  # 每 1000 字符 1 分

        return base_cost + input_cost

    def _can_run_locally(
        self,
        request: ExecutionRequest,
        ctx: RoutingContext,
    ) -> bool:
        """
        检查是否可以本地执行

        Args:
            request: 执行请求
            ctx: 路由上下文

        Returns:
            是否可以本地执行
        """
        if not ctx.has_local_sidecar:
            return False

        # 检查是否有云端专用工具
        required_tools = self._get_required_tools(request)
        for tool in required_tools:
            if tool in self._cloud_only_tools:
                return False

        return True

    def _can_run_in_cloud(
        self,
        request: ExecutionRequest,
        ctx: RoutingContext,
    ) -> bool:
        """
        检查是否可以云端执行

        Args:
            request: 执行请求
            ctx: 路由上下文

        Returns:
            是否可以云端执行
        """
        # 检查是否有本地专用工具
        required_tools = self._get_required_tools(request)
        for tool in required_tools:
            if tool in self._local_only_tools:
                return False

        return True

    def _get_required_tools(self, request: ExecutionRequest) -> List[str]:
        """
        获取执行所需的工具列表

        Args:
            request: 执行请求

        Returns:
            工具名称列表
        """
        # TODO: 从 Graph 定义中解析所需工具
        # 当前返回空列表
        return []

    def get_risk_level(
        self,
        request: ExecutionRequest,
        tools: List[str],
    ) -> RiskLevel:
        """
        评估操作风险等级

        Args:
            request: 执行请求
            tools: 使用的工具列表

        Returns:
            风险等级
        """
        # 检查是否包含高风险工具
        for tool in tools:
            if tool in self._high_risk_tools:
                return RiskLevel.HIGH

        # 检查是否涉及账号操作
        if "account" in request.graph_name.lower():
            return RiskLevel.HIGH

        # 检查是否涉及发布操作
        if "publish" in request.graph_name.lower():
            return RiskLevel.MEDIUM

        return RiskLevel.LOW
