"""
直接调用 LLM 客户端 - 云端服务使用

直接调用 LLMGateway 实例，无需 HTTP 开销。

@author Ysf
@date 2025-12-28
"""

from typing import List, Optional, AsyncIterator, TYPE_CHECKING

from .interface import (
    LLMClientInterface,
    LLMConfig,
    LLMMessage,
    LLMResponse,
    LLMUsage,
    ModelInfo,
    ModelType,
    LLMProvider,
)

if TYPE_CHECKING:
    from backend.app.llm.core.gateway import LLMGateway


class DirectLLMClient(LLMClientInterface):
    """
    直接调用 LLM 客户端

    云端服务使用，直接调用 LLMGateway 实例，无需 HTTP 开销。
    """

    def __init__(self, gateway: "LLMGateway", config: LLMConfig):
        """
        初始化直接调用客户端

        Args:
            gateway: LLMGateway 实例 (云端服务注入)
            config: LLM 配置
        """
        self.gateway = gateway
        self.config = config

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
        """
        直接调用 LLMGateway

        Args:
            messages: 对话消息列表
            model: 模型名称
            system: 系统提示
            max_tokens: 最大生成 tokens
            temperature: 温度参数
            user_id: 用户ID

        Returns:
            LLMResponse: 响应结果
        """
        api_messages = [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]

        response = await self.gateway.chat(
            messages=api_messages,
            model_id=model or self.config.default_model,
            user_id=user_id,
            system=system,
            max_tokens=max_tokens or self.config.default_max_tokens,
            temperature=temperature if temperature is not None else self.config.default_temperature,
            stream=False,
        )

        return LLMResponse(
            content=response.content,
            model=response.model,
            provider=response.provider,
            usage=LLMUsage(
                input_tokens=response.usage.get("input_tokens", 0),
                output_tokens=response.usage.get("output_tokens", 0),
                total_tokens=response.usage.get("input_tokens", 0) + response.usage.get("output_tokens", 0),
            ),
            cost=response.cost,
            latency_ms=response.latency_ms,
        )

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
        """
        直接调用 LLMGateway 流式接口

        Args:
            messages: 对话消息列表
            model: 模型名称
            system: 系统提示
            max_tokens: 最大生成 tokens
            temperature: 温度参数
            user_id: 用户ID

        Yields:
            str: 逐字返回的内容片段
        """
        api_messages = [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]

        async for chunk in self.gateway.chat_stream(
            messages=api_messages,
            model_id=model or self.config.default_model,
            user_id=user_id,
            system=system,
            max_tokens=max_tokens or self.config.default_max_tokens,
            temperature=temperature if temperature is not None else self.config.default_temperature,
        ):
            yield chunk

    async def get_available_models(self) -> List[ModelInfo]:
        """
        从数据库获取模型列表

        Returns:
            List[ModelInfo]: 模型信息列表
        """
        models = await self.gateway.get_available_models()
        return [
            ModelInfo(
                model_id=m.model_id,
                provider=LLMProvider(m.provider) if hasattr(m, 'provider') else LLMProvider.OPENAI,
                display_name=m.display_name if hasattr(m, 'display_name') else m.model_id,
                max_tokens=m.max_tokens if hasattr(m, 'max_tokens') else 4096,
                model_type=ModelType(m.model_type) if hasattr(m, 'model_type') else ModelType.TEXT,
                supports_streaming=m.supports_streaming if hasattr(m, 'supports_streaming') else True,
                supports_vision=m.supports_vision if hasattr(m, 'supports_vision') else False,
                priority=m.priority if hasattr(m, 'priority') else 0,
                enabled=m.enabled if hasattr(m, 'enabled') else True,
            )
            for m in models
            if getattr(m, 'enabled', True)
        ]

    async def get_model_by_type(self, model_type: ModelType) -> Optional[ModelInfo]:
        """
        按类型获取推荐模型

        Args:
            model_type: 模型类型

        Returns:
            ModelInfo: 该类型下优先级最高的可用模型
        """
        models = await self.get_models_by_type(model_type)
        return models[0] if models else None

    async def get_models_by_type(self, model_type: ModelType) -> List[ModelInfo]:
        """
        按类型获取所有可用模型

        Args:
            model_type: 模型类型

        Returns:
            List[ModelInfo]: 该类型下所有可用模型，按优先级排序
        """
        all_models = await self.get_available_models()
        typed_models = [m for m in all_models if m.model_type == model_type and m.enabled]
        return sorted(typed_models, key=lambda m: m.priority, reverse=True)

    async def get_usage_summary(
        self,
        user_id: str,
        period: str = "month",
    ) -> dict:
        """
        从用量追踪器获取统计

        Args:
            user_id: 用户ID
            period: 统计周期

        Returns:
            dict: 用量统计数据
        """
        if hasattr(self.gateway, 'usage_tracker'):
            return await self.gateway.usage_tracker.get_usage_summary(user_id, period)
        return {}

    async def health_check(self) -> bool:
        """
        检查网关状态

        Returns:
            bool: 始终返回 True (直接调用)
        """
        return True
