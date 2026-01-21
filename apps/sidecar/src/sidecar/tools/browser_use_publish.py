"""
Browser-Use AI 发布工具

使用 browser-use 让 AI 自主操作浏览器完成发布。

@author Ysf
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional
from dataclasses import dataclass


@dataclass
class PublishResult:
    """发布结果"""
    success: bool
    platform: str
    post_url: Optional[str] = None
    error: Optional[str] = None


class BrowserUsePublisher:
    """Browser-Use AI 发布器"""

    def __init__(self):
        self.credentials_dir = Path(os.path.expanduser("~/.ai-creator/credentials"))

    async def publish(
        self,
        platform: str,
        account_id: str,
        title: str,
        content: str,
        images: list[str] = None,
        hashtags: list[str] = None,
    ) -> PublishResult:
        """
        使用 browser-use AI 发布内容

        Args:
            platform: 平台名称
            account_id: 账号ID
            title: 标题
            content: 正文
            images: 图片路径列表
            hashtags: 话题标签

        Returns:
            PublishResult: 发布结果
        """
        try:
            from browser_use import Agent, Browser, BrowserConfig
            from langchain_openai import ChatOpenAI
        except ImportError:
            return PublishResult(
                success=False,
                platform=platform,
                error="browser-use 未安装，请运行: pip install browser-use langchain-openai",
            )

        # 获取 LLM 配置
        import os
        from agent_core.llm.config import LLMConfigManager
        
        config_manager = LLMConfigManager()
        env = os.environ.get("AI_CREATOR_ENV", "development")
        llm_config = config_manager.load(env)
        
        if not llm_config.api_token:
            return PublishResult(
                success=False,
                platform=platform,
                error="browser-use 需要 LLM Token，请先登录 CreatorFlow",
            )

        # 加载凭证
        credentials = self._load_credentials(platform, account_id)
        if not credentials:
            return PublishResult(
                success=False,
                platform=platform,
                error=f"未找到 {platform} 账号 {account_id} 的凭证",
            )

        # 构建发布任务描述
        task = self._build_publish_task(platform, title, content, images, hashtags)

        try:
            # 构建 LLM（使用 CreatorFlow LLM 网关）
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
            
            # 创建浏览器配置
            browser_config = BrowserConfig(
                headless=False,  # 发布时使用有头模式便于调试
                cookies=credentials.get("cookies", []),
            )
            browser = Browser(config=browser_config)
            
            # 创建 browser-use Agent
            agent = Agent(
                task=task,
                llm=llm,
                browser=browser,
            )

            # 执行发布
            result = await agent.run()

            # 解析结果
            if "成功" in str(result) or "success" in str(result).lower():
                return PublishResult(
                    success=True,
                    platform=platform,
                    post_url=self._extract_post_url(str(result)),
                )
            else:
                return PublishResult(
                    success=False,
                    platform=platform,
                    error=str(result),
                )

        except Exception as e:
            return PublishResult(
                success=False,
                platform=platform,
                error=f"发布失败: {str(e)}",
            )

    def _load_credentials(self, platform: str, account_id: str) -> Optional[Dict]:
        """加载账号凭证"""
        cred_path = self.credentials_dir / platform / f"{account_id}.json"
        if not cred_path.exists():
            return None
        try:
            with open(cred_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None

    def _build_publish_task(
        self,
        platform: str,
        title: str,
        content: str,
        images: list[str] = None,
        hashtags: list[str] = None,
    ) -> str:
        """构建发布任务描述"""
        platform_urls = {
            "xiaohongshu": "https://creator.xiaohongshu.com/publish/publish",
            "wechat": "https://mp.weixin.qq.com/",
            "douyin": "https://creator.douyin.com/creator-micro/content/upload",
        }

        url = platform_urls.get(platform, "")
        tags_str = " ".join([f"#{tag}" for tag in (hashtags or [])])

        task = f"""
请在 {platform} 平台发布以下内容：

1. 打开发布页面: {url}
2. 等待页面加载完成
3. 填写标题: {title}
4. 填写正文内容:
{content}

{tags_str}
"""

        if images:
            task += f"\n5. 上传图片: {', '.join(images)}"
            task += "\n6. 点击发布按钮"
        else:
            task += "\n5. 点击发布按钮"

        task += "\n7. 等待发布成功提示，返回发布结果"

        return task

    def _extract_post_url(self, result: str) -> Optional[str]:
        """从结果中提取发布链接"""
        import re
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        urls = re.findall(url_pattern, result)
        for url in urls:
            if any(p in url for p in ["xiaohongshu", "weixin", "douyin"]):
                return url
        return None


async def start_platform_login(platform: str) -> Dict[str, Any]:
    """
    启动平台扫码登录（browser-use AI 辅助）
    
    注意：登录主要通过 BrowserSessionManager 完成，
    此函数仅作为备用方案。

    Args:
        platform: 平台名称

    Returns:
        登录结果
    """
    try:
        from browser_use import Agent, Browser, BrowserConfig
        from langchain_openai import ChatOpenAI
    except ImportError:
        return {
            "success": False,
            "error": "browser-use 未安装",
        }
    
    # 获取 LLM 配置
    import os
    from agent_core.llm.config import LLMConfigManager
    
    config_manager = LLMConfigManager()
    env = os.environ.get("AI_CREATOR_ENV", "development")
    llm_config = config_manager.load(env)
    
    if not llm_config.api_token:
        return {
            "success": False,
            "error": "browser-use 需要 LLM Token，请先登录 CreatorFlow",
        }

    platform_urls = {
        "xiaohongshu": "https://www.xiaohongshu.com/login",
        "wechat": "https://mp.weixin.qq.com/",
        "douyin": "https://creator.douyin.com/",
    }

    url = platform_urls.get(platform)
    if not url:
        return {"success": False, "error": f"不支持的平台: {platform}"}

    task = f"""
请完成 {platform} 平台的登录：

1. 打开登录页面: {url}
2. 等待用户扫码或输入账号密码登录
3. 检测登录成功后，获取用户信息（昵称、头像等）
4. 返回登录结果
"""

    browser = None
    try:
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
        
        # 创建浏览器（有头模式，用户需要看到扫码）
        browser_config = BrowserConfig(headless=False)
        browser = Browser(config=browser_config)
        
        agent = Agent(task=task, llm=llm, browser=browser)
        result = await agent.run()

        # 保存凭证
        # TODO: 从 browser context 获取 cookies 并保存

        return {
            "success": True,
            "platform": platform,
            "result": str(result),
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }
    finally:
        if browser:
            await browser.close()
