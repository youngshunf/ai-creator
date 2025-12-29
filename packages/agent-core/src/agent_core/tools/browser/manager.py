import logging
from typing import Optional, Any
from playwright.async_api import async_playwright, Browser, BrowserContext, Page, Playwright

logger = logging.getLogger(__name__)

class BrowserManager:
    """
    浏览器管理器 - 管理 Playwright 生命周期
    
    设计为单例或在 RuntimeContext 中共享使用。
    """
    
    def __init__(self, headless: bool = False):
        self.headless = headless
        self._playwright: Optional[Playwright] = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._page: Optional[Page] = None
        
    async def start(self):
        """启动浏览器"""
        if self._playwright:
            return

        logger.info("Starting Playwright browser...")
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(
            headless=self.headless,
            args=["--no-sandbox", "--disable-setuid-sandbox"]
        )
        self._context = await self._browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        self._page = await self._context.new_page()
        logger.info("Browser started.")

    async def get_page(self) -> Page:
        """获取当前页面，如果未启动则自动启动"""
        if not self._page:
            await self.start()
        return self._page

    async def stop(self):
        """关闭浏览器"""
        if self._context:
            await self._context.close()
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()
            
        self._page = None
        self._context = None
        self._browser = None
        self._playwright = None
        logger.info("Browser stopped.")
