"""
运行时上下文 - 管理执行环境信息
@author Ysf
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, TYPE_CHECKING

from .interfaces import RuntimeType

if TYPE_CHECKING:
    from ..resource.resolver import AssetResolver


@dataclass
class RuntimeContext:
    """
    运行时上下文

    包含 Graph 执行所需的所有环境信息，包括用户信息、模型配置、
    API 密钥、资源解析器等。
    """

    # 基础信息
    runtime_type: RuntimeType
    user_id: str

    # Graph 输入参数
    inputs: Dict[str, Any] = field(default_factory=dict)

    # 模型配置
    model_default: str = "claude-sonnet-4-20250514"
    model_fast: str = "claude-3-5-haiku-20241022"

    # API 密钥 (运行时注入，不持久化)
    api_keys: Dict[str, str] = field(default_factory=dict)

    # 资源解析器
    asset_resolver: Optional["AssetResolver"] = None

    # 额外上下文 (端/云特有配置)
    extra: Dict[str, Any] = field(default_factory=dict)

    # 追踪标识
    trace_id: str = ""
    run_id: str = ""

    # 设备类型 (可选)
    device_type: Optional[str] = None

    def get_api_key(self, provider: str) -> Optional[str]:
        """
        获取指定供应商的 API 密钥

        Args:
            provider: 供应商名称 (如 "anthropic", "openai")

        Returns:
            API 密钥，如果不存在返回 None
        """
        return self.api_keys.get(provider)

    def set_api_key(self, provider: str, key: str) -> None:
        """
        设置指定供应商的 API 密钥

        Args:
            provider: 供应商名称
            key: API 密钥
        """
        self.api_keys[provider] = key
