"""
定时发布调度器 - 使用 APScheduler 管理定时发布任务

@author Ysf
@date 2025-12-28
"""

import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


@dataclass
class ScheduledTask:
    """定时任务"""
    id: str
    platform: str
    account_id: str
    content: Dict[str, Any]
    scheduled_time: datetime
    status: str = "pending"  # pending, running, completed, failed, cancelled
    error: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    created_at: datetime = field(default_factory=datetime.now)


class PublishScheduler:
    """
    定时发布调度器

    管理定时发布任务的创建、执行和取消。
    """

    def __init__(self):
        """初始化调度器"""
        self._tasks: Dict[str, ScheduledTask] = {}
        self._running = False
        self._check_interval = 30  # 检查间隔（秒）
        self._publish_callback: Optional[Callable] = None

    def set_publish_callback(self, callback: Callable):
        """
        设置发布回调函数

        Args:
            callback: 异步发布函数，签名为 async def publish(platform, account_id, content) -> dict
        """
        self._publish_callback = callback

    async def start(self):
        """启动调度器"""
        if self._running:
            return

        self._running = True
        asyncio.create_task(self._check_loop())
        logger.info("发布调度器已启动")

    async def stop(self):
        """停止调度器"""
        self._running = False
        logger.info("发布调度器已停止")

    def schedule_publish(
        self,
        task_id: str,
        platform: str,
        account_id: str,
        content: Dict[str, Any],
        scheduled_time: datetime,
    ) -> ScheduledTask:
        """
        创建定时发布任务

        Args:
            task_id: 任务ID
            platform: 平台名称
            account_id: 账号ID
            content: 发布内容
            scheduled_time: 计划发布时间

        Returns:
            ScheduledTask: 创建的任务
        """
        task = ScheduledTask(
            id=task_id,
            platform=platform,
            account_id=account_id,
            content=content,
            scheduled_time=scheduled_time,
        )

        self._tasks[task_id] = task
        logger.info(f"已创建定时任务: {task_id}, 计划时间: {scheduled_time}")

        return task

    def cancel_schedule(self, task_id: str) -> bool:
        """
        取消定时任务

        Args:
            task_id: 任务ID

        Returns:
            bool: 是否取消成功
        """
        task = self._tasks.get(task_id)
        if not task:
            return False

        if task.status == "pending":
            task.status = "cancelled"
            logger.info(f"已取消定时任务: {task_id}")
            return True

        return False

    def list_scheduled(
        self,
        status: Optional[str] = None,
        platform: Optional[str] = None,
    ) -> List[ScheduledTask]:
        """
        列出定时任务

        Args:
            status: 筛选状态
            platform: 筛选平台

        Returns:
            List[ScheduledTask]: 任务列表
        """
        tasks = list(self._tasks.values())

        if status:
            tasks = [t for t in tasks if t.status == status]

        if platform:
            tasks = [t for t in tasks if t.platform == platform]

        return sorted(tasks, key=lambda t: t.scheduled_time)

    def get_task(self, task_id: str) -> Optional[ScheduledTask]:
        """获取任务详情"""
        return self._tasks.get(task_id)

    async def _check_loop(self):
        """检查循环"""
        while self._running:
            try:
                await self._check_and_execute()
            except Exception as e:
                logger.error(f"检查任务时出错: {e}")

            await asyncio.sleep(self._check_interval)

    async def _check_and_execute(self):
        """检查并执行到期任务"""
        now = datetime.now()

        for task in list(self._tasks.values()):
            if task.status != "pending":
                continue

            if task.scheduled_time <= now:
                await self._execute_task(task)

    async def _execute_task(self, task: ScheduledTask):
        """执行发布任务"""
        task.status = "running"
        logger.info(f"开始执行定时任务: {task.id}")

        try:
            if not self._publish_callback:
                raise RuntimeError("未设置发布回调函数")

            result = await self._publish_callback(
                task.platform,
                task.account_id,
                task.content,
            )

            task.status = "completed"
            task.result = result
            logger.info(f"定时任务执行成功: {task.id}")

        except Exception as e:
            task.status = "failed"
            task.error = str(e)
            logger.error(f"定时任务执行失败: {task.id}, 错误: {e}")


# 全局调度器实例
_scheduler: Optional[PublishScheduler] = None


def get_scheduler() -> PublishScheduler:
    """获取全局调度器实例"""
    global _scheduler
    if _scheduler is None:
        _scheduler = PublishScheduler()
    return _scheduler
