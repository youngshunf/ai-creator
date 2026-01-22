"""
平台适配器模块

提供所有平台适配器的统一导出和注册表。

@author Ysf
@date 2026-01-22
"""

from typing import Dict, Type, Optional

from .xiaohongshu import XiaohongshuAdapter
from .douyin import DouyinAdapter
from .bilibili import BilibiliAdapter
from .wechat import WechatAdapter

# 导入基类和模型用于重导出
from ..adapter import PlatformAdapter
from ..models import (
    ContentSpec,
    AdaptedContent,
    PublishContent,
    LoginResult,
    UserProfile,
    PublishResult,
)

# 平台适配器注册表
PLATFORM_ADAPTERS: Dict[str, Type[PlatformAdapter]] = {
    "xiaohongshu": XiaohongshuAdapter,
    "douyin": DouyinAdapter,
    "bilibili": BilibiliAdapter,
    "wechat": WechatAdapter,
}

# 平台名称别名
PLATFORM_ALIASES: Dict[str, str] = {
    "xhs": "xiaohongshu",
    "小红书": "xiaohongshu",
    "抖音": "douyin",
    "dy": "douyin",
    "b站": "bilibili",
    "bili": "bilibili",
    "哔哩哔哩": "bilibili",
    "微信": "wechat",
    "微信公众号": "wechat",
    "公众号": "wechat",
    "weixin": "wechat",
}


def get_adapter(platform_name: str) -> Optional[PlatformAdapter]:
    """
    获取平台适配器实例
    
    Args:
        platform_name: 平台名称或别名
        
    Returns:
        平台适配器实例，不存在返回 None
    """
    # 规范化名称
    name = platform_name.lower().strip()
    
    # 检查别名
    if name in PLATFORM_ALIASES:
        name = PLATFORM_ALIASES[name]
    
    # 获取适配器类
    adapter_class = PLATFORM_ADAPTERS.get(name)
    if adapter_class:
        return adapter_class()
    
    return None


def get_adapter_class(platform_name: str) -> Optional[Type[PlatformAdapter]]:
    """
    获取平台适配器类
    
    Args:
        platform_name: 平台名称或别名
        
    Returns:
        平台适配器类，不存在返回 None
    """
    name = platform_name.lower().strip()
    if name in PLATFORM_ALIASES:
        name = PLATFORM_ALIASES[name]
    return PLATFORM_ADAPTERS.get(name)


def list_platforms() -> list[str]:
    """
    列出所有支持的平台
    
    Returns:
        平台名称列表
    """
    return list(PLATFORM_ADAPTERS.keys())


def register_adapter(name: str, adapter_class: Type[PlatformAdapter]) -> None:
    """
    注册新的平台适配器
    
    Args:
        name: 平台名称
        adapter_class: 适配器类
    """
    PLATFORM_ADAPTERS[name.lower()] = adapter_class


__all__ = [
    # 具体适配器
    "XiaohongshuAdapter",
    "DouyinAdapter",
    "BilibiliAdapter",
    "WechatAdapter",
    # 基类
    "PlatformAdapter",
    # 数据模型
    "ContentSpec",
    "AdaptedContent",
    "PublishContent",
    "LoginResult",
    "UserProfile",
    "PublishResult",
    # 注册表
    "PLATFORM_ADAPTERS",
    "PLATFORM_ALIASES",
    # 工具函数
    "get_adapter",
    "get_adapter_class",
    "list_platforms",
    "register_adapter",
]
