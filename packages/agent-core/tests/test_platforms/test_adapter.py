"""
平台适配器基类测试

@author Ysf
@date 2026-01-22
"""

import pytest
from typing import Any

from agent_core.platforms.adapter import PlatformAdapter
from agent_core.platforms.models import AdaptedContent, PublishResult, ContentSpec
from agent_core.platforms.config import ConfigLoader


class MockAdapter(PlatformAdapter):
    """测试用模拟适配器"""
    
    platform_name = "xiaohongshu"
    platform_display_name = "小红书"
    login_url = "https://www.xiaohongshu.com"
    
    async def publish(self, page: Any, content: AdaptedContent) -> PublishResult:
        return PublishResult(success=True, post_id="test123")


class MockAdapterNoConfig(PlatformAdapter):
    """无配置的模拟适配器"""
    
    platform_name = "unknown_platform"
    platform_display_name = "未知平台"
    login_url = "https://example.com"
    
    def _get_spec(self) -> ContentSpec:
        return ContentSpec(
            title_max_length=50,
            content_max_length=500,
        )
    
    async def publish(self, page: Any, content: AdaptedContent) -> PublishResult:
        return PublishResult(success=True)


class TestPlatformAdapterInit:
    """初始化测试"""
    
    def test_init_with_config(self):
        """测试从配置初始化"""
        config = ConfigLoader.load("xiaohongshu")
        adapter = MockAdapter(config=config)
        
        assert adapter._config is not None
        assert adapter.platform_display_name == "小红书"
    
    def test_init_auto_load(self):
        """测试自动加载配置"""
        adapter = MockAdapter()
        
        assert adapter._config is not None
        assert adapter.platform_name == "xiaohongshu"
    
    def test_init_without_config(self):
        """测试无配置时使用默认值"""
        adapter = MockAdapterNoConfig()
        
        assert adapter._config is None
        # 应该使用 _get_spec() 的默认值
        assert adapter.spec.title_max_length == 50


class TestContentSpec:
    """内容规范测试"""
    
    def test_spec_from_config(self):
        """测试从配置获取 spec"""
        adapter = MockAdapter()
        spec = adapter.spec
        
        assert spec.title_max_length == 20
        assert spec.content_max_length == 1000
        assert spec.image_max_count == 18
    
    def test_spec_fallback(self):
        """测试 spec 回退到默认实现"""
        adapter = MockAdapterNoConfig()
        spec = adapter.spec
        
        assert spec.title_max_length == 50
        assert spec.content_max_length == 500


class TestSelectorAccess:
    """选择器访问测试"""
    
    def test_get_selector_exists(self):
        """测试获取存在的选择器"""
        adapter = MockAdapter()
        
        selector = adapter.get_selector("login_check")
        assert selector is not None
    
    def test_get_selector_not_exists(self):
        """测试获取不存在的选择器"""
        adapter = MockAdapter()
        
        selector = adapter.get_selector("nonexistent")
        assert selector is None
    
    def test_get_selector_default(self):
        """测试获取不存在选择器时返回默认值"""
        adapter = MockAdapter()
        
        selector = adapter.get_selector("nonexistent", default=".fallback")
        assert selector == ".fallback"
    
    def test_get_selector_no_config(self):
        """测试无配置时获取选择器"""
        adapter = MockAdapterNoConfig()
        
        selector = adapter.get_selector("any", default=".default")
        assert selector == ".default"


class TestUrlAccess:
    """URL 访问测试"""
    
    def test_get_url(self):
        """测试获取 URL"""
        adapter = MockAdapter()
        
        login_url = adapter.get_url("login")
        assert "xiaohongshu.com" in login_url
    
    def test_get_profile_url(self):
        """测试获取用户主页 URL"""
        adapter = MockAdapter()
        
        profile_url = adapter.get_profile_url("user123")
        assert profile_url is not None
        assert "user123" in profile_url


class TestContentAdaptation:
    """内容适配测试"""
    
    def test_adapt_content_basic(self):
        """测试基本内容适配"""
        adapter = MockAdapter()
        
        adapted = adapter.adapt_content(
            title="测试标题",
            content="测试内容",
        )
        
        assert adapted.title == "测试标题"
        assert adapted.content == "测试内容"
        assert len(adapted.warnings) == 0
    
    def test_adapt_content_truncate_title(self):
        """测试标题截断"""
        adapter = MockAdapter()
        
        long_title = "这是一个非常长的标题" * 10  # 超过 20 字符
        adapted = adapter.adapt_content(
            title=long_title,
            content="内容",
        )
        
        assert len(adapted.title) <= adapter.spec.title_max_length
        assert "标题超长" in adapted.warnings[0]
    
    def test_adapt_content_truncate_content(self):
        """测试正文截断"""
        adapter = MockAdapter()
        
        long_content = "内容" * 1000  # 超过 1000 字符
        adapted = adapter.adapt_content(
            title="标题",
            content=long_content,
        )
        
        assert len(adapted.content) <= adapter.spec.content_max_length
        assert "内容超长" in adapted.warnings[0]
    
    def test_adapt_content_limit_images(self):
        """测试图片数量限制"""
        adapter = MockAdapter()
        
        images = [f"img{i}.jpg" for i in range(30)]  # 超过 18 张
        adapted = adapter.adapt_content(
            title="标题",
            content="内容",
            images=images,
        )
        
        assert len(adapted.images) == adapter.spec.image_max_count
        assert "图片数量超限" in adapted.warnings[0]
    
    def test_adapt_content_limit_hashtags(self):
        """测试话题标签限制"""
        adapter = MockAdapter()
        
        hashtags = [f"话题{i}" for i in range(50)]  # 超过限制
        adapted = adapter.adapt_content(
            title="标题",
            content="内容",
            hashtags=hashtags,
        )
        
        assert len(adapted.hashtags) <= adapter.spec.hashtag_max_count


class TestContentValidation:
    """内容验证测试"""
    
    def test_validate_valid_content(self):
        """测试验证有效内容"""
        adapter = MockAdapter()
        
        content = AdaptedContent(
            title="有效标题",
            content="有效内容" * 10,
            images=["img.jpg"],
        )
        
        is_valid, errors = adapter.validate_content(content)
        assert is_valid
        assert len(errors) == 0
    
    def test_validate_missing_title(self):
        """测试验证缺失标题"""
        adapter = MockAdapter()
        
        content = AdaptedContent(
            title="",  # 空标题
            content="内容",
        )
        
        is_valid, errors = adapter.validate_content(content)
        # 小红书标题是必需的
        assert not is_valid


class TestPublishPrompt:
    """发布提示词测试"""
    
    def test_get_publish_prompt(self):
        """测试生成发布提示词"""
        adapter = MockAdapter()
        
        content = AdaptedContent(
            title="测试标题",
            content="测试内容正文",
            hashtags=["话题1", "话题2"],
            images=["img1.jpg", "img2.jpg"],
        )
        
        prompt = adapter.get_publish_prompt(content)
        
        assert "小红书" in prompt
        assert "测试标题" in prompt
        assert "测试内容正文" in prompt
        assert "话题标签" in prompt
        assert "2 张图片" in prompt


class TestPlatformInfo:
    """平台信息测试"""
    
    def test_get_platform_info(self):
        """测试获取平台信息"""
        adapter = MockAdapter()
        
        info = adapter.get_platform_info()
        
        assert info["name"] == "xiaohongshu"
        assert info["display_name"] == "小红书"
        assert "spec" in info
        assert info["spec"]["title_max_length"] == 20
