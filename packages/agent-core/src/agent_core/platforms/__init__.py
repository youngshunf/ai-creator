"""
Platforms 模块 - 平台适配器统一导出

本模块整合了平台适配器实现：
- 新版 (adapter.py + models.py): 基于 YAML 配置的实现
- 旧版 (base.py): 基于 dataclass 的实现，向后兼容

推荐使用新版 API:
- PlatformAdapter, ContentSpec, AdaptedContent 等 (from adapter.py, models.py)
- ConfigLoader, PlatformConfig (from config/)
- get_adapter(), PLATFORM_ADAPTERS (from adapters/)

@author Ysf
@date 2026-01-22
"""

# ========== 新版统一模块 ==========

# 统一数据模型
from .models import (
    ContentType,
    ContentSpec,
    AdaptedContent,
    PublishContent,
    LoginResult,
    UserProfile,
    PublishResult,
    # 兼容别名
    ContentConstraints,
)

# 统一基类
from .adapter import PlatformAdapter

# 配置模块
from .config import (
    ConfigLoader,
    PlatformConfig,
    PlatformInfo,
    PlatformUrls,
    PlatformConstraints,
    PlatformSelectors,
    LoginDetection,
    ConfigError,
)

# ========== 新版平台适配器 ==========

from .adapters import (
    # 具体适配器
    XiaohongshuAdapter,
    DouyinAdapter,
    BilibiliAdapter,
    WechatAdapter,
    # 注册表和工具函数
    PLATFORM_ADAPTERS,
    PLATFORM_ALIASES,
    get_adapter,
    get_adapter_class,
    list_platforms,
    register_adapter,
)

# ========== 旧版兼容模块 ==========

# 旧版基类（别名）
from .base import (
    PlatformType,
    PlatformAdapter as LegacyPlatformAdapter,
    PlatformRegistry,
)

# 旧版适配器（保留用于兼容，后续删除）
try:
    from .xiaohongshu import XiaohongshuAdapter as LegacyXiaohongshuAdapter
    from .wechat_mp import WeChatMPAdapter
    from .weibo import WeiboAdapter as LegacyWeiboAdapter
    from .douyin import DouyinAdapter as LegacyDouyinAdapter
    from .bilibili import BilibiliAdapter as LegacyBilibiliAdapter
except ImportError:
    # 旧版适配器可能已删除
    LegacyXiaohongshuAdapter = None
    WeChatMPAdapter = None
    LegacyWeiboAdapter = None
    LegacyDouyinAdapter = None
    LegacyBilibiliAdapter = None

__all__ = [
    # 新版核心
    "PlatformAdapter",
    "ContentSpec",
    "AdaptedContent",
    "PublishContent",
    "LoginResult",
    "UserProfile",
    "PublishResult",
    "ContentType",
    # 配置模块
    "ConfigLoader",
    "PlatformConfig",
    "PlatformInfo",
    "PlatformUrls",
    "PlatformConstraints",
    "PlatformSelectors",
    "LoginDetection",
    "ConfigError",
    # 新版适配器
    "XiaohongshuAdapter",
    "DouyinAdapter",
    "BilibiliAdapter",
    "WechatAdapter",
    # 注册表和工具函数
    "PLATFORM_ADAPTERS",
    "PLATFORM_ALIASES",
    "get_adapter",
    "get_adapter_class",
    "list_platforms",
    "register_adapter",
    # 旧版兼容
    "PlatformType",
    "ContentConstraints",
    "LegacyPlatformAdapter",
    "PlatformRegistry",
    "WeChatMPAdapter",  # 旧版微信适配器
]
