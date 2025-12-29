"""
LLM 统一接口模块

提供端云统一的 LLM 调用接口。

@author Ysf
@date 2025-12-28
"""

from .interface import (
    LLMProvider,
    ModelType,
    ModelInfo,
    LLMMessage,
    LLMUsage,
    LLMResponse,
    LLMConfig,
    LLMClientInterface,
    LLMError,
)
from .config import LLMConfigManager
from .cloud_client import CloudLLMClient
from .direct_client import DirectLLMClient

__all__ = [
    # 接口定义
    "LLMProvider",
    "ModelType",
    "ModelInfo",
    "LLMMessage",
    "LLMUsage",
    "LLMResponse",
    "LLMConfig",
    "LLMClientInterface",
    "LLMError",
    # 配置管理
    "LLMConfigManager",
    # 客户端实现
    "CloudLLMClient",
    "DirectLLMClient",
]
