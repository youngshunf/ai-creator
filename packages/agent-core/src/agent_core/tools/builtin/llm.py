"""
LLM 生成工具 - 通过 LLM 客户端生成文本
@author Ysf
"""

import logging
from typing import Optional

from ..base import (
    ToolInterface,
    ToolMetadata,
    ToolResult,
    ToolCapability,
    ToolExecutionError,
)
from ...runtime.interfaces import RuntimeType
from ...runtime.context import RuntimeContext
from ...llm.interface import LLMMessage, ModelType

logger = logging.getLogger(__name__)


class LLMGenerateTool(ToolInterface):
    """
    LLM 文本生成工具

    通过 LLM 客户端生成文本，支持动态模型选择。
    优先使用 LLM 客户端（通过网关），失败时回退到直接 API 调用。
    """

    metadata = ToolMetadata(
        name="llm_generate",
        description="使用 LLM 生成文本",
        capabilities=[ToolCapability.LLM_GENERATE],
        supported_runtimes=[RuntimeType.LOCAL, RuntimeType.CLOUD],
    )

    async def execute(self, ctx: RuntimeContext, **kwargs) -> ToolResult:
        """
        执行 LLM 文本生成

        Args:
            ctx: 运行时上下文
            **kwargs: 工具参数
                - prompt (str): 提示词
                - model (str, optional): 模型名称或模型类型 (fast/default/advanced)
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
            messages_history = kwargs.get("messages") # 历史消息
            
            if not prompt and not messages_history:
                raise ToolExecutionError("必须提供 prompt 或 messages")

            model_param = kwargs.get("model")
            max_tokens = kwargs.get("max_tokens", 2000)
            temperature = kwargs.get("temperature", 0.7)
            system = kwargs.get("system")

            # 合并 Skill 注入的 System Prompts
            skill_system = "\n\n".join(getattr(ctx, "system_prompts", []))
            if skill_system:
                if system:
                    system = f"{skill_system}\n\n{system}"
                else:
                    system = skill_system

            # 解析模型参数 - 支持模型类型或具体模型名
            model = await self._resolve_model(ctx, model_param)
            logger.info(f"[LLM] Model: {model}, max_tokens: {max_tokens}")
            logger.debug(f"[LLM] Prompt: {prompt[:200]}..." if prompt else "[LLM] No direct prompt, using messages history.")

            # 准备工具定义
            tools_def = []
            registry = ctx.extra.get("tool_registry")
            # ctx.required_tools 是 RuntimeContext 中新增的字段 (Phase 1)
            required_tools = getattr(ctx, "required_tools", [])
            
            if registry and required_tools:
                for tool_name in required_tools:
                    tool = registry.get_tool(tool_name)
                    if tool:
                        tools_def.append({
                            "type": "function",
                            "function": {
                                "name": tool.name,
                                "description": tool.description,
                                "parameters": tool.get_schema()
                            }
                        })

            # 优先使用 LLM 客户端
            if ctx.llm_client:
                return await self._execute_via_client(
                    ctx, prompt, model, max_tokens, temperature, system, tools_def, messages_history
                )

            # 回退到直接 API 调用
            return await self._execute_direct(
                ctx, prompt, model, max_tokens, temperature, system, tools_def, messages_history
            )

        except Exception as e:
            logger.error(f"[LLM] Generation failed: {e}")
            return ToolResult(
                success=False, data=None, error=f"LLM 生成失败: {e}"
            )

    async def _resolve_model(self, ctx: RuntimeContext, model_param: Optional[str]) -> str:
        """
        解析模型参数

        支持:
        - 模型类型: ${runtime.model_fast}, ${runtime.model_default}
        - 具体模型名: claude-sonnet-4-20250514
        - 模型类型字符串: TEXT, REASONING, VISION 等

        Args:
            ctx: 运行时上下文
            model_param: 模型参数

        Returns:
            具体模型名称
        """
        if not model_param:
            # 默认使用 TEXT 类型
            return await ctx.get_model(ModelType.TEXT) or ctx.model_default

        # 检查是否是模型类型
        model_type_map = {
            "TEXT": ModelType.TEXT,
            "REASONING": ModelType.REASONING,
            "VISION": ModelType.VISION,
            "IMAGE": ModelType.IMAGE,
            "VIDEO": ModelType.VIDEO,
            "EMBEDDING": ModelType.EMBEDDING,
            "TTS": ModelType.TTS,
            "STT": ModelType.STT,
        }

        upper_param = model_param.upper()
        if upper_param in model_type_map:
            model_type = model_type_map[upper_param]
            return await ctx.get_model(model_type) or ctx.model_default

        # 否则认为是具体模型名
        return model_param

    async def _execute_via_client(
        self,
        ctx: RuntimeContext,
        prompt: str,
        model: str,
        max_tokens: int,
        temperature: float,
        system: Optional[str],
        tools: Optional[list] = None,
        messages_history: Optional[list] = None,
    ) -> ToolResult:
        """通过 LLM 客户端执行"""
        logger.info(f"[LLM] Using LLM client, model={model}, tools={len(tools) if tools else 0}")

        # 构建消息列表
        messages = []
        if messages_history:
            for m in messages_history:
                if isinstance(m, dict):
                    messages.append(LLMMessage(role=m.get("role", "user"), content=m.get("content", "")))
                elif isinstance(m, LLMMessage):
                    messages.append(m)
                else:
                    messages.append(LLMMessage(role=getattr(m, "role", "user"), content=getattr(m, "content", "")))
        
        if prompt:
            messages.append(LLMMessage(role="user", content=prompt))

        response = await ctx.llm_client.chat(
            messages=messages,
            model=model,
            system=system,
            tools=tools,
            max_tokens=max_tokens,
            temperature=temperature,
            user_id=ctx.user_id,
        )

        logger.info(f"[LLM] Response received, tokens: input={response.usage.input_tokens}, output={response.usage.output_tokens}")

        # 构造 LLMMessage 对象
        message = LLMMessage(
            role="assistant",
            content=response.content,
            tool_calls=response.tool_calls
        )

        return ToolResult(
            success=True,
            data={
                "content": response.content,
                "model": response.model,
                "tool_calls": response.tool_calls,
                "message": message, # 返回完整的一条消息对象
            },
            metadata={
                "usage": {
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens,
                },
                "model": response.model,
                "finish_reason": response.finish_reason,
            },
        )

    async def _execute_direct(
        self,
        ctx: RuntimeContext,
        prompt: str,
        model: str,
        max_tokens: int,
        temperature: float,
        system: Optional[str],
        tools: Optional[list] = None,
        messages_history: Optional[list] = None,
    ) -> ToolResult:
        """直接调用 Anthropic API (回退方案)"""
        import anthropic

        logger.info(f"[LLM] Using direct API call, model={model}")

        api_key = ctx.get_api_key("anthropic")
        if not api_key:
            logger.error("[LLM] No Anthropic API key configured")
            raise ToolExecutionError("未配置 Anthropic API 密钥")

        logger.info(f"[LLM] API key found (length={len(api_key)})")

        client = anthropic.AsyncAnthropic(api_key=api_key)
        client = anthropic.AsyncAnthropic(api_key=api_key)
        
        messages = []
        if messages_history:
             # assume messages_history are objects, need to convert to dicts if anthropic client requires
             # But here we are in direct executor, inputs are passed from execute(). 
             # execute() passes what it got. If it got dicts, fine. 
             # CloudLLMClient converts objects. Anthropic client needs dicts.
             for m in messages_history:
                 if isinstance(m, dict):
                     messages.append(m)
                 else:
                     # Assume LLMMessage
                     messages.append({"role": m.role, "content": m.content}) # simplified
        
        if prompt:
            messages.append({"role": "user", "content": prompt})

        kwargs_for_api = {
            "model": model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": messages,
        }

        if tools:
            kwargs_for_api["tools"] = tools

        if system:
            kwargs_for_api["system"] = system

        logger.info(f"[LLM] Calling Anthropic API...")
        response = await client.messages.create(**kwargs_for_api)

        content = response.content[0].text if response.content else ""
        logger.info(f"[LLM] Response received, tokens: input={response.usage.input_tokens}, output={response.usage.output_tokens}")

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
                "messages": {
                    "type": "array",
                    "description": "历史消息列表（可选）",
                    "items": {"type": "object"}
                },
            },
            "required": [],
        }
