"""
平台适配器基类测试

@author Ysf
@date 2025-12-28
"""

import pytest
from agent_core.platforms import (
    PlatformType,
    ContentType,
    ContentConstraints,
    PublishContent,
    PublishResult,
    PlatformRegistry,
)


class TestPlatformType:
    """平台类型测试"""

    def test_platform_types_exist(self):
        """测试平台类型定义"""
        assert PlatformType.XIAOHONGSHU == "xiaohongshu"
        assert PlatformType.DOUYIN == "douyin"
        assert PlatformType.WEIBO == "weibo"
        assert PlatformType.BILIBILI == "bilibili"
        assert PlatformType.WEIXIN == "weixin"


class TestContentType:
    """内容类型测试"""

    def test_content_types_exist(self):
        """测试内容类型定义"""
        assert ContentType.TEXT == "text"
        assert ContentType.IMAGE_TEXT == "image_text"
        assert ContentType.VIDEO == "video"


class TestContentConstraints:
    """内容约束测试"""

    def test_default_constraints(self):
        """测试默认约束"""
        constraints = ContentConstraints()
        assert constraints.max_title_length == 100
        assert constraints.max_content_length == 20000
        assert constraints.max_images == 9

    def test_custom_constraints(self):
        """测试自定义约束"""
        constraints = ContentConstraints(
            max_title_length=20,
            max_content_length=1000,
            max_images=18,
        )
        assert constraints.max_title_length == 20
        assert constraints.max_content_length == 1000
        assert constraints.max_images == 18


class TestPublishContent:
    """发布内容测试"""

    def test_create_content(self):
        """测试创建内容"""
        content = PublishContent(
            title="测试标题",
            content="测试内容",
            images=["img1.jpg"],
            hashtags=["tag1", "tag2"],
        )
        assert content.title == "测试标题"
        assert content.content == "测试内容"
        assert len(content.images) == 1
        assert len(content.hashtags) == 2

    def test_default_values(self):
        """测试默认值"""
        content = PublishContent()
        assert content.title is None
        assert content.content == ""
        assert content.images == []
        assert content.visibility == "public"


class TestPublishResult:
    """发布结果测试"""

    def test_success_result(self):
        """测试成功结果"""
        result = PublishResult(
            success=True,
            post_id="123",
            url="https://example.com/post/123",
        )
        assert result.success is True
        assert result.post_id == "123"
        assert result.error is None

    def test_failure_result(self):
        """测试失败结果"""
        result = PublishResult(
            success=False,
            error="发布失败",
            error_code="PUBLISH_ERROR",
        )
        assert result.success is False
        assert result.error == "发布失败"
        assert result.error_code == "PUBLISH_ERROR"


class TestPlatformRegistry:
    """平台注册表测试"""

    def test_list_platforms(self):
        """测试列出平台"""
        platforms = PlatformRegistry.list_platforms()
        assert "xiaohongshu" in platforms
        assert "douyin" in platforms
        assert "weibo" in platforms
        assert "bilibili" in platforms

    def test_get_adapter(self):
        """测试获取适配器"""
        adapter_class = PlatformRegistry.get("xiaohongshu")
        assert adapter_class is not None
        assert adapter_class.platform_name == "xiaohongshu"

    def test_get_nonexistent_adapter(self):
        """测试获取不存在的适配器"""
        adapter_class = PlatformRegistry.get("nonexistent")
        assert adapter_class is None

    def test_create_adapter(self):
        """测试创建适配器实例"""
        adapter = PlatformRegistry.create("xiaohongshu")
        assert adapter is not None
        assert adapter.platform_name == "xiaohongshu"
        assert adapter.platform_display_name == "小红书"
