"""
Agent 事件定义
@author Ysf
"""

from enum import Enum
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional

class EventType(str, Enum):
    """统一事件类型"""
    # 执行生命周期
    RUN_STARTED = "run_started"
    RUN_COMPLETED = "run_completed"
    RUN_FAILED = "run_failed"

    # 节点执行
    NODE_STARTED = "node_started"
    NODE_COMPLETED = "node_completed"

    # 工具调用
    TOOL_CALLED = "tool_called"
    TOOL_RESULT = "tool_result"

    # 人机交互
    HUMAN_REQUIRED = "human_required"
    HUMAN_RESPONDED = "human_responded"

    # 预算与成本
    BUDGET_WARNING = "budget_warning"
    COST_UPDATE = "cost_update"

@dataclass
class AgentEvent:
    """Agent 事件"""
    event_type: EventType
    run_id: str
    timestamp: datetime
    data: Optional[Any] = None

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "event_type": self.event_type.value,
            "run_id": self.run_id,
            "timestamp": self.timestamp.isoformat(),
            "data": self.data,
        }
