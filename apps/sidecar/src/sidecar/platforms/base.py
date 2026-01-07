"""
平台适配器基类
@author Ysf
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class LoginResult:
    """登录检测结果"""
    is_logged_in: bool
    platform_user_id: Optional[str] = None
    extra: dict = field(default_factory=dict)


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
    extra: dict = field(default_factory=dict)


@dataclass
class ContentSpec:
    """平台内容规范"""
    title_max_length: int = 100
    title_min_length: int = 0
    content_max_length: int = 10000
    content_min_length: int = 0
    image_max_count: int = 9
    image_min_count: int = 0
    video_max_count: int = 1
    video_max_duration: int = 600  # 秒
    supported_formats: list[str] = field(default_factory=lambda: ["text", "image", "video"])
    hashtag_max_count: int = 20
    mention_supported: bool = True
    location_supported: bool = True


@dataclass
class AdaptedContent:
    """适配后的内容"""
    title: str
    content: str
    images: list[str] = field(default_factory=list)
    videos: list[str] = field(default_factory=list)
    hashtags: list[str] = field(default_factory=list)
    cover_url: Optional[str] = None
    extra: dict = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)


class PlatformAdapter(ABC):
    """平台适配器基类"""

    platform_name: str = ""
    platform_display_name: str = ""
    login_url: str = ""

    @property
    @abstractmethod
    def spec(self) -> ContentSpec:
        """获取平台内容规范"""
        pass

    def adapt_content(
        self,
        title: str,
        content: str,
        images: Optional[list[str]] = None,
        videos: Optional[list[str]] = None,
        hashtags: Optional[list[str]] = None,
    ) -> AdaptedContent:
        """适配内容到平台规范"""
        warnings = []
        images = images or []
        videos = videos or []
        hashtags = hashtags or []

        # 标题适配
        adapted_title = title
        if len(title) > self.spec.title_max_length:
            adapted_title = title[:self.spec.title_max_length - 3] + "..."
            warnings.append(f"标题超长，已截断至 {self.spec.title_max_length} 字符")

        # 正文适配
        adapted_content = content
        if len(content) > self.spec.content_max_length:
            adapted_content = content[:self.spec.content_max_length - 3] + "..."
            warnings.append(f"正文超长，已截断至 {self.spec.content_max_length} 字符")

        # 图片适配
        adapted_images = images[:self.spec.image_max_count]
        if len(images) > self.spec.image_max_count:
            warnings.append(f"图片数量超限，仅保留前 {self.spec.image_max_count} 张")

        # 视频适配
        adapted_videos = videos[:self.spec.video_max_count]
        if len(videos) > self.spec.video_max_count:
            warnings.append(f"视频数量超限，仅保留前 {self.spec.video_max_count} 个")

        # 话题标签适配
        adapted_hashtags = hashtags[:self.spec.hashtag_max_count]
        if len(hashtags) > self.spec.hashtag_max_count:
            warnings.append(f"话题标签超限，仅保留前 {self.spec.hashtag_max_count} 个")

        return AdaptedContent(
            title=adapted_title,
            content=adapted_content,
            images=adapted_images,
            videos=adapted_videos,
            hashtags=adapted_hashtags,
            warnings=warnings,
        )

    def validate_content(self, content: AdaptedContent) -> tuple[bool, list[str]]:
        """验证内容是否符合平台规范"""
        errors = []

        if len(content.title) < self.spec.title_min_length:
            errors.append(f"标题长度不足，最少需要 {self.spec.title_min_length} 字符")

        if len(content.content) < self.spec.content_min_length:
            errors.append(f"正文长度不足，最少需要 {self.spec.content_min_length} 字符")

        if len(content.images) < self.spec.image_min_count:
            errors.append(f"图片数量不足，最少需要 {self.spec.image_min_count} 张")

        return len(errors) == 0, errors

    def get_publish_prompt(self, content: AdaptedContent) -> str:
        """生成发布提示词（供 browser-use AI 使用）"""
        prompt = f"""请在 {self.platform_display_name} 发布以下内容：

标题：{content.title}

正文：
{content.content}
"""
        if content.hashtags:
            prompt += f"\n话题标签：{' '.join('#' + tag for tag in content.hashtags)}"

        if content.images:
            prompt += f"\n\n需要上传 {len(content.images)} 张图片"

        return prompt

    # ========== 登录检测方法 ==========

    async def check_login_status(
        self,
        cookies: list[dict],
        local_storage: dict[str, Any],
        current_url: str,
    ) -> LoginResult:
        """检测登录状态，子类应重写"""
        return LoginResult(is_logged_in=False)

    async def get_user_profile(self, page: Any) -> Optional["UserProfile"]:
        """获取用户资料，子类应重写。通过 DOM 提取或导航到个人主页获取"""
        return None
