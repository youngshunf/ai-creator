"""
平台适配器统一数据模型

合并 sidecar 和 agent-core 两个版本的数据模型，
保持 sidecar 版本的命名风格（因为它是当前工作的版本）。

@author Ysf
@date 2026-01-22
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from enum import Enum

# 尝试导入配置模块（可能不可用）
try:
    from .config.schema import PlatformConstraints, PlatformConfig
    _CONFIG_AVAILABLE = True
except ImportError:
    _CONFIG_AVAILABLE = False
    PlatformConstraints = None
    PlatformConfig = None


class ContentType(str, Enum):
    """内容类型"""
    TEXT = "text"           # 纯文本
    IMAGE = "image"         # 图文
    IMAGE_TEXT = "image_text"  # 图文 (别名)
    VIDEO = "video"         # 视频
    ARTICLE = "article"     # 长文章
    LIVE = "live"           # 直播
    STORY = "story"         # 快拍/故事


@dataclass
class ContentSpec:
    """
    平台内容规范
    
    定义平台对内容格式的限制，用于内容适配和验证。
    这是 sidecar 版本的命名，同时包含 agent-core 版本的额外字段。
    
    使用示例:
        # 直接创建
        spec = ContentSpec(
            title_max_length=20,
            content_max_length=1000,
            image_max_count=9,
        )
        
        # 从配置加载
        spec = ContentSpec.from_config(platform_config.constraints)
    """
    # 标题限制
    title_max_length: int = 100
    title_min_length: int = 0
    title_required: bool = False
    
    # 正文限制
    content_max_length: int = 10000
    content_min_length: int = 0
    
    # 图片限制
    image_max_count: int = 9
    image_min_count: int = 0
    image_max_size_mb: float = 20.0
    image_formats: List[str] = field(default_factory=lambda: ["jpg", "jpeg", "png", "webp"])
    image_aspect_ratio: Optional[str] = None
    
    # 视频限制
    video_max_count: int = 1
    video_max_duration: int = 600  # 秒
    video_max_size_mb: float = 500.0
    video_formats: List[str] = field(default_factory=lambda: ["mp4", "mov"])
    
    # 标签限制
    hashtag_max_count: int = 20
    hashtag_format: str = "#{tag}"  # 标签格式模板
    
    # 提及限制
    mention_max_count: int = 10
    mention_supported: bool = True
    
    # 功能支持
    location_supported: bool = True
    schedule_supported: bool = True
    draft_supported: bool = True
    allow_external_links: bool = True
    allow_internal_links: bool = True
    
    # 支持的内容格式
    supported_formats: List[str] = field(default_factory=lambda: ["text", "image", "video"])
    
    @classmethod
    def from_config(cls, constraints: "PlatformConstraints") -> "ContentSpec":
        """
        从 PlatformConfig.constraints 创建 ContentSpec
        
        Args:
            constraints: 平台约束配置
            
        Returns:
            ContentSpec 实例
        """
        if not _CONFIG_AVAILABLE or constraints is None:
            return cls()
        
        return cls(
            # 标题
            title_max_length=constraints.title.max_length,
            title_min_length=constraints.title.min_length,
            title_required=constraints.title.required,
            # 正文
            content_max_length=constraints.content.max_length,
            content_min_length=constraints.content.min_length,
            # 图片
            image_max_count=constraints.images.max_count,
            image_min_count=constraints.images.min_count,
            image_max_size_mb=constraints.images.max_size_mb,
            image_formats=constraints.images.formats,
            image_aspect_ratio=constraints.images.aspect_ratio,
            # 视频
            video_max_count=constraints.video.max_count,
            video_max_duration=constraints.video.max_duration,
            video_max_size_mb=constraints.video.max_size_mb,
            video_formats=constraints.video.formats,
            # 标签
            hashtag_max_count=constraints.hashtags.max_count,
            hashtag_format=constraints.hashtags.format,
            # 提及
            mention_max_count=constraints.mentions.max_count,
            mention_supported=constraints.mentions.supported,
            # 功能
            location_supported=constraints.features.location_supported,
            schedule_supported=constraints.features.schedule_supported,
            draft_supported=constraints.features.draft_supported,
            allow_external_links=constraints.features.allow_external_links,
            allow_internal_links=constraints.features.allow_internal_links,
            # 支持的格式
            supported_formats=constraints.supported_formats,
        )


@dataclass
class AdaptedContent:
    """
    适配后的内容
    
    经过平台规范适配后的内容数据，用于发布。
    """
    title: str = ""
    content: str = ""
    images: List[str] = field(default_factory=list)
    videos: List[str] = field(default_factory=list)
    hashtags: List[str] = field(default_factory=list)
    mentions: List[str] = field(default_factory=list)
    cover_url: Optional[str] = None
    location: Optional[str] = None
    scheduled_at: Optional[str] = None  # ISO 格式时间
    visibility: str = "public"  # public/private/friends
    extra: Dict[str, Any] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)
    
    @classmethod
    def from_publish_content(cls, content: "PublishContent") -> "AdaptedContent":
        """从 PublishContent 转换"""
        return cls(
            title=content.title or "",
            content=content.content,
            images=content.images,
            videos=[content.video] if content.video else [],
            hashtags=content.hashtags,
            mentions=content.mentions,
            cover_url=content.cover_image,
            location=content.location,
            scheduled_at=content.scheduled_at,
            visibility=content.visibility,
            extra=content.platform_specific,
        )


@dataclass
class PublishContent:
    """
    待发布的内容
    
    统一的内容数据结构，用于传递给平台适配器。
    这是 agent-core 版本的命名，保留以兼容。
    """
    # 标题
    title: Optional[str] = None
    
    # 正文内容
    content: str = ""
    
    # 图片列表（URL 或本地路径）
    images: List[str] = field(default_factory=list)
    
    # 视频（URL 或本地路径）
    video: Optional[str] = None
    
    # 封面图
    cover_image: Optional[str] = None
    
    # 话题标签
    hashtags: List[str] = field(default_factory=list)
    
    # @提及用户
    mentions: List[str] = field(default_factory=list)
    
    # 位置信息
    location: Optional[str] = None
    
    # 定时发布时间（ISO 格式）
    scheduled_at: Optional[str] = None
    
    # 可见性设置
    visibility: str = "public"  # public/private/friends
    
    # 平台特定参数
    platform_specific: Dict[str, Any] = field(default_factory=dict)
    
    def to_adapted(self) -> AdaptedContent:
        """转换为 AdaptedContent"""
        return AdaptedContent.from_publish_content(self)


@dataclass
class LoginResult:
    """登录检测结果"""
    is_logged_in: bool
    platform_user_id: Optional[str] = None
    extra: Dict[str, Any] = field(default_factory=dict)


@dataclass
class UserProfile:
    """用户资料"""
    platform_user_id: str
    username: Optional[str] = None
    nickname: Optional[str] = None
    avatar_url: Optional[str] = None
    followers_count: Optional[int] = None
    following_count: Optional[int] = None
    posts_count: Optional[int] = None
    likes_count: Optional[int] = None
    bio: Optional[str] = None
    extra: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PublishResult:
    """发布结果"""
    success: bool
    platform_post_id: Optional[str] = None
    platform_post_url: Optional[str] = None
    error_message: Optional[str] = None
    error_code: Optional[str] = None
    published_at: Optional[str] = None
    raw_response: Optional[Dict[str, Any]] = None
    extra: Dict[str, Any] = field(default_factory=dict)
    
    # 兼容 agent-core 版本的字段名
    @property
    def post_id(self) -> Optional[str]:
        return self.platform_post_id
    
    @property
    def url(self) -> Optional[str]:
        return self.platform_post_url
    
    @property
    def error(self) -> Optional[str]:
        return self.error_message


# ============================================================
# 兼容别名 - 为 agent-core 旧版本提供向后兼容
# ============================================================

# ContentConstraints 是 agent-core 版本的命名
ContentConstraints = ContentSpec

# 用于类型检查的工厂函数
def create_content_spec(**kwargs) -> ContentSpec:
    """创建 ContentSpec 实例的工厂函数"""
    return ContentSpec(**kwargs)

def create_adapted_content(**kwargs) -> AdaptedContent:
    """创建 AdaptedContent 实例的工厂函数"""
    return AdaptedContent(**kwargs)

def create_publish_content(**kwargs) -> PublishContent:
    """创建 PublishContent 实例的工厂函数"""
    return PublishContent(**kwargs)
