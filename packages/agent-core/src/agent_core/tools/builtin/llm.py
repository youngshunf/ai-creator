"""
LLM 生成工具 - 使用 Anthropic API 生成文本
@author Ysf
"""

from typing import Optional

import anthropic

from ..base import (
    ToolInterface,
    ToolMetadata,
    ToolResult,
    ToolCapability,
    ToolExecutionError,
)
from ...runtime.interfaces import RuntimeType
from ...runtime.context import RuntimeContext


class LLMGenerateTool(ToolInterface):
    """
    LLM 文本生成工具

    使用 Anthropic Claude API 生成文本。
    支持本地和云端运行环境。
    """

    metadata = ToolMetadata(
        name="llm_generate",
        description="使用 LLM 生成文本",
        capabilities=[ToolCapability.LLM_GENERATE],
        supported_runtimes=[RuntimeType.LOCAL, RuntimeType.CLOUD],
    )

    def __init__(self):
        """初始化工具"""
        self._client: Optional[anthropic.AsyncAnthropic] = None

    async def execute(self, ctx: RuntimeContext, **kwargs) -> ToolResult:
        """
        执行 LLM 文本生成

        Args:
            ctx: 运行时上下文
            **kwargs: 工具参数
                - prompt (str): 提示词
                - model (str, optional): 模型名称
                - max_tokens (int, optional): 最大 token 数
                - temperature (float, optional): 温度参数
                - system (str, optional): 系统提示词

        Returns:
            ToolResult: 包含生成的文本

        Raises:
            ToolExecutionError: 执行失败
        """
        try:
            # 提取参数
            prompt = kwargs.get("prompt")
            if not prompt:
                raise ToolExecutionError("缺少必填参数: prompt")

            model = kwargs.get("model", ctx.model_default)
            max_tokens = kwargs.get("max_tokens", 2000)
            temperature = kwargs.get("temperature", 1.0)
            system = kwargs.get("system")

            # 获取 API 密钥
            api_key = ctx.get_api_key("anthropic")
            if not api_key:
                raise ToolExecutionError("未配置 Anthropic API 密钥")

            # 创建客户端
            client = anthropic.AsyncAnthropic(api_key=api_key)

            # 构建消息
            messages = [{"role": "user", "content": prompt}]

            # 调用 API
            kwargs_for_api = {
                "model": model,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": messages,
            }

            if system:
                kwargs_for_api["system"] = system

            response = await client.messages.create(**kwargs_for_api)

            # 提取文本
            content = response.content[0].text if response.content else ""

            # 返回结果
            return ToolResult(
                success=True,
                data={"content": content, "model": model},
                metadata={
                    "usage": {
                        "input_tokens": response.usage.input_tokens,
                        "output_tokens": response.usage.output_tokens,
                    },
                    "model": response.model,
                    "stop_reason": response.stop_reason,
                },
            )

        except anthropic.APIError as e:
            return ToolResult(
                success=False, data=None, error=f"Anthropic API 错误: {e}"
            )
        except Exception as e:
            return ToolResult(
                success=False, data=None, error=f"LLM 生成失败: {e}"
            )

    def get_schema(self) -> dict:
        """
        获取工具参数 Schema

        Returns:
            JSON Schema 定义
        """
        return {
            "type": "object",
            "properties": {
                "prompt": {
                    "type": "string",
                    "description": "输入提示词",
                },
                "model": {
                    "type": "string",
                    "description": "模型名称",
                    "default": "claude-sonnet-4-20250514",
                },
                "max_tokens": {
                    "type": "integer",
                    "description": "最大 token 数",
                    "default": 2000,
                    "minimum": 1,
                    "maximum": 8192,
                },
                "temperature": {
                    "type": "number",
                    "description": "温度参数（0-1）",
                    "default": 1.0,
                    "minimum": 0,
                    "maximum": 1,
                },
                "system": {
                    "type": "string",
                    "description": "系统提示词（可选）",
                },
            },
            "required": ["prompt"],
        }
