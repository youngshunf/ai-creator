"""
账号同步调度器 - 定时同步账号资料
@author Ysf
"""

import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from ..services.account_sync import AccountSyncService, SyncResult

logger = logging.getLogger(__name__)


class AccountSyncScheduler:
    """账号同步调度器 - 每隔指定时间同步所有账号"""

    def __init__(self, sync_interval_hours: float = 5.0):
        self._sync_interval = sync_interval_hours * 3600  # 转换为秒
        self._running = False
        self._sync_service = AccountSyncService()
        self._credentials_dir = Path.home() / ".ai-creator" / "credentials"
        self._last_sync: Dict[str, datetime] = {}

    async def start(self):
        """启动调度器"""
        if self._running:
            return
        self._running = True
        asyncio.create_task(self._sync_loop())
        logger.info(f"账号同步调度器已启动，间隔: {self._sync_interval / 3600}小时")

    async def stop(self):
        """停止调度器"""
        self._running = False
        logger.info("账号同步调度器已停止")

    async def sync_all(self) -> List[SyncResult]:
        """同步所有账号"""
        results = []
        if not self._credentials_dir.exists():
            return results

        for platform_dir in self._credentials_dir.iterdir():
            if platform_dir.is_dir() and not platform_dir.name.startswith("."):
                for cred_file in platform_dir.glob("*.enc"):
                    account_id = cred_file.stem
                    result = await self._sync_service.sync_account(platform_dir.name, account_id)
                    results.append(result)
                    if result.success:
                        self._last_sync[f"{platform_dir.name}:{account_id}"] = datetime.now()
        return results

    async def sync_account(self, platform: str, account_id: str) -> SyncResult:
        """同步单个账号"""
        result = await self._sync_service.sync_account(platform, account_id)
        if result.success:
            self._last_sync[f"{platform}:{account_id}"] = datetime.now()
        return result

    def get_last_sync(self, platform: str, account_id: str) -> Optional[datetime]:
        """获取上次同步时间"""
        return self._last_sync.get(f"{platform}:{account_id}")

    async def _sync_loop(self):
        """同步循环"""
        while self._running:
            try:
                logger.info("[SYNC] 开始定时同步...")
                results = await self.sync_all()
                success_count = sum(1 for r in results if r.success)
                logger.info(f"[SYNC] 同步完成: {success_count}/{len(results)} 成功")
            except Exception as e:
                logger.error(f"[SYNC] 同步出错: {e}")
            await asyncio.sleep(self._sync_interval)


_scheduler: Optional[AccountSyncScheduler] = None


def get_sync_scheduler() -> AccountSyncScheduler:
    """获取全局同步调度器"""
    global _scheduler
    if _scheduler is None:
        _scheduler = AccountSyncScheduler()
    return _scheduler
