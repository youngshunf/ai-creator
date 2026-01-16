"""
发布执行器 - 统一管理多平台发布流程
@author Ysf
"""

import logging
import asyncio
from typing import Dict, Any, Optional, List

from .browser.manager import BrowserSessionManager
from .platforms.base import PublishResult, AdaptedContent
from .platforms.xiaohongshu import XiaohongshuAdapter
# from .platforms.douyin import DouyinAdapter
# from .platforms.wechat import WechatAdapter

logger = logging.getLogger(__name__)

class PublishExecutor:
    """发布执行器"""

    def __init__(self, browser_manager: BrowserSessionManager):
        self.browser_manager = browser_manager
        self.adapters = {
            "xiaohongshu": XiaohongshuAdapter(),
            # "douyin": DouyinAdapter(),
            # "wechat": WechatAdapter(),
        }

    async def execute_publish(
        self,
        platform: str,
        account_id: str,
        content: Dict[str, Any]
    ) -> PublishResult:
        """
        执行发布任务
        
        Args:
            platform: 平台名称 (xiaohongshu, douyin, etc.)
            account_id: 账号ID
            content: 内容字典 {title, content, images, hashtags}
            
        Returns:
            PublishResult: 发布结果
        """
        if platform not in self.adapters:
            return PublishResult(success=False, error_message=f"不支持的平台: {platform}")

        adapter = self.adapters[platform]
        
        try:
            # 1. 获取/恢复浏览器会话
            logger.info(f"[{platform}] 获取会话: {account_id}")
            session = await self.browser_manager.get_session(platform, account_id)
            
            # 2. 检查登录状态
            # TODO: 可以在这里做一次快速检查，或者依赖 publish 过程中的跳转检测
            
            # 3. 内容适配
            logger.info(f"[{platform}] 适配内容...")
            adapted_content = adapter.adapt_content(
                title=content.get("title", ""),
                content=content.get("content", ""),
                images=content.get("images", []),
                videos=content.get("videos", []),
                hashtags=content.get("hashtags", [])
            )
            
            if adapted_content.warnings:
                logger.warning(f"[{platform}] 内容适配警告: {adapted_content.warnings}")

            # 4. 执行发布
            logger.info(f"[{platform}] 开始执行发布...")
            result = await adapter.publish(session.page, adapted_content)
            
            # 5. 记录结果
            if result.success:
                logger.info(f"[{platform}] 发布成功")
            else:
                logger.error(f"[{platform}] 发布失败: {result.error_message}")
                
            return result

        except Exception as e:
            logger.exception(f"[{platform}] 发布任务异常: {e}")
            return PublishResult(success=False, error_message=str(e))
