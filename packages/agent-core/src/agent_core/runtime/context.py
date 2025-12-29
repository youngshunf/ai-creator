"""
运行时上下文 - 管理执行环境信息
@author Ysf
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, TYPE_CHECKING

from .interfaces import RuntimeType

if TYPE_CHECKING:
    from ..resource.resolver import AssetResolver
    from ..llm.interface import LLMClientInterface, ModelInfo, ModelType


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

    # 模型配置 (作为后备，优先从 LLM 客户端动态获取)
    # 默认值为空，由调用方动态设置
    model_default: str = ""
    model_fast: str = ""

    # API 密钥 (运行时注入，不持久化)
    api_keys: Dict[str, str] = field(default_factory=dict)

    # LLM 客户端 (用于动态获取模型)
    llm_client: Optional["LLMClientInterface"] = None

    # 资源解析器
    asset_resolver: Optional["AssetResolver"] = None

    # 额外上下文 (端/云特有配置)
    extra: Dict[str, Any] = field(default_factory=dict)

    # 追踪标识
    trace_id: str = ""
    run_id: str = ""

    # 设备类型 (可选)
    device_type: Optional[str] = None

    # 模型缓存 (避免重复请求)
    _model_cache: Dict[str, "ModelInfo"] = field(default_factory=dict)

    # -------------------------------------------------------------------------
    # Skill Integration Fields
    # -------------------------------------------------------------------------
    
    # 动态挂载的工具名称列表 (由 SkillManager 注入)
    required_tools: list[str] = field(default_factory=list)

    # 注入的系统提示词片段 (由 SkillManager 注入)
    system_prompts: list[str] = field(default_factory=list)

    # 注入的 Few-Shot 示例 (由 SkillManager 注入)
    few_shot_examples: list[dict[str, Any]] = field(default_factory=list)

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

    async def get_model(self, model_type: "ModelType") -> Optional[str]:
        """
        按类型获取模型 ID

        优先从 LLM 客户端动态获取，失败时使用后备配置

        Args:
            model_type: 模型类型 (TEXT/REASONING/VISION 等)

        Returns:
            模型 ID
        """
        from ..llm.interface import ModelType as MT

        # 检查缓存
        cache_key = model_type.value
        if cache_key in self._model_cache:
            return self._model_cache[cache_key].model_id

        # 尝试从 LLM 客户端获取
        if self.llm_client:
            try:
                model_info = await self.llm_client.get_model_by_type(model_type)
                if model_info:
                    self._model_cache[cache_key] = model_info
                    return model_info.model_id
            except Exception:
                pass

        # 使用后备配置
        # TEXT 类型使用 model_fast，REASONING 类型使用 model_default
        if model_type == MT.TEXT:
            return self.model_fast
        return self.model_default
