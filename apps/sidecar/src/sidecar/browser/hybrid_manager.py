"""
混合浏览器管理器 - 根据场景选择最佳浏览器方案

结合 CDP 真实浏览器和 Stagehand AI 自动化的优势。

@author Ysf
@date 2026-01-10
"""

import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass

from .stagehand_client import StagehandClient
from .schemas import UserProfile, LoginStatus, PublishResult
from .manager import BrowserSessionManager

logger = logging.getLogger(__name__)


@dataclass
class BrowserStrategy:
    """浏览器策略"""
    CDP = "cdp"          # CDP 真实浏览器 (最高反检测)
    STAGEHAND = "stagehand"  # Stagehand AI 自动化
    PLAYWRIGHT = "playwright"  # Playwright + Stealth


class HybridBrowserManager:
    """
    混合浏览器管理器
    
    根据不同场景选择最佳浏览器方案：
    - 首次登录: CDP 真实浏览器 (最高反检测)
    - 账号同步: Stagehand extract() (AI 提取 + 自愈)
    - 发布内容: Stagehand agent() (多步骤任务)
    """
    
    def __init__(self, headless: bool = True):
        """
        初始化混合浏览器管理器
        
        Args:
            headless: 是否无头模式 (Stagehand 使用)
        """
        self._headless = headless
        self._stagehand_client: Optional[StagehandClient] = None
        self._cdp_manager: Optional[BrowserSessionManager] = None
    
    async def _get_stagehand(self) -> StagehandClient:
        """获取 Stagehand 客户端"""
        if self._stagehand_client is None:
            self._stagehand_client = StagehandClient(headless=self._headless)
        return self._stagehand_client
    
    async def _get_cdp_manager(self, headless: bool = False) -> BrowserSessionManager:
        """获取 CDP 浏览器管理器"""
        if self._cdp_manager is None:
            self._cdp_manager = BrowserSessionManager(headless=headless)
        return self._cdp_manager
    
    async def login(
        self, 
        platform: str, 
        account_id: str,
    ) -> Dict[str, Any]:
        """
        首次登录 - 使用 CDP 真实浏览器
        
        需要用户扫码或输入密码，使用真实浏览器获得最高反检测能力。
        
        Args:
            platform: 平台名称
            account_id: 账号ID
            
        Returns:
            登录结果
        """
        logger.info(f"[HybridBrowserManager] 使用 CDP 登录: {platform}/{account_id}")
        
        # 首次登录使用非无头模式的 CDP 浏览器
        cdp_manager = await self._get_cdp_manager(headless=False)
        session = await cdp_manager.get_session(platform, account_id, load_credentials=False)
        
        return {
            "strategy": BrowserStrategy.CDP,
            "session": session,
            "message": "请在浏览器中完成登录",
        }
    
    async def sync_profile(
        self, 
        platform: str, 
        account_id: str,
        platform_url: str,
    ) -> UserProfile:
        """
        账号同步 - 使用 Stagehand extract()
        
        静默模式下提取用户资料，具有自愈能力。
        
        Args:
            platform: 平台名称
            account_id: 账号ID
            platform_url: 平台首页 URL
            
        Returns:
            UserProfile: 用户资料
        """
        logger.info(f"[HybridBrowserManager] 使用 Stagehand 同步: {platform}/{account_id}")
        
        stagehand = await self._get_stagehand()
        
        try:
            # 先初始化 Stagehand（这会检查 LLM Token）
            await stagehand.initialize()
            
            # 然后加载平台凭证（cookies）
            await self._load_credentials_to_stagehand(stagehand, platform, account_id)
            
            # 导航到平台首页
            await stagehand.goto(platform_url, wait_until="domcontentloaded")
            
            # 使用 AI 提取用户资料
            profile = await stagehand.extract(
                f"提取当前登录用户的资料，包括：用户昵称、头像URL、粉丝数、关注数、用户ID、个人简介",
                schema=UserProfile
            )
            
            logger.info(f"[HybridBrowserManager] 同步成功: {profile.nickname}")
            return profile
            
        except Exception as e:
            logger.error(f"[HybridBrowserManager] Stagehand 同步失败: {e}")
            raise
    
    async def check_login_status(
        self,
        platform: str,
        platform_url: str,
    ) -> LoginStatus:
        """
        检查登录状态 - 使用 Stagehand extract()
        
        Args:
            platform: 平台名称
            platform_url: 平台 URL
            
        Returns:
            LoginStatus: 登录状态
        """
        logger.info(f"[HybridBrowserManager] 检查登录状态: {platform}")
        
        stagehand = await self._get_stagehand()
        
        try:
            await stagehand.goto(platform_url, wait_until="domcontentloaded")
            
            status = await stagehand.extract(
                "检查当前页面是否已登录，如果已登录提取用户名",
                schema=LoginStatus
            )
            
            return status
            
        except Exception as e:
            logger.error(f"[HybridBrowserManager] 检查登录状态失败: {e}")
            return LoginStatus(is_logged_in=False, error_message=str(e))
    
    async def publish(
        self, 
        platform: str, 
        account_id: str,
        content: Dict[str, Any],
        platform_publish_url: str,
    ) -> PublishResult:
        """
        发布内容 - 使用 Stagehand agent()
        
        执行多步骤发布任务。
        
        Args:
            platform: 平台名称
            account_id: 账号ID
            content: 发布内容
            platform_publish_url: 平台发布页 URL
            
        Returns:
            PublishResult: 发布结果
        """
        logger.info(f"[HybridBrowserManager] 使用 Stagehand Agent 发布: {platform}/{account_id}")
        
        stagehand = await self._get_stagehand()
        
        try:
            # 加载凭证
            await self._load_credentials_to_stagehand(stagehand, platform, account_id)
            
            # 导航到发布页
            await stagehand.goto(platform_publish_url, wait_until="domcontentloaded")
            
            # 构建发布任务
            title = content.get("title", "")
            text = content.get("text", "")
            tags = content.get("tags", [])
            tags_str = " ".join([f"#{tag}" for tag in tags])
            
            task = f"""
请在当前页面发布内容：
1. 填写标题: {title}
2. 填写正文: {text}
3. 添加话题标签: {tags_str}
4. 点击发布按钮
5. 等待发布成功
"""
            
            # 执行发布
            result_text = await stagehand.agent_execute(task)
            
            # 提取发布结果
            result = await stagehand.extract(
                "提取发布结果：是否成功、作品链接、作品ID",
                schema=PublishResult
            )
            
            return result
            
        except Exception as e:
            logger.error(f"[HybridBrowserManager] 发布失败: {e}")
            return PublishResult(success=False, error_message=str(e))
    
    async def _load_credentials_to_stagehand(
        self, 
        stagehand: StagehandClient,
        platform: str,
        account_id: str,
    ):
        """加载凭证到 Stagehand"""
        import json
        from pathlib import Path
        import os
        
        cred_path = Path(os.path.expanduser(
            f"~/.ai-creator/credentials/{platform}/{account_id}_state.json"
        ))
        
        if not cred_path.exists():
            logger.warning(f"[HybridBrowserManager] 凭证不存在: {cred_path}")
            return
        
        try:
            with open(cred_path, "r", encoding="utf-8") as f:
                state = json.load(f)
            
            cookies = state.get("cookies", [])
            if cookies:
                await stagehand.add_cookies(cookies)
                logger.info(f"[HybridBrowserManager] 加载了 {len(cookies)} 个 cookies")
                
        except Exception as e:
            logger.error(f"[HybridBrowserManager] 加载凭证失败: {e}")
    
    async def close(self):
        """关闭所有浏览器资源"""
        if self._stagehand_client:
            await self._stagehand_client.close()
            self._stagehand_client = None
        
        if self._cdp_manager:
            await self._cdp_manager.close()
            self._cdp_manager = None
        
        logger.info("[HybridBrowserManager] 所有浏览器资源已关闭")
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.close()
