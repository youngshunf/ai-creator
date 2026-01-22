"""
账号同步服务 - 静默获取并同步用户资料

策略优先级：
1. Playwright + 平台适配器（快速、可靠、无需 LLM）
2. browser-use AI（降级方案，适应 UI 变化）

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
    strategy: str = "playwright"  # playwright | browser-use


class AccountSyncService:
    """
    账号同步服务 - 静默获取用户资料
    
    优先使用 Playwright + 平台适配器，失败后降级到 browser-use AI。
    URL 配置现在从平台适配器加载（agent-core YAML 配置）。
    """

    def __init__(self, credentials_dir: str = None):
        self._credentials_dir = credentials_dir
    
    def _get_platform_url(self, platform: str) -> str:
        """从适配器获取平台主站 URL"""
        try:
            adapter = get_adapter(platform)
            return adapter.get_url("home")
        except Exception:
            # 降级：硬编码备用
            fallback = {
                "xiaohongshu": "https://www.xiaohongshu.com",
                "douyin": "https://www.douyin.com",
                "bilibili": "https://www.bilibili.com",
                "weibo": "https://weibo.com",
                "kuaishou": "https://www.kuaishou.com",
            }
            return fallback.get(platform, "")
    
    def _get_profile_url(self, platform: str, user_id: str) -> str:
        """从适配器获取用户主页 URL"""
        try:
            adapter = get_adapter(platform)
            return adapter.get_profile_url(user_id)
        except Exception:
            # 降级：硬编码备用
            fallback_templates = {
                "xiaohongshu": "https://www.xiaohongshu.com/user/profile/{user_id}",
                "douyin": "https://www.douyin.com/user/{user_id}",
                "bilibili": "https://space.bilibili.com/{user_id}",
                "weibo": "https://weibo.com/u/{user_id}",
                "kuaishou": "https://www.kuaishou.com/profile/{user_id}",
            }
            template = fallback_templates.get(platform, "")
            return template.format(user_id=user_id) if template else ""

    async def sync_account(
        self, 
        platform: str, 
        account_id: str,
        headless: bool = True,
        use_browser_use_fallback: bool = True,
    ) -> SyncResult:
        """
        同步单个账号的用户资料

        策略：
        1. 优先使用 Playwright + 平台适配器（快速、可靠）
        2. 失败后降级到 browser-use AI（自愈能力）

        Args:
            platform: 平台名称
            account_id: 账号ID
            headless: 是否无头模式
            use_browser_use_fallback: 是否启用 browser-use 降级

        Returns:
            同步结果
        """
        # 优先使用 Playwright
        try:
            result = await self._sync_with_playwright(platform, account_id, headless)
            if result.success:
                return result
            # Playwright 返回失败但未抛异常，尝试降级
            logger.warning(f"[SYNC] Playwright 同步失败: {result.error}")
        except Exception as e:
            logger.warning(f"[SYNC] Playwright 同步异常: {e}")
        
        # 降级到 browser-use
        if use_browser_use_fallback:
            logger.info(f"[SYNC] 降级到 browser-use AI 同步")
            try:
                return await self._sync_with_browser_use(platform, account_id, headless)
            except Exception as e:
                logger.error(f"[SYNC] browser-use 同步也失败: {e}")
                return SyncResult(
                    success=False,
                    platform=platform,
                    account_id=account_id,
                    error=f"所有同步方式都失败: {e}",
                    strategy="browser-use"
                )
        
        return SyncResult(
            success=False,
            platform=platform,
            account_id=account_id,
            error="Playwright 同步失败，未启用降级",
            strategy="playwright"
        )
    
    async def _sync_with_playwright(
        self, 
        platform: str, 
        account_id: str,
        headless: bool = True,
    ) -> SyncResult:
        """
        使用 Playwright + 平台适配器同步（首选方案）
        
        优势：快速、可靠、无需 LLM Token
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
                # 转换为前端期望的字段格式
                profile_dict = asdict(profile)
                # 从 extra 中提取 collects_count 并映射为 collects
                extra = profile_dict.pop("extra", {}) or {}
                if "collects_count" in extra:
                    profile_dict["collects"] = extra["collects_count"]
                return SyncResult(
                    success=True, platform=platform, account_id=account_id,
                    profile=profile_dict,
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
    
    async def _sync_with_browser_use(
        self, 
        platform: str, 
        account_id: str,
        headless: bool = True,
    ) -> SyncResult:
        """
        使用 browser-use AI 同步（降级方案）
        
        优势：自愈能力，适应 UI 变化
        需要：LLM Token
        """
        try:
            from browser_use import Agent, Browser, BrowserConfig
            from langchain_openai import ChatOpenAI
        except ImportError:
            return SyncResult(
                success=False, platform=platform, account_id=account_id,
                error="browser-use 未安装，请运行: pip install browser-use langchain-openai",
                strategy="browser-use"
            )
        
        # 获取 LLM 配置
        import os
        from agent_core.llm.config import LLMConfigManager
        
        config_manager = LLMConfigManager()
        env = os.environ.get("AI_CREATOR_ENV", "development")
        llm_config = config_manager.load(env)
        
        if not llm_config.api_token:
            return SyncResult(
                success=False, platform=platform, account_id=account_id,
                error="browser-use 需要 LLM Token，请先登录 CreatorFlow",
                strategy="browser-use"
            )
        
        # 加载凭证
        import json
        from pathlib import Path
        
        cred_path = Path(os.path.expanduser(
            f"~/.ai-creator/credentials/{platform}/{account_id}_state.json"
        ))
        
        cookies = []
        if cred_path.exists():
            try:
                with open(cred_path, "r", encoding="utf-8") as f:
                    state = json.load(f)
                cookies = state.get("cookies", [])
            except Exception as e:
                logger.warning(f"[SYNC] 加载凭证失败: {e}")
        
        # 获取用户主页 URL
        profile_url = self._get_profile_url(platform, account_id)
        if not profile_url:
            return SyncResult(
                success=False, platform=platform, account_id=account_id,
                error=f"不支持的平台: {platform}",
                strategy="browser-use"
            )
        
        # 构建 LLM
        base_url = f"{llm_config.base_url}/api/v1/llm/proxy/v1"
        llm = ChatOpenAI(
            model=llm_config.default_model,
            api_key=llm_config.api_token,
            base_url=base_url,
            default_headers={
                "x-api-key": llm_config.api_token,
                "Authorization": f"Bearer {llm_config.access_token}" if llm_config.access_token else "",
            },
        )
        
        # 构建任务
        task = f"""
请提取当前页面用户的资料信息：
1. 打开用户主页: {profile_url}
2. 提取以下信息并以 JSON 格式返回：
   - nickname: 用户昵称
   - avatar_url: 头像URL
   - followers_count: 粉丝数
   - following_count: 关注数
   - user_id: 用户ID（{account_id}）
   - bio: 个人简介
3. 返回格式示例: {{"nickname": "xxx", "followers_count": 1000, ...}}
"""
        
        browser = None
        try:
            # 创建浏览器配置
            browser_config = BrowserConfig(
                headless=headless,
                cookies=cookies,
            )
            browser = Browser(config=browser_config)
            
            # 创建 Agent
            agent = Agent(
                task=task,
                llm=llm,
                browser=browser,
            )
            
            # 执行
            history = await agent.run()
            # 获取最后一次的输出结果
            result = history.final_result()
            result_str = str(result)
            
            logger.info(f"[SYNC] browser-use AI 返回: {result_str}")
            
            # 尝试解析 JSON 结果
            import re
            # 匹配最外层的 JSON 对象，尽可能宽松以应对 AI 输出
            json_match = re.search(r'\{.*"nickname".*\}', result_str, re.DOTALL)
            if json_match:
                try:
                    profile_data = json.loads(json_match.group())
                    logger.info(f"[SYNC] browser-use 同步成功: {platform}:{account_id}")
                    return SyncResult(
                        success=True,
                        platform=platform,
                        account_id=account_id,
                        profile=profile_data,
                        strategy="browser-use"
                    )
                except json.JSONDecodeError:
                    logger.warning("[SYNC] JSON 解析失败，尝试修复")
                    # 简单的修复尝试，例如替换单引号
                    try:
                         fixed_json = json_match.group().replace("'", '"')
                         profile_data = json.loads(fixed_json)
                         return SyncResult(
                            success=True,
                            platform=platform,
                            account_id=account_id,
                            profile=profile_data,
                            strategy="browser-use"
                        )
                    except:
                        pass

            return SyncResult(
                success=False, platform=platform, account_id=account_id,
                error=f"无法解析 AI 返回结果: {result_str[:200]}",
                strategy="browser-use"
            )
                
        except Exception as e:
            logger.error(f"[SYNC] browser-use 同步失败: {e}")
            return SyncResult(
                success=False, platform=platform, account_id=account_id,
                error=str(e),
                strategy="browser-use"
            )
        finally:
            if browser:
                await browser.close()
