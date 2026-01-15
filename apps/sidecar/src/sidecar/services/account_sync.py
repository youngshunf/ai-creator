"""
账号同步服务 - 静默获取并同步用户资料

支持两种模式：
- Stagehand: AI 驱动的结构化数据提取（推荐）
- Playwright: 传统选择器方式（Fallback）

@author Ysf
@date 2026-01-10
"""

import logging
from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any

from ..platforms import get_adapter, UserProfile
from ..browser.manager import BrowserSessionManager

logger = logging.getLogger(__name__)


@dataclass
class SyncResult:
    """同步结果"""
    success: bool
    platform: str
    account_id: str
    profile: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    strategy: str = "playwright"  # stagehand | playwright


class AccountSyncService:
    """
    账号同步服务 - 静默获取用户资料
    
    支持 Stagehand AI 驱动和 Playwright 传统两种模式。
    """

    # 平台 URL 映射
    PLATFORM_URLS = {
        "xiaohongshu": "https://creator.xiaohongshu.com",
        "douyin": "https://creator.douyin.com",
        "bilibili": "https://member.bilibili.com",
        "weibo": "https://weibo.com",
        "kuaishou": "https://cp.kuaishou.com",
    }

    def __init__(self, credentials_dir: str = None):
        self._credentials_dir = credentials_dir

    async def sync_account(
        self, 
        platform: str, 
        account_id: str,
        use_stagehand: bool = True,
        headless: bool = True,
    ) -> SyncResult:
        """
        同步单个账号的用户资料

        Args:
            platform: 平台名称
            account_id: 账号ID
            use_stagehand: 是否使用 Stagehand（推荐，需要 LLM Token）
            headless: 是否无头模式

        Returns:
            同步结果
        """
        # 检查 Stagehand 是否可用（需要 LLM Token）
        if use_stagehand:
            from ..browser.stagehand_client import StagehandClient
            
            if not StagehandClient.is_available():
                logger.info(
                    f"[SYNC] Stagehand 不可用（未登录 CreatorFlow 或 stagehand 未安装），"
                    f"使用 Playwright 模式"
                )
                use_stagehand = False
        
        if use_stagehand:
            try:
                return await self._sync_with_stagehand(platform, account_id, headless)
            except Exception as e:
                logger.warning(f"[SYNC] Stagehand 同步失败，降级到 Playwright: {e}")
                return await self._sync_with_playwright(platform, account_id, headless=False)
        else:
            return await self._sync_with_playwright(platform, account_id, headless)
    
    async def _sync_with_stagehand(
        self, 
        platform: str, 
        account_id: str,
        headless: bool = True,
    ) -> SyncResult:
        """
        使用 Stagehand AI 同步
        
        优势：
        - 静默运行（无头模式）
        - 自愈能力（适应 UI 变化）
        - 结构化提取（Pydantic Schema）
        """
        from ..browser.hybrid_manager import HybridBrowserManager
        
        manager = None
        try:
            manager = HybridBrowserManager(headless=headless)
            
            platform_url = self.PLATFORM_URLS.get(platform)
            if not platform_url:
                return SyncResult(
                    success=False, platform=platform, account_id=account_id,
                    error=f"不支持的平台: {platform}",
                    strategy="stagehand"
                )
            
            # 使用 Stagehand 同步
            profile = await manager.sync_profile(
                platform=platform,
                account_id=account_id,
                platform_url=platform_url,
            )
            
            logger.info(f"[SYNC] Stagehand 同步成功: {platform}:{account_id}, nickname={profile.nickname}")
            
            return SyncResult(
                success=True,
                platform=platform,
                account_id=account_id,
                profile={
                    "nickname": profile.nickname,
                    "avatar_url": profile.avatar_url,
                    "followers": profile.followers,
                    "following": profile.following,
                    "user_id": profile.user_id,
                    "bio": profile.bio,
                },
                strategy="stagehand"
            )
            
        except Exception as e:
            logger.error(f"[SYNC] Stagehand 同步失败: {platform}:{account_id}, error={e}")
            raise
        finally:
            if manager:
                await manager.close()
    
    async def _sync_with_playwright(
        self, 
        platform: str, 
        account_id: str,
        headless: bool = False,
    ) -> SyncResult:
        """
        使用 Playwright 传统方式同步（Fallback）
        
        注意：非无头模式可能会弹出浏览器窗口
        """
        browser_manager = None
        try:
            browser_manager = BrowserSessionManager(headless=headless)

            # 加载已保存的凭证
            session = await browser_manager.get_session(platform, account_id)
            if not session or not session.page:
                return SyncResult(
                    success=False, platform=platform, account_id=account_id,
                    error="无法创建浏览器会话",
                    strategy="playwright"
                )

            # 获取适配器
            adapter = get_adapter(platform)

            # 先导航到平台首页以加载 localStorage
            await session.page.goto(
                adapter.login_url.replace('/login', ''), 
                wait_until="domcontentloaded", 
                timeout=15000
            )

            # 注入 localStorage
            await browser_manager.inject_local_storage(session.page, platform, account_id)
            await session.page.reload(wait_until="domcontentloaded")

            # 提取用户资料
            profile = await adapter.get_user_profile(session.page)

            if profile:
                logger.info(f"[SYNC] Playwright 同步成功: {platform}:{account_id}, nickname={profile.nickname}")
                return SyncResult(
                    success=True, platform=platform, account_id=account_id,
                    profile=asdict(profile),
                    strategy="playwright"
                )
            else:
                return SyncResult(
                    success=False, platform=platform, account_id=account_id,
                    error="无法获取用户资料",
                    strategy="playwright"
                )

        except Exception as e:
            logger.error(f"[SYNC] Playwright 同步失败: {platform}:{account_id}, error={e}")
            return SyncResult(
                success=False, platform=platform, account_id=account_id,
                error=str(e),
                strategy="playwright"
            )
        finally:
            if browser_manager:
                await browser_manager.close()
