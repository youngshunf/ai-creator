"""
账号同步服务 - 静默获取并同步用户资料
@author Ysf
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


class AccountSyncService:
    """账号同步服务 - 静默获取用户资料"""

    def __init__(self, credentials_dir: str = None):
        self._credentials_dir = credentials_dir

    async def sync_account(self, platform: str, account_id: str) -> SyncResult:
        """
        同步单个账号的用户资料

        Args:
            platform: 平台名称
            account_id: 账号ID

        Returns:
            同步结果
        """
        browser_manager = None
        try:
            # 使用真实浏览器（非无头模式）避免反爬检测
            browser_manager = BrowserSessionManager(headless=False)

            # 加载已保存的凭证
            session = await browser_manager.get_session(platform, account_id)
            if not session or not session.page:
                return SyncResult(
                    success=False, platform=platform, account_id=account_id,
                    error="无法创建浏览器会话"
                )

            # 获取适配器
            adapter = get_adapter(platform)

            # 先导航到平台首页以加载 localStorage
            await session.page.goto(adapter.login_url.replace('/login', ''), wait_until="domcontentloaded", timeout=15000)

            # 注入 localStorage
            await browser_manager.inject_local_storage(session.page, platform, account_id)
            await session.page.reload(wait_until="domcontentloaded")

            # 提取用户资料
            profile = await adapter.get_user_profile(session.page)

            if profile:
                logger.info(f"[SYNC] 同步成功: {platform}:{account_id}, nickname={profile.nickname}")
                return SyncResult(
                    success=True, platform=platform, account_id=account_id,
                    profile=asdict(profile)
                )
            else:
                return SyncResult(
                    success=False, platform=platform, account_id=account_id,
                    error="无法获取用户资料"
                )

        except Exception as e:
            logger.error(f"[SYNC] 同步失败: {platform}:{account_id}, error={e}")
            return SyncResult(
                success=False, platform=platform, account_id=account_id,
                error=str(e)
            )
        finally:
            if browser_manager:
                await browser_manager.close()
