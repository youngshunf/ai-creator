"""
平台配置模块单元测试

测试配置加载、Schema 验证等功能。

@author Ysf
@date 2026-01-22
"""

import pytest
from pathlib import Path

from agent_core.platforms.config import (
    ConfigLoader,
    ConfigError,
    PlatformConfig,
    PlatformInfo,
    PlatformUrls,
    PlatformConstraints,
    PlatformSelectors,
    LoginDetection,
)


class TestConfigLoader:
    """配置加载器测试"""

    def test_list_platforms(self):
        """测试列出所有平台"""
        platforms = ConfigLoader.list_platforms()
        
        assert isinstance(platforms, list)
        assert len(platforms) >= 5  # 至少有 5 个平台配置
        
        # 检查必须存在的平台
        expected_platforms = ["xiaohongshu", "douyin", "bilibili", "wechat", "weibo"]
        for platform in expected_platforms:
            assert platform in platforms, f"平台 {platform} 应该存在"

    def test_load_xiaohongshu(self):
        """测试加载小红书配置"""
        config = ConfigLoader.load("xiaohongshu")
        
        assert isinstance(config, PlatformConfig)
        assert config.platform.name == "xiaohongshu"
        assert config.platform.display_name == "小红书"
        assert config.urls.login == "https://www.xiaohongshu.com/login"
        assert config.constraints.title.max_length == 20
        assert config.constraints.content.max_length == 1000

    def test_load_douyin(self):
        """测试加载抖音配置"""
        config = ConfigLoader.load("douyin")
        
        assert config.platform.name == "douyin"
        assert config.platform.display_name == "抖音"
        assert config.constraints.title.max_length == 55
        assert config.constraints.video.max_duration == 900

    def test_load_bilibili(self):
        """测试加载 B 站配置"""
        config = ConfigLoader.load("bilibili")
        
        assert config.platform.name == "bilibili"
        assert config.platform.display_name == "哔哩哔哩"
        assert config.constraints.title.required is True
        assert config.constraints.video.max_duration == 36000  # 10 小时

    def test_load_wechat(self):
        """测试加载微信公众号配置"""
        config = ConfigLoader.load("wechat")
        
        assert config.platform.name == "wechat"
        assert config.platform.display_name == "微信公众号"
        assert config.constraints.content.max_length == 20000

    def test_load_weibo(self):
        """测试加载微博配置"""
        config = ConfigLoader.load("weibo")
        
        assert config.platform.name == "weibo"
        assert config.platform.display_name == "微博"
        assert config.constraints.content.max_length == 2000
        assert config.constraints.hashtags.format == "#{tag}#"

    def test_load_nonexistent_platform(self):
        """测试加载不存在的平台"""
        with pytest.raises(ConfigError) as exc_info:
            ConfigLoader.load("nonexistent_platform")
        
        assert "找不到平台配置文件" in str(exc_info.value)

    def test_load_all(self):
        """测试加载所有平台配置"""
        configs = ConfigLoader.load_all()
        
        assert isinstance(configs, dict)
        assert len(configs) >= 5
        
        for name, config in configs.items():
            assert isinstance(config, PlatformConfig)
            assert config.platform.name == name

    def test_cache_behavior(self):
        """测试缓存行为"""
        # 清除缓存
        ConfigLoader.refresh_cache()
        
        # 首次加载
        config1 = ConfigLoader.load("xiaohongshu")
        
        # 二次加载应该返回缓存的对象
        config2 = ConfigLoader.load("xiaohongshu")
        
        assert config1 is config2  # 应该是同一个对象
        
        # 刷新缓存后应该是新对象
        ConfigLoader.refresh_cache()
        config3 = ConfigLoader.load("xiaohongshu")
        
        assert config3 is not config1

    def test_disable_cache(self):
        """测试禁用缓存"""
        ConfigLoader.set_cache_enabled(False)
        
        try:
            config1 = ConfigLoader.load("xiaohongshu")
            config2 = ConfigLoader.load("xiaohongshu")
            
            # 禁用缓存后应该是不同对象
            assert config1 is not config2
        finally:
            # 恢复缓存
            ConfigLoader.set_cache_enabled(True)
            ConfigLoader.refresh_cache()


class TestPlatformConfig:
    """平台配置 Schema 测试"""

    def test_constraints_structure(self):
        """测试约束结构"""
        config = ConfigLoader.load("xiaohongshu")
        
        # 标题约束
        assert hasattr(config.constraints, "title")
        assert hasattr(config.constraints.title, "max_length")
        assert hasattr(config.constraints.title, "min_length")
        
        # 图片约束
        assert hasattr(config.constraints, "images")
        assert hasattr(config.constraints.images, "max_count")
        assert hasattr(config.constraints.images, "formats")
        
        # 视频约束
        assert hasattr(config.constraints, "video")
        assert hasattr(config.constraints.video, "max_duration")
        assert hasattr(config.constraints.video, "formats")

    def test_selectors_structure(self):
        """测试选择器结构"""
        config = ConfigLoader.load("xiaohongshu")
        
        assert hasattr(config.selectors, "login_check")
        assert hasattr(config.selectors, "submit_btn")
        assert hasattr(config.selectors, "success_indicator")
        
        # 选择器应该是非空字符串
        assert len(config.selectors.login_check) > 0
        assert len(config.selectors.submit_btn) > 0

    def test_login_detection_structure(self):
        """测试登录检测结构"""
        config = ConfigLoader.load("xiaohongshu")
        
        assert hasattr(config.login_detection, "cookie_keys")
        assert hasattr(config.login_detection, "local_storage_keys")
        assert hasattr(config.login_detection, "user_id_extraction")
        
        assert isinstance(config.login_detection.cookie_keys, list)
        assert len(config.login_detection.cookie_keys) > 0

    def test_urls_structure(self):
        """测试 URL 结构"""
        config = ConfigLoader.load("xiaohongshu")
        
        assert config.urls.home.startswith("https://")
        assert config.urls.login.startswith("https://")
        assert config.urls.publish.startswith("https://")


class TestConfigValidation:
    """配置验证测试"""

    def test_validate_valid_config(self):
        """测试验证有效配置"""
        config_data = {
            "platform": {
                "name": "test",
                "display_name": "测试平台",
                "type": "test",
            },
            "urls": {
                "home": "https://test.com",
                "login": "https://test.com/login",
                "publish": "https://test.com/publish",
            },
            "constraints": {
                "title": {"max_length": 100},
                "content": {"max_length": 1000},
            },
            "selectors": {
                "login_check": "div.user",
                "submit_btn": "button.submit",
                "success_indicator": "div.success",
            },
            "login_detection": {
                "cookie_keys": ["session"],
            },
        }
        
        errors = ConfigLoader.validate_config(config_data)
        assert len(errors) == 0

    def test_validate_missing_required_field(self):
        """测试验证缺少必填字段"""
        config_data = {
            "platform": {
                "name": "test",
                # 缺少 display_name
                "type": "test",
            },
            "urls": {
                "home": "https://test.com",
                "login": "https://test.com/login",
                "publish": "https://test.com/publish",
            },
            "constraints": {
                "title": {"max_length": 100},
                "content": {"max_length": 1000},
            },
            "selectors": {
                "login_check": "div.user",
                "submit_btn": "button.submit",
                "success_indicator": "div.success",
            },
            "login_detection": {},
        }
        
        errors = ConfigLoader.validate_config(config_data)
        assert len(errors) > 0
        assert any("display_name" in e for e in errors)


class TestConfigPath:
    """配置路径测试"""

    def test_get_config_path(self):
        """测试获取配置文件路径"""
        path = ConfigLoader.get_config_path("xiaohongshu")
        
        assert path is not None
        assert path.exists()
        assert path.suffix in [".yaml", ".yml"]

    def test_get_nonexistent_config_path(self):
        """测试获取不存在的配置路径"""
        path = ConfigLoader.get_config_path("nonexistent")
        
        assert path is None
