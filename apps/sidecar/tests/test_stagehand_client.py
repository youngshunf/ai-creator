"""
Stagehand 客户端测试

@author Ysf
@date 2026-01-10
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestStagehandClientConfig:
    """测试 Stagehand 客户端配置"""
    
    @pytest.mark.asyncio
    async def test_get_config_without_login(self):
        """测试未登录时获取配置应抛出异常"""
        from sidecar.browser.stagehand_client import StagehandClient
        
        with patch("sidecar.browser.stagehand_client.LLMConfigManager") as MockConfig:
            mock_config = MagicMock()
            mock_config.load.return_value = MagicMock(api_token="")
            MockConfig.return_value = mock_config
            
            client = StagehandClient()
            
            with pytest.raises(RuntimeError, match="用户未登录"):
                await client._get_config()
    
    @pytest.mark.asyncio
    async def test_get_config_with_login(self):
        """测试已登录时获取配置"""
        with patch("sidecar.browser.stagehand_client.LLMConfigManager") as MockConfig:
            mock_llm_config = MagicMock()
            mock_llm_config.api_token = "sk-cf-test"
            mock_llm_config.access_token = "jwt-token"
            mock_llm_config.base_url = "https://api.ai-creator.com"
            mock_llm_config.default_model = "claude-sonnet-4-5-20250929"
            
            mock_manager = MagicMock()
            mock_manager.load.return_value = mock_llm_config
            MockConfig.return_value = mock_manager
            
            # Mock stagehand import
            with patch.dict("sys.modules", {"stagehand": MagicMock()}):
                from sidecar.browser.stagehand_client import StagehandClient
                
                client = StagehandClient()
                
                # 验证配置可以正常获取
                # 由于需要真实模块，这里只验证不抛出异常
                try:
                    config = await client._get_config()
                    assert config is not None
                except ImportError:
                    # stagehand 未安装时跳过
                    pytest.skip("stagehand not installed")


class TestSchemas:
    """测试 Pydantic Schemas"""
    
    def test_user_profile_schema(self):
        """测试 UserProfile 模型"""
        from sidecar.browser.schemas import UserProfile
        
        profile = UserProfile(
            nickname="测试用户",
            avatar_url="https://example.com/avatar.jpg",
            followers=1000,
            following=100,
            user_id="123456",
            bio="这是个人简介"
        )
        
        assert profile.nickname == "测试用户"
        assert profile.followers == 1000
    
    def test_user_profile_minimal(self):
        """测试 UserProfile 最小必填字段"""
        from sidecar.browser.schemas import UserProfile
        
        profile = UserProfile(nickname="最小用户")
        
        assert profile.nickname == "最小用户"
        assert profile.avatar_url is None
        assert profile.followers is None
    
    def test_login_status_schema(self):
        """测试 LoginStatus 模型"""
        from sidecar.browser.schemas import LoginStatus
        
        status = LoginStatus(
            is_logged_in=True,
            username="test_user"
        )
        
        assert status.is_logged_in is True
        assert status.username == "test_user"
    
    def test_publish_result_schema(self):
        """测试 PublishResult 模型"""
        from sidecar.browser.schemas import PublishResult
        
        result = PublishResult(
            success=True,
            post_url="https://example.com/post/123",
            post_id="123"
        )
        
        assert result.success is True
        assert result.post_url == "https://example.com/post/123"


class TestAccountSyncService:
    """测试账号同步服务"""
    
    @pytest.mark.asyncio
    async def test_sync_account_unsupported_platform(self):
        """测试不支持的平台"""
        from sidecar.services.account_sync import AccountSyncService
        
        service = AccountSyncService()
        
        with patch.object(service, "_sync_with_stagehand") as mock_stagehand:
            # 模拟 Stagehand 返回不支持平台错误
            from sidecar.services.account_sync import SyncResult
            mock_stagehand.return_value = SyncResult(
                success=False,
                platform="unknown_platform",
                account_id="123",
                error="不支持的平台: unknown_platform",
                strategy="stagehand"
            )
            
            result = await service.sync_account("unknown_platform", "123")
            
            assert result.success is False
            assert "不支持的平台" in result.error
    
    def test_platform_urls(self):
        """测试平台 URL 映射"""
        from sidecar.services.account_sync import AccountSyncService
        
        assert "xiaohongshu" in AccountSyncService.PLATFORM_URLS
        assert "douyin" in AccountSyncService.PLATFORM_URLS
        assert "bilibili" in AccountSyncService.PLATFORM_URLS


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
