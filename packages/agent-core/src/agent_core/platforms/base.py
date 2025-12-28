"""
平台适配器基类 - 定义平台发布接口
@author Ysf
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, ClassVar
from enum import Enum


class PlatformType(str, Enum):
    """平台类型"""

    XIAOHONGSHU = "xiaohongshu"  # 小红书
    DOUYIN = "douyin"  # 抖音
    WEIXIN = "weixin"  # 微信公众号
    WEIBO = "weibo"  # 微博
    BILIBILI = "bilibili"  # B站
    ZHIHU = "zhihu"  # 知乎
    TOUTIAO = "toutiao"  # 头条号
    KUAISHOU = "kuaishou"  # 快手


class ContentType(str, Enum):
    """内容类型"""

    TEXT = "text"  # 纯文本
    IMAGE_TEXT = "image_text"  # 图文
    VIDEO = "video"  # 视频
    LIVE = "live"  # 直播
    STORY = "story"  # 快拍/故事


@dataclass
class ContentConstraints:
    """
    平台内容约束

    定义各平台对内容格式的限制。
    """

    # 标题限制
    max_title_length: int = 100
    min_title_length: int = 0
    title_required: bool = False

    # 正文限制
    max_content_length: int = 20000
    min_content_length: int = 1

    # 图片限制
    max_images: int = 9
    min_images: int = 0
    max_image_size_mb: float = 20.0
    allowed_image_formats: List[str] = field(
        default_factory=lambda: ["jpg", "jpeg", "png", "gif", "webp"]
    )
    image_aspect_ratio: Optional[str] = None  # 如 "1:1", "3:4"

    # 视频限制
    max_video_duration: int = 600  # 秒
    max_video_size_mb: float = 500.0
    allowed_video_formats: List[str] = field(
        default_factory=lambda: ["mp4", "mov", "avi"]
    )

    # 标签限制
    max_hashtags: int = 10
    max_mentions: int = 10

    # 链接限制
    allow_external_links: bool = True
    allow_internal_links: bool = True

    # 内容类型
    supported_content_types: List[ContentType] = field(
        default_factory=lambda: [ContentType.TEXT, ContentType.IMAGE_TEXT]
    )


@dataclass
class PublishResult:
    """
    发布结果

    封装内容发布的返回信息。
    """

    # 是否成功
    success: bool

    # 发布后的内容 ID
    post_id: Optional[str] = None

    # 发布后的 URL
    url: Optional[str] = None

    # 错误信息
    error: Optional[str] = None

    # 错误代码
    error_code: Optional[str] = None

    # 平台返回的原始响应
    raw_response: Optional[Dict[str, Any]] = None

    # 发布时间戳
    published_at: Optional[str] = None

    # 额外元数据
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PublishContent:
    """
    待发布的内容

    统一的内容数据结构。
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


class PlatformAdapter(ABC):
    """
    平台适配器抽象基类

    定义与内容平台交互的通用接口，包括：
    - 内容发布
    - 内容约束获取
    - 内容格式适配
    - 登录状态验证
    - 内容草稿管理

    子类需要实现具体平台的逻辑。

    使用示例:
        class XiaohongshuAdapter(PlatformAdapter):
            platform_type = PlatformType.XIAOHONGSHU
            platform_name = "xiaohongshu"
            platform_display_name = "小红书"

            async def publish(self, page, content):
                # 实现小红书发布逻辑
                pass

            async def get_content_constraints(self):
                return ContentConstraints(
                    max_title_length=20,
                    max_content_length=1000,
                    max_images=9,
                )

            def adapt_content(self, content):
                # 适配内容格式
                pass
    """

    # 平台类型（子类必须定义）
    platform_type: ClassVar[PlatformType]

    # 平台标识名（如 "xiaohongshu"）
    platform_name: ClassVar[str]

    # 平台显示名（如 "小红书"）
    platform_display_name: ClassVar[str]

    # 平台 URL
    platform_url: ClassVar[str] = ""

    # 是否需要登录
    requires_login: ClassVar[bool] = True

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化平台适配器

        Args:
            config: 平台配置
        """
        self.config = config or {}

    @abstractmethod
    async def publish(
        self,
        page: Any,  # Playwright Page 对象
        content: PublishContent,
    ) -> PublishResult:
        """
        发布内容到平台

        Args:
            page: Playwright 浏览器页面对象
            content: 待发布的内容

        Returns:
            PublishResult: 发布结果
        """
        pass

    @abstractmethod
    async def get_content_constraints(self) -> ContentConstraints:
        """
        获取平台内容约束

        Returns:
            ContentConstraints: 内容约束配置
        """
        pass

    @abstractmethod
    def adapt_content(self, content: PublishContent) -> PublishContent:
        """
        适配内容到平台规范

        根据平台规范调整内容格式，如：
        - 截断过长的标题/正文
        - 转换图片格式
        - 添加平台特定标记

        Args:
            content: 原始内容

        Returns:
            PublishContent: 适配后的内容
        """
        pass

    @abstractmethod
    async def verify_login(self, page: Any) -> bool:
        """
        验证登录状态

        Args:
            page: Playwright 浏览器页面对象

        Returns:
            True 表示已登录，False 表示未登录
        """
        pass

    async def save_draft(
        self,
        page: Any,
        content: PublishContent,
    ) -> PublishResult:
        """
        保存为草稿

        默认实现：不支持草稿，返回错误。
        子类可以覆盖此方法实现草稿功能。

        Args:
            page: Playwright 浏览器页面对象
            content: 待保存的内容

        Returns:
            PublishResult: 保存结果
        """
        return PublishResult(
            success=False,
            error="该平台不支持草稿功能",
            error_code="DRAFT_NOT_SUPPORTED",
        )

    async def delete_content(
        self,
        page: Any,
        post_id: str,
    ) -> bool:
        """
        删除已发布的内容

        默认实现：不支持删除，返回 False。
        子类可以覆盖此方法实现删除功能。

        Args:
            page: Playwright 浏览器页面对象
            post_id: 内容 ID

        Returns:
            True 表示删除成功，False 表示失败
        """
        return False

    async def get_publish_url(self) -> str:
        """
        获取发布页面 URL

        Returns:
            发布页面的 URL
        """
        return self.platform_url

    def validate_content(self, content: PublishContent) -> List[str]:
        """
        验证内容是否符合平台规范

        Args:
            content: 待验证的内容

        Returns:
            错误信息列表，空列表表示验证通过
        """
        errors = []

        # 子类可以调用父类方法后添加自定义验证
        # 这里提供基础验证逻辑

        return errors

    async def upload_image(
        self,
        page: Any,
        image_path: str,
    ) -> Optional[str]:
        """
        上传图片到平台

        默认实现：返回 None。
        子类可以覆盖此方法实现图片上传。

        Args:
            page: Playwright 浏览器页面对象
            image_path: 本地图片路径

        Returns:
            上传后的图片 URL，失败返回 None
        """
        return None

    async def upload_video(
        self,
        page: Any,
        video_path: str,
    ) -> Optional[str]:
        """
        上传视频到平台

        默认实现：返回 None。
        子类可以覆盖此方法实现视频上传。

        Args:
            page: Playwright 浏览器页面对象
            video_path: 本地视频路径

        Returns:
            上传后的视频 URL，失败返回 None
        """
        return None

    def get_platform_info(self) -> Dict[str, Any]:
        """
        获取平台信息

        Returns:
            平台信息字典
        """
        return {
            "type": self.platform_type.value,
            "name": self.platform_name,
            "display_name": self.platform_display_name,
            "url": self.platform_url,
            "requires_login": self.requires_login,
        }


class PlatformRegistry:
    """
    平台适配器注册表

    管理所有已注册的平台适配器。
    """

    _adapters: Dict[str, type] = {}

    @classmethod
    def register(cls, adapter_class: type) -> type:
        """
        注册平台适配器

        可作为装饰器使用:
            @PlatformRegistry.register
            class XiaohongshuAdapter(PlatformAdapter):
                ...

        Args:
            adapter_class: 平台适配器类

        Returns:
            注册的类（用于装饰器）
        """
        cls._adapters[adapter_class.platform_name] = adapter_class
        return adapter_class

    @classmethod
    def get(cls, platform_name: str) -> Optional[type]:
        """
        获取平台适配器类

        Args:
            platform_name: 平台名称

        Returns:
            平台适配器类，不存在则返回 None
        """
        return cls._adapters.get(platform_name)

    @classmethod
    def create(
        cls,
        platform_name: str,
        config: Optional[Dict[str, Any]] = None,
    ) -> Optional[PlatformAdapter]:
        """
        创建平台适配器实例

        Args:
            platform_name: 平台名称
            config: 平台配置

        Returns:
            平台适配器实例，不存在则返回 None
        """
        adapter_class = cls.get(platform_name)
        if adapter_class:
            return adapter_class(config)
        return None

    @classmethod
    def list_platforms(cls) -> List[str]:
        """
        列出所有已注册的平台

        Returns:
            平台名称列表
        """
        return list(cls._adapters.keys())

    @classmethod
    def get_all_info(cls) -> List[Dict[str, Any]]:
        """
        获取所有平台信息

        Returns:
            平台信息列表
        """
        infos = []
        for name, adapter_class in cls._adapters.items():
            infos.append({
                "type": adapter_class.platform_type.value,
                "name": adapter_class.platform_name,
                "display_name": adapter_class.platform_display_name,
                "url": adapter_class.platform_url,
                "requires_login": adapter_class.requires_login,
            })
        return infos
