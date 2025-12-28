"""
本地浏览器工具 - 使用 Playwright 进行浏览器自动化

@author Ysf
@date 2025-12-28
"""

from typing import Any, Dict, Optional

from agent_core.tools.base import (
    ToolInterface,
    ToolMetadata,
    ToolCapability,
    ToolResult,
)
from agent_core.runtime.interfaces import RuntimeType
from agent_core.runtime.context import RuntimeContext


class LocalBrowserPublishTool(ToolInterface):
    """
    本地浏览器发布工具

    使用 Playwright 在本地浏览器中执行发布操作。
    仅在桌面端 Sidecar 中可用。
    """

    metadata = ToolMetadata(
        name="browser_publish",
        description="使用本地 Playwright 浏览器发布内容到社交平台",
        capabilities=[ToolCapability.BROWSER_AUTOMATION],
        supported_runtimes=[RuntimeType.LOCAL],
    )

    def __init__(self):
        """初始化浏览器工具"""
        self._browser = None
        self._context = None

    async def execute(
        self,
        ctx: RuntimeContext,
        *,
        platform: str,
        account_id: str,
        content: Dict[str, Any],
        headless: bool = False,
    ) -> ToolResult:
        """
        执行浏览器发布操作

        Args:
            ctx: 运行时上下文
            platform: 目标平台 (xiaohongshu, douyin, weibo, etc.)
            account_id: 账号ID
            content: 发布内容
            headless: 是否无头模式

        Returns:
            ToolResult: 执行结果
        """
        try:
            from playwright.async_api import async_playwright

            async with async_playwright() as p:
                # 启动浏览器
                browser = await p.chromium.launch(headless=headless)
                context = await browser.new_context()

                # 加载凭证
                credential_loaded = await self._load_credentials(
                    context, platform, account_id
                )
                if not credential_loaded:
                    await browser.close()
                    return ToolResult(
                        success=False,
                        data=None,
                        error=f"无法加载 {platform} 账号 {account_id} 的凭证",
                    )

                # 创建页面
                page = await context.new_page()

                # 获取平台适配器并执行发布
                adapter = self._get_platform_adapter(platform)
                if not adapter:
                    await browser.close()
                    return ToolResult(
                        success=False,
                        data=None,
                        error=f"不支持的平台: {platform}",
                    )

                result = await adapter.publish(page, content)

                # 保存更新后的凭证
                await self._save_credentials(context, platform, account_id)

                await browser.close()

                return ToolResult(
                    success=True,
                    data={
                        "platform": platform,
                        "account_id": account_id,
                        "result": result,
                    },
                )

        except ImportError:
            return ToolResult(
                success=False,
                data=None,
                error="Playwright 未安装，请运行: pip install playwright && playwright install",
            )
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"浏览器操作失败: {str(e)}",
            )

    async def _load_credentials(
        self,
        context,
        platform: str,
        account_id: str,
    ) -> bool:
        """
        加载本地保存的凭证

        Args:
            context: Playwright 浏览器上下文
            platform: 平台名称
            account_id: 账号ID

        Returns:
            bool: 是否成功加载
        """
        import os
        import json
        from pathlib import Path

        # 凭证存储路径
        cred_path = Path(os.path.expanduser(
            f"~/.ai-creator/credentials/{platform}/{account_id}.json"
        ))

        if not cred_path.exists():
            return False

        try:
            with open(cred_path, "r", encoding="utf-8") as f:
                cred_data = json.load(f)

            # 加载 cookies
            cookies = cred_data.get("cookies", [])
            if cookies:
                await context.add_cookies(cookies)

            # 加载 localStorage (如果有)
            storage_state = cred_data.get("storage_state")
            if storage_state:
                # Playwright 支持直接加载 storage state
                pass

            return True

        except Exception:
            return False

    async def _save_credentials(
        self,
        context,
        platform: str,
        account_id: str,
    ):
        """
        保存更新后的凭证

        Args:
            context: Playwright 浏览器上下文
            platform: 平台名称
            account_id: 账号ID
        """
        import os
        import json
        from pathlib import Path

        # 凭证存储路径
        cred_dir = Path(os.path.expanduser(
            f"~/.ai-creator/credentials/{platform}"
        ))
        cred_dir.mkdir(parents=True, exist_ok=True)

        cred_path = cred_dir / f"{account_id}.json"

        try:
            # 获取当前 cookies
            cookies = await context.cookies()

            cred_data = {
                "platform": platform,
                "account_id": account_id,
                "cookies": cookies,
            }

            with open(cred_path, "w", encoding="utf-8") as f:
                json.dump(cred_data, f, indent=2)

            # 设置文件权限
            try:
                cred_path.chmod(0o600)
            except OSError:
                pass

        except Exception:
            pass

    def _get_platform_adapter(self, platform: str):
        """
        获取平台适配器

        Args:
            platform: 平台名称

        Returns:
            平台适配器实例
        """
        # TODO: 实现平台适配器工厂
        # 目前返回 None，后续实现具体平台适配器
        adapters = {
            # "xiaohongshu": XiaohongshuAdapter(),
            # "douyin": DouyinAdapter(),
            # "weibo": WeiboAdapter(),
        }
        return adapters.get(platform)

    def get_schema(self) -> Dict[str, Any]:
        """获取工具参数 Schema"""
        return {
            "type": "object",
            "properties": {
                "platform": {
                    "type": "string",
                    "description": "目标平台",
                    "enum": ["xiaohongshu", "douyin", "weibo", "wechat_mp", "bilibili"],
                },
                "account_id": {
                    "type": "string",
                    "description": "账号ID",
                },
                "content": {
                    "type": "object",
                    "description": "发布内容",
                    "properties": {
                        "title": {"type": "string"},
                        "text": {"type": "string"},
                        "images": {"type": "array", "items": {"type": "string"}},
                        "video": {"type": "string"},
                        "tags": {"type": "array", "items": {"type": "string"}},
                    },
                },
                "headless": {
                    "type": "boolean",
                    "description": "是否无头模式",
                    "default": False,
                },
            },
            "required": ["platform", "account_id", "content"],
        }


class LocalBrowserScrapeTool(ToolInterface):
    """
    本地浏览器数据采集工具

    使用 Playwright 在本地浏览器中采集数据。
    """

    metadata = ToolMetadata(
        name="browser_scrape",
        description="使用本地 Playwright 浏览器采集网页数据",
        capabilities=[ToolCapability.BROWSER_AUTOMATION],
        supported_runtimes=[RuntimeType.LOCAL],
    )

    async def execute(
        self,
        ctx: RuntimeContext,
        *,
        url: str,
        selectors: Dict[str, str],
        wait_for: Optional[str] = None,
        timeout: int = 30000,
    ) -> ToolResult:
        """
        执行数据采集

        Args:
            ctx: 运行时上下文
            url: 目标URL
            selectors: CSS选择器映射 {"field_name": "css_selector"}
            wait_for: 等待的选择器
            timeout: 超时时间(毫秒)

        Returns:
            ToolResult: 采集结果
        """
        try:
            from playwright.async_api import async_playwright

            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()

                # 访问页面
                await page.goto(url, timeout=timeout)

                # 等待元素
                if wait_for:
                    await page.wait_for_selector(wait_for, timeout=timeout)

                # 提取数据
                data = {}
                for field_name, selector in selectors.items():
                    try:
                        element = await page.query_selector(selector)
                        if element:
                            data[field_name] = await element.text_content()
                    except Exception:
                        data[field_name] = None

                await browser.close()

                return ToolResult(
                    success=True,
                    data=data,
                )

        except ImportError:
            return ToolResult(
                success=False,
                data=None,
                error="Playwright 未安装",
            )
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"数据采集失败: {str(e)}",
            )

    def get_schema(self) -> Dict[str, Any]:
        """获取工具参数 Schema"""
        return {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "目标URL",
                },
                "selectors": {
                    "type": "object",
                    "description": "CSS选择器映射",
                    "additionalProperties": {"type": "string"},
                },
                "wait_for": {
                    "type": "string",
                    "description": "等待的选择器",
                },
                "timeout": {
                    "type": "integer",
                    "description": "超时时间(毫秒)",
                    "default": 30000,
                },
            },
            "required": ["url", "selectors"],
        }
