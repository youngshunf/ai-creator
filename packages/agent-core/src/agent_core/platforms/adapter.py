"""
平台适配器统一基类

整合 sidecar 和 agent-core 两个版本的基类功能，
支持从 YAML 配置加载平台元数据。

@author Ysf
@date 2026-01-22
"""

from abc import ABC, abstractmethod
from typing import Any, Optional, List, Dict, ClassVar
import logging

from .models import (
    ContentSpec,
    AdaptedContent,
    PublishContent,
    LoginResult,
    UserProfile,
    PublishResult,
)

# 尝试导入配置模块
try:
    from .config import ConfigLoader, PlatformConfig, ConfigError
    _CONFIG_AVAILABLE = True
except ImportError:
    _CONFIG_AVAILABLE = False
    ConfigLoader = None
    PlatformConfig = None
    ConfigError = Exception

logger = logging.getLogger(__name__)


class PlatformAdapter(ABC):
    """
    平台适配器抽象基类
    
    定义与内容平台交互的通用接口，包括：
    - 内容发布
    - 内容适配
    - 登录状态检测
    - 用户资料获取
    
    支持两种初始化方式：
    1. 从 YAML 配置加载（推荐）
    2. 子类硬编码配置（向后兼容）
    
    使用示例:
        class XiaohongshuAdapter(PlatformAdapter):
            platform_name = "xiaohongshu"
            
            async def publish(self, page, content):
                # 使用 self.get_selector("submit_btn") 获取选择器
                # 使用 self.spec 获取内容规范
                pass
    """
    
    # 子类必须定义的类属性
    platform_name: ClassVar[str] = ""
    platform_display_name: ClassVar[str] = ""
    login_url: ClassVar[str] = ""
    
    # 配置缓存
    _config: Optional["PlatformConfig"] = None
    _spec: Optional[ContentSpec] = None
    
    def __init__(self, config: Optional["PlatformConfig"] = None):
        """
        初始化平台适配器
        
        Args:
            config: 平台配置对象。如果不提供，将尝试从 YAML 加载。
        """
        if config is not None:
            self._config = config
        elif _CONFIG_AVAILABLE and self.platform_name:
            try:
                self._config = ConfigLoader.load(self.platform_name)
            except ConfigError as e:
                logger.debug(f"未找到配置文件 [{self.platform_name}]，使用默认值: {e}")
                self._config = None
        else:
            self._config = None
        
        # 同步类属性（从配置或默认值）
        if self._config:
            self.platform_display_name = self._config.platform.display_name
            self.login_url = self._config.urls.login
    
    @property
    def spec(self) -> ContentSpec:
        """
        获取平台内容规范
        
        优先从配置加载，否则调用子类的 _get_spec() 方法。
        """
        if self._spec is not None:
            return self._spec
        
        if self._config is not None:
            self._spec = ContentSpec.from_config(self._config.constraints)
        else:
            self._spec = self._get_spec()
        
        return self._spec
    
    def _get_spec(self) -> ContentSpec:
        """
        子类可重写此方法提供默认 ContentSpec
        
        仅在配置文件不存在时调用。
        """
        return ContentSpec()
    
    def get_selector(self, name: str, default: Optional[str] = None) -> Optional[str]:
        """
        获取选择器
        
        Args:
            name: 选择器名称（如 "submit_btn", "title_input"）
            default: 默认值
            
        Returns:
            选择器字符串，不存在返回 default
        """
        if self._config is None:
            return default
        
        # 首先检查标准选择器
        selector = getattr(self._config.selectors, name, None)
        if selector is not None:
            return selector
        
        # 然后检查 extra 选择器
        if hasattr(self._config.selectors, 'extra'):
            return self._config.selectors.extra.get(name, default)
        
        return default
    
    def get_url(self, name: str, default: Optional[str] = None) -> Optional[str]:
        """
        获取 URL
        
        Args:
            name: URL 名称（如 "login", "publish", "home"）
            default: 默认值
            
        Returns:
            URL 字符串，不存在返回 default
        """
        if self._config is None:
            return default
        
        return getattr(self._config.urls, name, default)
    
    def get_profile_url(self, user_id: str) -> Optional[str]:
        """
        获取用户主页 URL
        
        Args:
            user_id: 用户 ID
            
        Returns:
            用户主页 URL，模板不存在返回 None
        """
        if self._config is None or not self._config.urls.profile_template:
            return None
        
        return self._config.urls.profile_template.format(user_id=user_id)
    
    def adapt_content(
        self,
        title: str,
        content: str,
        images: Optional[List[str]] = None,
        videos: Optional[List[str]] = None,
        hashtags: Optional[List[str]] = None,
        mentions: Optional[List[str]] = None,
        **kwargs,
    ) -> AdaptedContent:
        """
        适配内容到平台规范
        
        根据 self.spec 的限制自动截断和过滤内容。
        子类可重写此方法添加平台特定的适配逻辑。
        
        Args:
            title: 标题
            content: 正文
            images: 图片路径列表
            videos: 视频路径列表
            hashtags: 话题标签列表
            mentions: @提及列表
            **kwargs: 其他参数
            
        Returns:
            AdaptedContent: 适配后的内容
        """
        warnings = []
        images = images or []
        videos = videos or []
        hashtags = hashtags or []
        mentions = mentions or []
        spec = self.spec
        
        # 标题适配
        adapted_title = title
        if len(title) > spec.title_max_length and spec.title_max_length > 0:
            adapted_title = title[:spec.title_max_length - 3] + "..."
            warnings.append(f"标题超长，已截断至 {spec.title_max_length} 字符")
        
        # 正文适配
        adapted_content = content
        if len(content) > spec.content_max_length:
            adapted_content = content[:spec.content_max_length - 3] + "..."
            warnings.append(f"内容超长，已截断至 {spec.content_max_length} 字符")
        
        # 图片适配
        adapted_images = images[:spec.image_max_count]
        if len(images) > spec.image_max_count:
            warnings.append(f"图片数量超限，仅保留前 {spec.image_max_count} 张")
        
        # 视频适配
        adapted_videos = videos[:spec.video_max_count]
        if len(videos) > spec.video_max_count:
            warnings.append(f"视频数量超限，仅保留前 {spec.video_max_count} 个")
        
        # 话题标签适配
        adapted_hashtags = hashtags[:spec.hashtag_max_count]
        if len(hashtags) > spec.hashtag_max_count:
            warnings.append(f"话题标签超限，仅保留前 {spec.hashtag_max_count} 个")
        
        # 提及适配
        adapted_mentions = mentions if spec.mention_supported else []
        if mentions and not spec.mention_supported:
            warnings.append("该平台不支持 @提及功能")
        elif len(mentions) > spec.mention_max_count:
            adapted_mentions = mentions[:spec.mention_max_count]
            warnings.append(f"提及数量超限，仅保留前 {spec.mention_max_count} 个")
        
        return AdaptedContent(
            title=adapted_title,
            content=adapted_content,
            images=adapted_images,
            videos=adapted_videos,
            hashtags=adapted_hashtags,
            mentions=adapted_mentions,
            cover_url=kwargs.get("cover_url"),
            location=kwargs.get("location"),
            scheduled_at=kwargs.get("scheduled_at"),
            visibility=kwargs.get("visibility", "public"),
            extra=kwargs.get("extra", {}),
            warnings=warnings,
        )
    
    def validate_content(self, content: AdaptedContent) -> tuple[bool, List[str]]:
        """
        验证内容是否符合平台规范
        
        Args:
            content: 适配后的内容
            
        Returns:
            (是否有效, 错误列表)
        """
        errors = []
        spec = self.spec
        
        if spec.title_required and not content.title:
            errors.append("标题不能为空")
        
        if len(content.title) < spec.title_min_length:
            errors.append(f"标题长度不足，最少需要 {spec.title_min_length} 字符")
        
        if len(content.content) < spec.content_min_length:
            errors.append(f"正文长度不足，最少需要 {spec.content_min_length} 字符")
        
        if len(content.images) < spec.image_min_count:
            errors.append(f"图片数量不足，最少需要 {spec.image_min_count} 张")
        
        return len(errors) == 0, errors
    
    def get_publish_prompt(self, content: AdaptedContent) -> str:
        """
        生成发布提示词（供 browser-use AI 使用）
        
        Args:
            content: 适配后的内容
            
        Returns:
            发布提示词
        """
        prompt = f"""请在 {self.platform_display_name} 发布以下内容：

标题：{content.title}

正文：
{content.content}
"""
        if content.hashtags:
            formatted_tags = []
            for tag in content.hashtags:
                formatted_tags.append(self.spec.hashtag_format.replace("{tag}", tag))
            prompt += f"\n话题标签：{' '.join(formatted_tags)}"
        
        if content.images:
            prompt += f"\n\n需要上传 {len(content.images)} 张图片"
        
        if content.videos:
            prompt += f"\n\n需要上传 {len(content.videos)} 个视频"
        
        return prompt
    
    # ========== 抽象方法 - 子类必须实现 ==========
    
    @abstractmethod
    async def publish(self, page: Any, content: AdaptedContent) -> PublishResult:
        """
        发布内容到平台
        
        Args:
            page: Playwright Page 对象
            content: 适配后的内容
            
        Returns:
            PublishResult: 发布结果
        """
        pass
    
    # ========== 可选方法 - 子类可重写 ==========
    
    async def check_login_status(
        self,
        cookies: List[Dict],
        local_storage: Dict[str, Any],
        current_url: str,
    ) -> LoginResult:
        """
        检测登录状态
        
        默认实现使用配置中的 login_detection 规则。
        子类可重写此方法添加平台特定的检测逻辑。
        
        Args:
            cookies: 当前页面的 cookies
            local_storage: localStorage 数据
            current_url: 当前页面 URL
            
        Returns:
            LoginResult: 登录检测结果
        """
        if self._config is None:
            return LoginResult(is_logged_in=False)
        
        detection = self._config.login_detection
        
        # 检查 URL 模式
        for pattern in detection.url_patterns.logged_out:
            if pattern in current_url:
                return LoginResult(is_logged_in=False)
        
        # 检查关键 cookie
        cookie_names = {c.get("name") for c in cookies}
        has_required_cookies = all(
            key in cookie_names for key in detection.cookie_keys
        ) if detection.cookie_keys else True
        
        # 检查 localStorage
        has_required_storage = all(
            key in local_storage for key in detection.local_storage_keys
        ) if detection.local_storage_keys else True
        
        if has_required_cookies or has_required_storage:
            # 尝试提取用户 ID
            user_id = self._extract_user_id(cookies, local_storage)
            return LoginResult(is_logged_in=True, platform_user_id=user_id)
        
        return LoginResult(is_logged_in=False)
    
    def _extract_user_id(
        self,
        cookies: List[Dict],
        local_storage: Dict[str, Any],
    ) -> Optional[str]:
        """
        从 cookies 和 localStorage 提取用户 ID
        
        使用配置中的 user_id_extraction 规则。
        """
        if self._config is None:
            return None
        
        for rule in self._config.login_detection.user_id_extraction:
            if rule.type == "cookie" and rule.key:
                for c in cookies:
                    if c.get("name") == rule.key:
                        return c.get("value")
            
            elif rule.type == "local_storage" and rule.key:
                if rule.key in local_storage:
                    return local_storage[rule.key]
            
            elif rule.type == "local_storage_key_prefix" and rule.pattern:
                for key in local_storage:
                    if key.startswith(rule.pattern):
                        return key[len(rule.pattern):]
        
        return None
    
    async def get_user_profile(self, page: Any) -> Optional[UserProfile]:
        """
        获取用户资料
        
        默认返回 None，子类应重写此方法。
        
        Args:
            page: Playwright Page 对象
            
        Returns:
            UserProfile 或 None
        """
        return None
    
    async def verify_login(self, page: Any) -> bool:
        """
        验证登录状态（通过页面元素）
        
        Args:
            page: Playwright Page 对象
            
        Returns:
            True 表示已登录
        """
        login_check_selector = self.get_selector("login_check")
        if not login_check_selector:
            return False
        
        try:
            element = await page.query_selector(login_check_selector)
            return element is not None
        except Exception:
            return False
    
    async def save_draft(self, page: Any, content: AdaptedContent) -> PublishResult:
        """
        保存为草稿
        
        默认返回不支持，子类可重写。
        """
        return PublishResult(
            success=False,
            error_message="该平台不支持草稿功能",
            error_code="DRAFT_NOT_SUPPORTED",
        )
    
    def get_platform_info(self) -> Dict[str, Any]:
        """
        获取平台信息
        
        Returns:
            平台信息字典
        """
        return {
            "name": self.platform_name,
            "display_name": self.platform_display_name,
            "login_url": self.login_url,
            "spec": {
                "title_max_length": self.spec.title_max_length,
                "content_max_length": self.spec.content_max_length,
                "image_max_count": self.spec.image_max_count,
                "video_max_count": self.spec.video_max_count,
                "supported_formats": self.spec.supported_formats,
            },
        }
