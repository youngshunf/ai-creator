"""
浏览器会话管理器 - 管理 Playwright 浏览器会话

@author Ysf
@date 2025-12-28
"""

import asyncio
import json
import os
from pathlib import Path
from typing import Any, Dict, Optional
from dataclasses import dataclass

from .fingerprint import FingerprintGenerator, BrowserFingerprint


@dataclass
class BrowserSession:
    """浏览器会话"""
    platform: str
    account_id: str
    browser: Any  # playwright Browser
    context: Any  # playwright BrowserContext
    page: Any  # playwright Page
    fingerprint: BrowserFingerprint


class BrowserSessionManager:
    """
    浏览器会话管理器

    管理多个平台账号的浏览器会话，支持会话复用和凭证持久化。
    """

    def __init__(self, headless: bool = False):
        """
        初始化会话管理器

        Args:
            headless: 是否无头模式
        """
        self._headless = headless
        self._playwright = None
        self._sessions: Dict[str, BrowserSession] = {}
        self._fingerprint_gen = FingerprintGenerator()
        self._credentials_dir = Path(os.path.expanduser("~/.ai-creator/credentials"))
        self._initialized = False

    async def initialize(self):
        """初始化 Playwright"""
        if self._initialized:
            return

        try:
            from playwright.async_api import async_playwright
            self._playwright = await async_playwright().start()
            self._initialized = True
        except ImportError:
            raise RuntimeError("Playwright 未安装，请运行: pip install playwright && playwright install")

    async def get_session(
        self,
        platform: str,
        account_id: str,
        load_credentials: bool = True,
    ) -> BrowserSession:
        """
        获取或创建浏览器会话

        Args:
            platform: 平台名称
            account_id: 账号ID
            load_credentials: 是否加载已保存的凭证

        Returns:
            BrowserSession: 浏览器会话
        """
        session_key = f"{platform}:{account_id}"

        # 复用现有会话
        if session_key in self._sessions:
            session = self._sessions[session_key]
            if session.page and not session.page.is_closed():
                return session
            # 会话已关闭，移除并重新创建
            del self._sessions[session_key]

        await self.initialize()

        # 生成指纹
        fingerprint = self._fingerprint_gen.generate_for_account(account_id)

        # 启动浏览器
        browser = await self._playwright.chromium.launch(
            headless=self._headless,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
            ],
        )

        # 创建上下文
        context_options = {
            "viewport": {"width": fingerprint.viewport_width, "height": fingerprint.viewport_height},
            "user_agent": fingerprint.user_agent,
            "device_scale_factor": fingerprint.device_scale_factor,
            "locale": fingerprint.locale,
            "timezone_id": fingerprint.timezone_id,
        }

        # 加载凭证
        if load_credentials:
            storage_state = await self._load_storage_state(platform, account_id)
            if storage_state:
                context_options["storage_state"] = storage_state

        context = await browser.new_context(**context_options)

        # 注入反检测脚本
        await self._inject_stealth_scripts(context)

        page = await context.new_page()

        session = BrowserSession(
            platform=platform,
            account_id=account_id,
            browser=browser,
            context=context,
            page=page,
            fingerprint=fingerprint,
        )

        self._sessions[session_key] = session
        return session

    async def save_session_credentials(
        self,
        platform: str,
        account_id: str,
    ) -> bool:
        """
        保存会话凭证 - 同时保存 cookies 和 localStorage

        Args:
            platform: 平台名称
            account_id: 账号ID

        Returns:
            bool: 是否保存成功
        """
        session_key = f"{platform}:{account_id}"
        session = self._sessions.get(session_key)

        if not session:
            return False

        try:
            # 保存 storage state (包含 cookies)
            storage_state = await session.context.storage_state()

            # 获取 localStorage
            local_storage_str = await session.page.evaluate("() => JSON.stringify(localStorage)")
            local_storage_data = json.loads(local_storage_str) if local_storage_str != '{}' else {}

            # 合并到 storage_state
            storage_state['localStorage'] = local_storage_data

            cred_dir = self._credentials_dir / platform
            cred_dir.mkdir(parents=True, exist_ok=True)

            cred_path = cred_dir / f"{account_id}_state.json"

            with open(cred_path, "w", encoding="utf-8") as f:
                json.dump(storage_state, f, indent=2)

            cred_path.chmod(0o600)
            return True

        except Exception:
            return False

    async def close_session(self, platform: str, account_id: str):
        """
        关闭指定会话

        Args:
            platform: 平台名称
            account_id: 账号ID
        """
        session_key = f"{platform}:{account_id}"
        session = self._sessions.pop(session_key, None)

        if session:
            try:
                await session.browser.close()
            except Exception:
                pass

    async def close(self):
        """关闭所有会话和 Playwright"""
        for session in list(self._sessions.values()):
            try:
                await session.browser.close()
            except Exception:
                pass

        self._sessions.clear()

        if self._playwright:
            await self._playwright.stop()
            self._playwright = None
            self._initialized = False

    async def _load_storage_state(
        self,
        platform: str,
        account_id: str,
    ) -> Optional[Dict[str, Any]]:
        """加载存储状态（不包含 localStorage，需要单独注入）"""
        cred_path = self._credentials_dir / platform / f"{account_id}_state.json"

        if not cred_path.exists():
            return None

        try:
            with open(cred_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                # 移除 localStorage，因为 Playwright 不支持直接加载
                # localStorage 需要在页面加载后通过 JS 注入
                self._pending_local_storage = data.pop('localStorage', None)
                return data
        except Exception:
            return None

    async def inject_local_storage(self, page, platform: str, account_id: str):
        """注入 localStorage 到页面"""
        cred_path = self._credentials_dir / platform / f"{account_id}_state.json"

        if not cred_path.exists():
            return

        try:
            with open(cred_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                local_storage = data.get('localStorage', {})

            if local_storage:
                # 注入 localStorage
                await page.evaluate(f"""(data) => {{
                    for (const [key, value] of Object.entries(data)) {{
                        localStorage.setItem(key, value);
                    }}
                }}""", local_storage)
        except Exception:
            pass

    async def _inject_stealth_scripts(self, context):
        """注入反检测脚本"""
        await context.add_init_script("""
            // 隐藏 webdriver 属性
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });

            // 修改 plugins
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });

            // 修改 languages
            Object.defineProperty(navigator, 'languages', {
                get: () => ['zh-CN', 'zh', 'en']
            });

            // 隐藏自动化相关属性
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Array;
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Promise;
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Symbol;
        """)

    def __del__(self):
        """析构时尝试清理资源"""
        if self._sessions or self._playwright:
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    loop.create_task(self.close())
                else:
                    loop.run_until_complete(self.close())
            except Exception:
                pass
