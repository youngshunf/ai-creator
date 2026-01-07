"""
平台适配器模块
@author Ysf
"""

from .base import PlatformAdapter, AdaptedContent, ContentSpec, LoginResult, UserProfile
from .xiaohongshu import XiaohongshuAdapter
from .wechat import WechatAdapter
from .douyin import DouyinAdapter

# 平台适配器注册表
PLATFORM_ADAPTERS: dict[str, type[PlatformAdapter]] = {
    "xiaohongshu": XiaohongshuAdapter,
    "wechat": WechatAdapter,
    "douyin": DouyinAdapter,
}


def get_adapter(platform: str) -> PlatformAdapter:
    """获取平台适配器实例"""
    adapter_class = PLATFORM_ADAPTERS.get(platform)
    if not adapter_class:
        raise ValueError(f"Unsupported platform: {platform}")
    return adapter_class()


__all__ = [
    "PlatformAdapter",
    "AdaptedContent",
    "ContentSpec",
    "LoginResult",
    "UserProfile",
    "XiaohongshuAdapter",
    "WechatAdapter",
    "DouyinAdapter",
    "get_adapter",
    "PLATFORM_ADAPTERS",
]
