"""
平台配置 Schema 定义

使用 Pydantic 定义平台配置的数据模型，用于验证 YAML 配置文件。

@author Ysf
@date 2026-01-22
"""

from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field


class PlatformInfo(BaseModel):
    """平台基本信息"""
    name: str = Field(..., description="平台标识名，如 xiaohongshu")
    display_name: str = Field(..., description="平台显示名，如 小红书")
    type: str = Field(..., description="平台类型，通常与 name 相同")
    icon: Optional[str] = Field(None, description="平台图标文件名")


class PlatformUrls(BaseModel):
    """平台 URL 配置"""
    home: str = Field(..., description="平台主站 URL")
    login: str = Field(..., description="登录页 URL")
    creator: Optional[str] = Field(None, description="创作者中心 URL")
    publish: str = Field(..., description="发布页 URL")
    profile_template: Optional[str] = Field(
        None, 
        description="用户主页 URL 模板，使用 {user_id} 占位符"
    )


class ContentLimits(BaseModel):
    """内容长度限制"""
    max_length: int = Field(..., description="最大长度")
    min_length: int = Field(0, description="最小长度")
    required: bool = Field(False, description="是否必填")


class ImageConstraints(BaseModel):
    """图片约束"""
    max_count: int = Field(9, description="最大图片数量")
    min_count: int = Field(0, description="最小图片数量")
    max_size_mb: float = Field(20.0, description="单张图片最大大小 (MB)")
    formats: List[str] = Field(
        default_factory=lambda: ["jpg", "jpeg", "png", "webp"],
        description="支持的图片格式"
    )
    aspect_ratio: Optional[str] = Field(None, description="推荐宽高比，如 3:4")


class VideoConstraints(BaseModel):
    """视频约束"""
    max_count: int = Field(1, description="最大视频数量")
    max_duration: int = Field(600, description="最大时长 (秒)")
    max_size_mb: float = Field(500.0, description="最大文件大小 (MB)")
    formats: List[str] = Field(
        default_factory=lambda: ["mp4", "mov"],
        description="支持的视频格式"
    )


class HashtagConstraints(BaseModel):
    """话题标签约束"""
    max_count: int = Field(10, description="最大标签数量")
    format: str = Field("#{tag}", description="标签格式模板")


class MentionConstraints(BaseModel):
    """@提及约束"""
    max_count: int = Field(10, description="最大提及数量")
    supported: bool = Field(True, description="是否支持 @提及")


class FeatureFlags(BaseModel):
    """平台功能特性"""
    allow_external_links: bool = Field(True, description="是否允许外部链接")
    allow_internal_links: bool = Field(True, description="是否允许内部链接")
    location_supported: bool = Field(True, description="是否支持位置信息")
    schedule_supported: bool = Field(True, description="是否支持定时发布")
    draft_supported: bool = Field(True, description="是否支持草稿")


class PlatformConstraints(BaseModel):
    """平台内容约束汇总"""
    title: ContentLimits = Field(..., description="标题限制")
    content: ContentLimits = Field(..., description="正文限制")
    images: ImageConstraints = Field(
        default_factory=ImageConstraints,
        description="图片约束"
    )
    video: VideoConstraints = Field(
        default_factory=VideoConstraints,
        description="视频约束"
    )
    hashtags: HashtagConstraints = Field(
        default_factory=HashtagConstraints,
        description="话题标签约束"
    )
    mentions: MentionConstraints = Field(
        default_factory=MentionConstraints,
        description="@提及约束"
    )
    features: FeatureFlags = Field(
        default_factory=FeatureFlags,
        description="平台功能特性"
    )
    supported_formats: List[str] = Field(
        default_factory=lambda: ["text", "image", "video"],
        description="支持的内容格式"
    )


class PlatformSelectors(BaseModel):
    """平台 DOM 选择器配置"""
    login_check: str = Field(..., description="登录状态检测选择器")
    publish_btn: Optional[str] = Field(None, description="发布按钮选择器")
    upload_image: Optional[str] = Field(None, description="图片上传输入框选择器")
    upload_video: Optional[str] = Field(None, description="视频上传输入框选择器")
    title_input: Optional[str] = Field(None, description="标题输入框选择器")
    content_input: Optional[str] = Field(None, description="正文输入框选择器")
    tag_input: Optional[str] = Field(None, description="标签输入框选择器")
    submit_btn: str = Field(..., description="提交按钮选择器")
    success_indicator: str = Field(..., description="发布成功标识选择器")
    
    # 额外选择器，可扩展
    extra: Dict[str, str] = Field(
        default_factory=dict,
        description="其他自定义选择器"
    )


class UserIdExtraction(BaseModel):
    """用户 ID 提取规则"""
    type: Literal["cookie", "local_storage", "local_storage_key_prefix", "url_pattern", "dom"] = Field(
        ..., 
        description="提取类型"
    )
    key: Optional[str] = Field(None, description="cookie/localStorage 键名")
    pattern: Optional[str] = Field(None, description="匹配模式")
    selector: Optional[str] = Field(None, description="DOM 选择器")


class UrlPatterns(BaseModel):
    """URL 模式配置"""
    logged_in: List[str] = Field(
        default_factory=list,
        description="已登录时 URL 包含的模式"
    )
    logged_out: List[str] = Field(
        default_factory=list,
        description="未登录时 URL 包含的模式"
    )


class LoginDetection(BaseModel):
    """登录检测配置"""
    cookie_keys: List[str] = Field(
        default_factory=list,
        description="登录状态相关的 cookie 键名"
    )
    local_storage_keys: List[str] = Field(
        default_factory=list,
        description="登录状态相关的 localStorage 键名"
    )
    url_patterns: UrlPatterns = Field(
        default_factory=UrlPatterns,
        description="URL 模式"
    )
    user_id_extraction: List[UserIdExtraction] = Field(
        default_factory=list,
        description="用户 ID 提取规则列表（按优先级排序）"
    )


class PlatformConfig(BaseModel):
    """平台配置根模型"""
    platform: PlatformInfo = Field(..., description="平台基本信息")
    urls: PlatformUrls = Field(..., description="URL 配置")
    constraints: PlatformConstraints = Field(..., description="内容约束")
    selectors: PlatformSelectors = Field(..., description="DOM 选择器")
    login_detection: LoginDetection = Field(..., description="登录检测配置")
    version: str = Field("1.0", description="配置版本")
    updated_at: Optional[str] = Field(None, description="最后更新时间")
    
    class Config:
        """Pydantic 配置"""
        extra = "allow"  # 允许额外字段，便于扩展
