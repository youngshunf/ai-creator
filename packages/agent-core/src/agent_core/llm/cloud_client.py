"""
云端 LLM 客户端 - 桌面端/Sidecar 使用

通过 HTTP 调用云端 LLM 网关，支持 OpenAI 兼容格式。

@author Ysf
@date 2025-12-28
"""

import json
from typing import List, Optional, AsyncIterator

import aiohttp

from .interface import (
    LLMClientInterface,
    LLMConfig,
    LLMMessage,
    LLMResponse,
    LLMUsage,
    ModelInfo,
    LLMError,
    LLMProvider,
)


class CloudLLMClient(LLMClientInterface):
    """
    云端 LLM 客户端

    桌面端/Sidecar 使用，通过 HTTP 调用云端 LLM 网关。
    支持 OpenAI 兼容格式的 API。
    """

    def __init__(self, config: LLMConfig):
        """
        初始化云端 LLM 客户端

        Args:
            config: LLM 配置
        """
        self.config = config
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """获取或创建 HTTP 会话"""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                headers={
                    "Authorization": f"Bearer {self.config.api_token}",
                    "Content-Type": "application/json",
                },
                timeout=aiohttp.ClientTimeout(total=self.config.timeout_seconds),
            )
        return self._session

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
        发送对话请求 (OpenAI 兼容格式)

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
        session = await self._get_session()

        # 构建消息
        api_messages = []
        if system:
            api_messages.append({"role": "system", "content": system})
        for msg in messages:
            api_messages.append({"role": msg.role, "content": msg.content})

        # 构建请求体
        payload = {
            "model": model or self.config.default_model,
            "messages": api_messages,
            "max_tokens": max_tokens or self.config.default_max_tokens,
            "temperature": temperature if temperature is not None else self.config.default_temperature,
            "stream": False,
        }
        if user_id:
            payload["user"] = user_id

        # 发送请求
        url = f"{self.config.base_url}/v1/chat/completions"

        async with session.post(url, json=payload) as response:
            if response.status != 200:
                error = await response.text()
                raise LLMError(f"LLM request failed: {response.status} - {error}")

            data = await response.json()

        # 解析响应
        choice = data["choices"][0]
        usage = data.get("usage", {})

        return LLMResponse(
            content=choice["message"]["content"],
            model=data.get("model", model or self.config.default_model),
            provider="cloud",
            usage=LLMUsage(
                input_tokens=usage.get("prompt_tokens", 0),
                output_tokens=usage.get("completion_tokens", 0),
                total_tokens=usage.get("total_tokens", 0),
            ),
            finish_reason=choice.get("finish_reason", "stop"),
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
            model: 模型名称
            system: 系统提示
            max_tokens: 最大生成 tokens
            temperature: 温度参数
            user_id: 用户ID

        Yields:
            str: 逐字返回的内容片段
        """
        session = await self._get_session()

        api_messages = []
        if system:
            api_messages.append({"role": "system", "content": system})
        for msg in messages:
            api_messages.append({"role": msg.role, "content": msg.content})

        payload = {
            "model": model or self.config.default_model,
            "messages": api_messages,
            "max_tokens": max_tokens or self.config.default_max_tokens,
            "temperature": temperature if temperature is not None else self.config.default_temperature,
            "stream": True,
        }
        if user_id:
            payload["user"] = user_id

        url = f"{self.config.base_url}/v1/chat/completions"

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
        url = f"{self.config.base_url}/api/v1/llm/models"

        try:
            async with session.get(url) as response:
                if response.status != 200:
                    return []
                data = await response.json()

            return [
                ModelInfo(
                    model_id=m["model_id"],
                    provider=LLMProvider(m.get("provider", "openai")),
                    display_name=m.get("display_name", m["model_id"]),
                    max_tokens=m.get("max_tokens", 4096),
                    supports_streaming=m.get("supports_streaming", True),
                    supports_vision=m.get("supports_vision", False),
                )
                for m in data.get("models", [])
            ]
        except Exception:
            return []

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
