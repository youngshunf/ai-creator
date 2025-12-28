"""
Platforms 模块 - 平台适配器
@author Ysf
"""

from .base import (
    PlatformType,
    ContentType,
    ContentConstraints,
    PublishResult,
    PublishContent,
    PlatformAdapter,
    PlatformRegistry,
)
from .xiaohongshu import XiaohongshuAdapter
from .wechat_mp import WeChatMPAdapter
from .weibo import WeiboAdapter
from .douyin import DouyinAdapter
from .bilibili import BilibiliAdapter

__all__ = [
    "PlatformType",
    "ContentType",
    "ContentConstraints",
    "PublishResult",
    "PublishContent",
    "PlatformAdapter",
    "PlatformRegistry",
    "XiaohongshuAdapter",
    "WeChatMPAdapter",
    "WeiboAdapter",
    "DouyinAdapter",
    "BilibiliAdapter",
]
