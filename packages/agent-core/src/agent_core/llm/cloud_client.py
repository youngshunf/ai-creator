"""
云端 LLM 客户端 - 桌面端/Sidecar 使用

通过 HTTP 调用云端 LLM 网关，支持 OpenAI 兼容格式。
支持 JWT Token 自动刷新。

@author Ysf
@date 2025-12-28
"""

import json
from datetime import datetime, timezone
from typing import List, Optional, AsyncIterator, Dict, Any

import aiohttp

from .interface import (
    LLMClientInterface,
    LLMConfig,
    LLMMessage,
    LLMResponse,
    LLMUsage,
    ModelInfo,
    ModelType,
    LLMError,
    LLMProvider,
)


class CloudLLMClient(LLMClientInterface):
    """
    云端 LLM 客户端

    桌面端/Sidecar 使用，通过 HTTP 调用云端 LLM 网关。
    支持 OpenAI 兼容格式的 API。
    支持 JWT Token 自动刷新。
    """

    def __init__(self, config: LLMConfig):
        """
        初始化云端 LLM 客户端

        Args:
            config: LLM 配置
        """
        self.config = config
        self._session: Optional[aiohttp.ClientSession] = None
        self._default_model_cache: Optional[str] = None  # 缓存动态获取的默认模型

    def _is_token_expired(self) -> bool:
        """检查 access_token 是否过期（提前 5 分钟刷新）"""
        if not self.config.access_token_expire_time:
            return False
        try:
            expire_time = datetime.fromisoformat(
                self.config.access_token_expire_time.replace("Z", "+00:00")
            )
            # 提前 5 分钟刷新
            buffer_seconds = 300
            now = datetime.now(timezone.utc)
            return now.timestamp() >= (expire_time.timestamp() - buffer_seconds)
        except (ValueError, AttributeError):
            return False

    async def _refresh_token(self) -> bool:
        """
        刷新 access_token

        Returns:
            bool: 刷新是否成功
        """
        if not self.config.refresh_token:
            return False

        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.config.base_url}/api/v1/auth/refresh"
                headers = {
                    "Content-Type": "application/json",
                    "Cookie": f"refresh_token={self.config.refresh_token}",
                }
                async with session.post(url, headers=headers) as response:
                    if response.status != 200:
                        return False
                    data = await response.json()

                # 更新配置
                resp_data = data.get("data", {})
                new_access_token = resp_data.get("access_token")
                new_expire_time = resp_data.get("access_token_expire_time")

                if new_access_token:
                    self.config.access_token = new_access_token
                    if new_expire_time:
                        self.config.access_token_expire_time = new_expire_time

                    # 关闭旧会话，下次请求时会创建新会话
                    if self._session and not self._session.closed:
                        await self._session.close()
                        self._session = None

                    # 保存到配置文件
                    from .config import LLMConfigManager
                    config_manager = LLMConfigManager()
                    config_manager.save_token(
                        api_token=self.config.api_token,
                        environment=self.config.environment,
                        access_token=new_access_token,
                        access_token_expire_time=new_expire_time or "",
                        refresh_token=self.config.refresh_token,
                        refresh_token_expire_time=self.config.refresh_token_expire_time,
                    )
                    return True
        except Exception:
            pass
        return False

    async def _ensure_valid_token(self):
        """确保 token 有效，如果过期则自动刷新"""
        if self._is_token_expired():
            await self._refresh_token()

    async def _get_session(self) -> aiohttp.ClientSession:
        """获取或创建 HTTP 会话"""
        # 确保 token 有效
        await self._ensure_valid_token()

        if self._session is None or self._session.closed:
            headers = {
                "Content-Type": "application/json",
                "X-API-Key": self.config.api_token,  # LLM API Key
            }
            # 如果有 access_token，添加 JWT 认证
            if self.config.access_token:
                headers["Authorization"] = f"Bearer {self.config.access_token}"

            self._session = aiohttp.ClientSession(
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=self.config.timeout_seconds),
            )
        return self._session

    async def _get_default_model(self, model_type: ModelType = ModelType.TEXT) -> str:
        """
        获取默认模型（动态从云端获取，按优先级排序）

        Args:
            model_type: 模型类型，默认为 TEXT

        Returns:
            str: 模型 ID
        """
        # 如果有缓存，直接返回
        if self._default_model_cache:
            return self._default_model_cache

        # 从云端获取优先级最高的模型
        model_info = await self.get_model_by_type(model_type)
        if model_info:
            self._default_model_cache = model_info.model_id
            return model_info.model_id

        # 回退到配置文件中的默认模型
        return self.config.default_model

    async def chat(
        self,
        messages: List[LLMMessage],
        *,
        model: Optional[str] = None,
        system: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        user_id: Optional[str] = None,
    ) -> LLMResponse:
        """
        发送对话请求 (OpenAI 兼容格式)

        Args:
            messages: 对话消息列表
            model: 模型名称（不传则动态获取优先级最高的模型）
            system: 系统提示
            tools: 工具定义列表 (OpenAI 格式)
            max_tokens: 最大生成 tokens
            temperature: 温度参数
            user_id: 用户ID

        Returns:
            LLMResponse: 响应结果
        """
        session = await self._get_session()

        # 动态获取模型（如果未指定）
        use_model = model or await self._get_default_model()

        # 构建消息
        api_messages = []
        if system:
            api_messages.append({"role": "system", "content": system})
        for msg in messages:
            m = {"role": msg.role, "content": msg.content}
            if msg.name:
                m["name"] = msg.name
            if msg.tool_calls:
                m["tool_calls"] = msg.tool_calls
            if msg.tool_call_id:
                m["tool_call_id"] = msg.tool_call_id
            api_messages.append(m)

        # 构建请求体
        payload = {
            "model": use_model,
            "messages": api_messages,
            "max_tokens": max_tokens or self.config.default_max_tokens,
            "temperature": temperature if temperature is not None else self.config.default_temperature,
            "stream": False,
        }
        
        if tools:
            payload["tools"] = tools
            
        if user_id:
            payload["user"] = user_id

        # 发送请求
        url = f"{self.config.base_url}/api/v1/llm/proxy/v1/chat/completions"

        async with session.post(url, json=payload) as response:
            if response.status != 200:
                error = await response.text()
                raise LLMError(f"LLM request failed: {response.status} - {error}")

            data = await response.json()

        # 解析响应
        choice = data["choices"][0]
        usage = data.get("usage", {})

        return LLMResponse(
            content=choice["message"].get("content") or "",
            model=data.get("model", use_model),
            provider="cloud",
            usage=LLMUsage(
                input_tokens=usage.get("prompt_tokens", 0),
                output_tokens=usage.get("completion_tokens", 0),
                total_tokens=usage.get("total_tokens", 0),
            ),
            finish_reason=choice.get("finish_reason", "stop"),
            tool_calls=choice["message"].get("tool_calls"),
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
        流式对话请求

        Args:
            messages: 对话消息列表
            model: 模型名称（不传则动态获取优先级最高的模型）
            system: 系统提示
            max_tokens: 最大生成 tokens
            temperature: 温度参数
            user_id: 用户ID

        Yields:
            str: 逐字返回的内容片段
        """
        session = await self._get_session()

        # 动态获取模型（如果未指定）
        use_model = model or await self._get_default_model()

        api_messages = []
        if system:
            api_messages.append({"role": "system", "content": system})
        for msg in messages:
            api_messages.append({"role": msg.role, "content": msg.content})

        payload = {
            "model": use_model,
            "messages": api_messages,
            "max_tokens": max_tokens or self.config.default_max_tokens,
            "temperature": temperature if temperature is not None else self.config.default_temperature,
            "stream": True,
        }
        if user_id:
            payload["user"] = user_id

        url = f"{self.config.base_url}/api/v1/llm/proxy/v1/chat/completions"

        async with session.post(url, json=payload) as response:
            if response.status != 200:
                error = await response.text()
                raise LLMError(f"LLM stream request failed: {response.status}")

            async for line in response.content:
                line = line.decode("utf-8").strip()
                if not line or line == "data: [DONE]":
                    continue
                if line.startswith("data: "):
                    try:
                        data = json.loads(line[6:])
                        choices = data.get("choices", [])
                        if choices:
                            delta = choices[0].get("delta", {})
                            if "content" in delta:
                                yield delta["content"]
                    except json.JSONDecodeError:
                        continue

    async def get_available_models(self) -> List[ModelInfo]:
        """
        获取可用模型列表

        Returns:
            List[ModelInfo]: 模型信息列表
        """
        session = await self._get_session()
        url = f"{self.config.base_url}/api/v1/llm/models/available"

        try:
            async with session.get(url) as response:
                if response.status != 200:
                    return []
                data = await response.json()

            # 从 response.data.models 中提取模型列表
            models_data = data.get("data", {}).get("models", [])
            return [
                ModelInfo(
                    model_id=m["model_id"],
                    provider=LLMProvider(m.get("provider", "openai")),
                    display_name=m.get("display_name", m["model_id"]),
                    max_tokens=m.get("max_tokens", 4096),
                    model_type=ModelType(m.get("model_type", "TEXT")),
                    supports_streaming=m.get("supports_streaming", True),
                    supports_vision=m.get("supports_vision", False),
                    priority=m.get("priority", 0),
                    enabled=m.get("enabled", True),
                )
                for m in models_data
                if m.get("enabled", True)
            ]
        except Exception:
            return []

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
        获取用量汇总

        Args:
            user_id: 用户ID
            period: 统计周期 (day, week, month)

        Returns:
            dict: 用量统计数据
        """
        session = await self._get_session()
        url = f"{self.config.base_url}/api/v1/llm/usage/summary"
        params = {"period": period}

        try:
            async with session.get(url, params=params) as response:
                if response.status != 200:
                    return {}
                return await response.json()
        except Exception:
            return {}

    async def health_check(self) -> bool:
        """
        健康检查

        Returns:
            bool: 网关是否可用
        """
        try:
            session = await self._get_session()
            url = f"{self.config.base_url}/health"
            async with session.get(url) as response:
                return response.status == 200
        except Exception:
            return False

    async def close(self):
        """关闭 HTTP 会话"""
        if self._session and not self._session.closed:
            await self._session.close()
