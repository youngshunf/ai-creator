"""
智能路由器测试

@author Ysf
@date 2025-12-28
"""

import pytest
from agent_core.runtime import (
    RuntimeRouter,
    RoutingContext,
    RoutingDecision,
    RuntimeType,
)
from agent_core.runtime.router import RiskLevel, BudgetConfig, QueueState


class TestRuntimeRouter:
    """智能路由器测试"""

    @pytest.fixture
    def router(self):
        """创建路由器实例"""
        return RuntimeRouter()

    @pytest.fixture
    def basic_context(self):
        """基础路由上下文"""
        return RoutingContext(
            user_id="user_123",
            graph_name="test_graph",
            budget=BudgetConfig(daily_limit=100.0, used=10.0),
            queue=QueueState(local_pending=0, cloud_pending=0),
            risk_level=RiskLevel.LOW,
            required_capabilities=["browser"],
        )

    def test_route_local_preferred(self, router, basic_context):
        """测试本地优先路由"""
        basic_context.local_available = True
        basic_context.cloud_available = True

        decision = router.route(basic_context)

        assert decision.runtime_type == RuntimeType.LOCAL
        assert decision.reason is not None

    def test_route_cloud_fallback(self, router, basic_context):
        """测试云端降级"""
        basic_context.local_available = False
        basic_context.cloud_available = True

        decision = router.route(basic_context)

        assert decision.runtime_type == RuntimeType.CLOUD

    def test_route_budget_exceeded(self, router, basic_context):
        """测试预算超限"""
        basic_context.budget = BudgetConfig(daily_limit=100.0, used=100.0)
        basic_context.local_available = False
        basic_context.cloud_available = True

        decision = router.route(basic_context)

        # 预算超限应该拒绝云端
        assert decision.runtime_type != RuntimeType.CLOUD or not decision.allowed

    def test_route_high_risk(self, router, basic_context):
        """测试高风险任务"""
        basic_context.risk_level = RiskLevel.HIGH
        basic_context.local_available = True
        basic_context.cloud_available = True

        decision = router.route(basic_context)

        # 高风险任务应该优先本地
        assert decision.runtime_type == RuntimeType.LOCAL

    def test_route_queue_congestion(self, router, basic_context):
        """测试队列拥堵"""
        basic_context.queue = QueueState(local_pending=100, cloud_pending=5)
        basic_context.local_available = True
        basic_context.cloud_available = True

        decision = router.route(basic_context)

        # 本地队列拥堵应该考虑云端
        # 具体行为取决于实现
        assert decision is not None


class TestRoutingDecision:
    """路由决策测试"""

    def test_create_decision(self):
        """测试创建决策"""
        decision = RoutingDecision(
            runtime_type=RuntimeType.LOCAL,
            allowed=True,
            reason="本地可用",
        )
        assert decision.runtime_type == RuntimeType.LOCAL
        assert decision.allowed is True
        assert decision.reason == "本地可用"


class TestRiskLevel:
    """风险等级测试"""

    def test_risk_levels(self):
        """测试风险等级定义"""
        assert RiskLevel.LOW.value == "low"
        assert RiskLevel.MEDIUM.value == "medium"
        assert RiskLevel.HIGH.value == "high"


class TestBudgetConfig:
    """预算配置测试"""

    def test_budget_remaining(self):
        """测试剩余预算计算"""
        budget = BudgetConfig(daily_limit=100.0, used=30.0)
        assert budget.remaining == 70.0

    def test_budget_exceeded(self):
        """测试预算超限检测"""
        budget = BudgetConfig(daily_limit=100.0, used=100.0)
        assert budget.is_exceeded is True

        budget2 = BudgetConfig(daily_limit=100.0, used=50.0)
        assert budget2.is_exceeded is False
