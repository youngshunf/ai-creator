"""
LLM 统一接口定义

@author Ysf
@date 2025-12-28
"""

from abc import ABC, abstractmethod
from typing import Optional, AsyncIterator, List
from dataclasses import dataclass
from enum import Enum


class LLMProvider(str, Enum):
    """LLM 供应商"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    ALIBABA = "alibaba"
    DEEPSEEK = "deepseek"
    ZHIPU = "zhipu"
    MOONSHOT = "moonshot"


@dataclass
class ModelInfo:
    """模型信息"""
    model_id: str
    provider: LLMProvider
    display_name: str
    max_tokens: int
    supports_streaming: bool = True
    supports_vision: bool = False
    supports_tools: bool = True


@dataclass
class LLMMessage:
    """LLM 消息"""
    role: str  # system, user, assistant
    content: str


@dataclass
class LLMUsage:
    """Token 使用统计"""
    input_tokens: int
    output_tokens: int
    total_tokens: int


@dataclass
class LLMResponse:
    """LLM 响应"""
    content: str
    model: str
    provider: str
    usage: LLMUsage
    cost: float = 0.0
    latency_ms: int = 0
    finish_reason: str = "stop"


@dataclass
class LLMConfig:
    """LLM 客户端配置"""
    base_url: str
    api_token: str
    environment: str = "production"
    default_model: str = "claude-sonnet-4-20250514"
    default_max_tokens: int = 4096
    default_temperature: float = 0.7
    timeout_seconds: int = 120
    retry_count: int = 3
    direct_mode: bool = False


class LLMClientInterface(ABC):
    """
    LLM 客户端统一接口

    - 端侧实现: CloudLLMClient (HTTP 调用云端网关)
    - 云端实现: DirectLLMClient (直接调用 LLMGateway)
    """

    @abstractmethod
    async def chat(
        self,
        messages: List[LLMMessage],
        *,
        model: Optional[str] = None,
        system: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        user_id: Optional[str] = None,
    ) -> LLMResponse:
        """发送对话请求"""
        pass

    @abstractmethod
    async def chat_stream(
        self,
        messages: List[LLMMessage],
        *,
        model: Optional[str] = None,
        system: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        user_id: Optional[str] = None,
    ) -> AsyncIterator[str]:
        """流式对话请求"""
        pass

    @abstractmethod
    async def get_available_models(self) -> List[ModelInfo]:
        """获取可用模型列表"""
        pass

    @abstractmethod
    async def get_usage_summary(self, user_id: str, period: str = "month") -> dict:
        """获取用量汇总"""
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """健康检查"""
        pass


class LLMError(Exception):
    """LLM 调用异常"""
    pass
