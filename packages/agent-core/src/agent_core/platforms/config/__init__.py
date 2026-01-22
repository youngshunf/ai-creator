"""
平台配置模块

提供平台配置的 Schema 定义和加载器。

@author Ysf
@date 2026-01-22
"""

from .schema import (
    PlatformConfig,
    PlatformInfo,
    PlatformUrls,
    ContentLimits,
    ImageConstraints,
    VideoConstraints,
    HashtagConstraints,
    PlatformConstraints,
    PlatformSelectors,
    LoginDetection,
    UserIdExtraction,
)
from .loader import ConfigLoader, ConfigError

__all__ = [
    # Schema
    "PlatformConfig",
    "PlatformInfo",
    "PlatformUrls",
    "ContentLimits",
    "ImageConstraints",
    "VideoConstraints",
    "HashtagConstraints",
    "PlatformConstraints",
    "PlatformSelectors",
    "LoginDetection",
    "UserIdExtraction",
    # Loader
    "ConfigLoader",
    "ConfigError",
]
