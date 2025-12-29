"""
LLM 统一接口定义

@author Ysf
@date 2025-12-28
"""

from abc import ABC, abstractmethod
from typing import Optional, AsyncIterator, List
from dataclasses import dataclass, field
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


class ModelType(str, Enum):
    """
    模型类型

    与云端后端和前端 MODEL_TYPES 保持一致
    """

    TEXT = 'TEXT'           # 文本生成
    REASONING = 'REASONING' # 推理
    VISION = 'VISION'       # 视觉
    IMAGE = 'IMAGE'         # 图像生成
    VIDEO = 'VIDEO'         # 视频生成
    EMBEDDING = 'EMBEDDING' # 嵌入
    TTS = 'TTS'             # 语音合成
    STT = 'STT'             # 语音识别


@dataclass
class ModelInfo:
    """模型信息"""
    model_id: str
    provider: LLMProvider
    display_name: str
    max_tokens: int
    model_type: ModelType = ModelType.TEXT
    supports_streaming: bool = True
    supports_vision: bool = False
    supports_tools: bool = True
    priority: int = 0  # 同类型模型的优先级，数值越大优先级越高
    enabled: bool = True  # 是否启用


@dataclass
class LLMMessage:
    """LLM 消息"""
    role: str  # system, user, assistant, tool
    content: str
    name: Optional[str] = None
    tool_calls: Optional[List[dict]] = None
    tool_call_id: Optional[str] = None


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
    tool_calls: Optional[List[dict]] = None


@dataclass
class LLMConfig:
    """LLM 客户端配置"""
    base_url: str
    api_token: str  # LLM API Key (sk-cf-xxx)
    access_token: str = ""  # JWT Token (用于用户认证)
    access_token_expire_time: str = ""  # JWT 过期时间 (ISO 格式)
    refresh_token: str = ""  # 刷新令牌
    refresh_token_expire_time: str = ""  # 刷新令牌过期时间 (ISO 格式)
    environment: str = "production"
    default_model: str = "claude-sonnet-4-5-20250929"
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
        tools: Optional[List[dict]] = None,
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
    async def get_model_by_type(self, model_type: ModelType) -> Optional[ModelInfo]:
        """
        按类型获取推荐模型

        Args:
            model_type: 模型类型

        Returns:
            ModelInfo: 该类型下优先级最高的可用模型，无可用模型返回 None
        """
        pass

    @abstractmethod
    async def get_models_by_type(self, model_type: ModelType) -> List[ModelInfo]:
        """
        按类型获取所有可用模型

        Args:
            model_type: 模型类型

        Returns:
            List[ModelInfo]: 该类型下所有可用模型，按优先级排序
        """
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
