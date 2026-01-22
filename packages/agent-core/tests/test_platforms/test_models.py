"""
平台适配器统一数据模型测试

@author Ysf
@date 2026-01-22
"""

import pytest
from agent_core.platforms.models import (
    ContentType,
    ContentSpec,
    AdaptedContent,
    PublishContent,
    LoginResult,
    UserProfile,
    PublishResult,
    ContentConstraints,
)
from agent_core.platforms.config import PlatformConstraints, ContentLimits


class TestContentType:
    """内容类型枚举测试"""
    
    def test_content_type_values(self):
        """测试枚举值"""
        assert ContentType.TEXT == "text"
        assert ContentType.IMAGE_TEXT == "image_text"
        assert ContentType.VIDEO == "video"
        assert ContentType.LIVE == "live"
        assert ContentType.STORY == "story"


class TestContentSpec:
    """内容规范测试"""
    
    def test_default_values(self):
        """测试默认值"""
        spec = ContentSpec()
        assert spec.title_max_length == 100
        assert spec.content_max_length == 10000
        assert spec.image_max_count == 9
        assert spec.hashtag_format == "#{tag}"
    
    def test_custom_values(self):
        """测试自定义值"""
        spec = ContentSpec(
            title_max_length=20,
            content_max_length=1000,
            image_max_count=18,
            hashtag_format="#{tag}#",
        )
        assert spec.title_max_length == 20
        assert spec.content_max_length == 1000
        assert spec.image_max_count == 18
        assert spec.hashtag_format == "#{tag}#"
    
    def test_from_config(self):
        """测试从配置创建"""
        constraints = PlatformConstraints(
            title=ContentLimits(max_length=20, min_length=5, required=True),
            content=ContentLimits(max_length=1000, min_length=10),
        )
        
        spec = ContentSpec.from_config(constraints)
        
        assert spec.title_max_length == 20
        assert spec.title_min_length == 5
        assert spec.title_required is True
        assert spec.content_max_length == 1000
        assert spec.content_min_length == 10
    
    def test_from_config_with_images(self):
        """测试带图片约束的配置"""
        from agent_core.platforms.config import ImageConstraints
        
        constraints = PlatformConstraints(
            title=ContentLimits(max_length=50),
            content=ContentLimits(max_length=5000),
            images=ImageConstraints(
                max_count=18,
                min_count=1,
                max_size_mb=20,
                allowed_formats=["jpg", "png", "webp"],
            ),
        )
        
        spec = ContentSpec.from_config(constraints)
        
        assert spec.image_max_count == 18
        assert spec.image_min_count == 1
        assert spec.image_max_size_mb == 20
        assert spec.image_formats == ["jpg", "png", "webp"]


class TestAdaptedContent:
    """适配内容测试"""
    
    def test_minimal_creation(self):
        """测试最小化创建"""
        content = AdaptedContent(
            title="测试标题",
            content="测试内容",
        )
        assert content.title == "测试标题"
        assert content.content == "测试内容"
        assert content.images == []
        assert content.warnings == []
    
    def test_full_creation(self):
        """测试完整创建"""
        content = AdaptedContent(
            title="测试标题",
            content="测试内容",
            images=["img1.jpg", "img2.jpg"],
            videos=["video.mp4"],
            hashtags=["话题1", "话题2"],
            mentions=["@用户1"],
            cover_url="cover.jpg",
            location="北京",
            visibility="friends",
            warnings=["图片已压缩"],
        )
        
        assert len(content.images) == 2
        assert len(content.videos) == 1
        assert len(content.hashtags) == 2
        assert content.visibility == "friends"
        assert len(content.warnings) == 1
    
    def test_from_publish_content(self):
        """测试从 PublishContent 转换"""
        publish = PublishContent(
            title="原始标题",
            content="原始内容",
            images=["img.jpg"],
            videos=["video.mp4"],
            hashtags=["tag1"],
        )
        
        adapted = AdaptedContent.from_publish_content(publish)
        
        assert adapted.title == "原始标题"
        assert adapted.content == "原始内容"
        assert adapted.images == ["img.jpg"]
        assert adapted.videos == ["video.mp4"]
        assert adapted.hashtags == ["tag1"]


class TestPublishContent:
    """发布内容测试"""
    
    def test_to_adapted(self):
        """测试转换为 AdaptedContent"""
        publish = PublishContent(
            title="标题",
            content="内容",
            images=["img.jpg"],
        )
        
        adapted = publish.to_adapted()
        
        assert isinstance(adapted, AdaptedContent)
        assert adapted.title == "标题"
        assert adapted.images == ["img.jpg"]


class TestLoginResult:
    """登录结果测试"""
    
    def test_logged_out(self):
        """测试未登录状态"""
        result = LoginResult(is_logged_in=False)
        assert not result.is_logged_in
        assert result.platform_user_id is None
    
    def test_logged_in(self):
        """测试已登录状态"""
        result = LoginResult(
            is_logged_in=True,
            platform_user_id="user123",
            username="测试用户",
        )
        assert result.is_logged_in
        assert result.platform_user_id == "user123"
        assert result.username == "测试用户"


class TestUserProfile:
    """用户资料测试"""
    
    def test_creation(self):
        """测试创建用户资料"""
        profile = UserProfile(
            platform_user_id="user123",
            username="测试用户",
            nickname="昵称",
            avatar_url="https://example.com/avatar.jpg",
            followers_count=1000,
            following_count=500,
        )
        
        assert profile.platform_user_id == "user123"
        assert profile.followers_count == 1000


class TestPublishResult:
    """发布结果测试"""
    
    def test_success_result(self):
        """测试成功结果"""
        result = PublishResult(
            success=True,
            platform_post_id="post123",
            platform_post_url="https://example.com/post/123",
        )
        
        assert result.success
        assert result.platform_post_id == "post123"
        assert result.post_id == "post123"  # 兼容属性
        assert result.error_message is None
    
    def test_error_result(self):
        """测试错误结果"""
        result = PublishResult(
            success=False,
            error_message="发布失败",
            error_code="PUBLISH_ERROR",
        )
        
        assert not result.success
        assert result.error_message == "发布失败"
        assert result.error_code == "PUBLISH_ERROR"


class TestCompatibilityAlias:
    """兼容性别名测试"""
    
    def test_content_constraints_alias(self):
        """测试 ContentConstraints 别名"""
        # ContentConstraints 应该是 ContentSpec 的别名
        assert ContentConstraints is ContentSpec
        
        # 可以用旧名称创建
        constraints = ContentConstraints(title_max_length=50)
        assert isinstance(constraints, ContentSpec)
        assert constraints.title_max_length == 50
