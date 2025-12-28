"""
小红书适配器测试

@author Ysf
@date 2025-12-28
"""

import pytest
from agent_core.platforms import (
    PublishContent,
    PlatformRegistry,
    ContentType,
)
from agent_core.platforms.xiaohongshu import XiaohongshuAdapter


class TestXiaohongshuAdapter:
    """小红书适配器测试"""

    @pytest.fixture
    def adapter(self):
        """创建适配器实例"""
        return XiaohongshuAdapter()

    def test_platform_info(self, adapter):
        """测试平台信息"""
        assert adapter.platform_name == "xiaohongshu"
        assert adapter.platform_display_name == "小红书"
        assert adapter.platform_url == "https://creator.xiaohongshu.com"
        assert adapter.requires_login is True

    @pytest.mark.asyncio
    async def test_get_content_constraints(self, adapter):
        """测试获取内容约束"""
        constraints = await adapter.get_content_constraints()
        assert constraints.max_title_length == 20
        assert constraints.max_content_length == 1000
        assert constraints.max_images == 18
        assert ContentType.IMAGE_TEXT in constraints.supported_content_types
        assert ContentType.VIDEO in constraints.supported_content_types

    def test_adapt_content_title_truncation(self, adapter):
        """测试标题截断"""
        content = PublishContent(
            title="这是一个非常非常非常非常非常长的标题",
            content="内容",
            images=["img.jpg"],
        )
        adapted = adapter.adapt_content(content)
        assert len(adapted.title) <= 20

    def test_adapt_content_content_truncation(self, adapter):
        """测试正文截断"""
        content = PublishContent(
            title="标题",
            content="内容" * 1000,
            images=["img.jpg"],
        )
        adapted = adapter.adapt_content(content)
        assert len(adapted.content) <= 1000

    def test_adapt_content_images_limit(self, adapter):
        """测试图片数量限制"""
        content = PublishContent(
            title="标题",
            content="内容",
            images=[f"img{i}.jpg" for i in range(30)],
        )
        adapted = adapter.adapt_content(content)
        assert len(adapted.images) <= 18

    def test_adapt_content_hashtags_limit(self, adapter):
        """测试话题标签限制"""
        content = PublishContent(
            title="标题",
            content="内容",
            images=["img.jpg"],
            hashtags=[f"tag{i}" for i in range(20)],
        )
        adapted = adapter.adapt_content(content)
        assert len(adapted.hashtags) <= 10

    def test_validate_content_no_media(self, adapter):
        """测试验证无媒体内容"""
        content = PublishContent(
            title="标题",
            content="内容",
        )
        errors = adapter.validate_content(content)
        assert any("图片或视频" in e for e in errors)

    def test_validate_content_valid(self, adapter):
        """测试验证有效内容"""
        content = PublishContent(
            title="标题",
            content="内容",
            images=["img.jpg"],
        )
        errors = adapter.validate_content(content)
        assert len(errors) == 0

    def test_registry_registration(self):
        """测试注册表注册"""
        adapter_class = PlatformRegistry.get("xiaohongshu")
        assert adapter_class is XiaohongshuAdapter
