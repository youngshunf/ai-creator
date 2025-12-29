from typing import Any, Dict, Optional, Type
import base64
from pydantic import BaseModel, Field

from agent_core.tools.base import ToolInterface, ToolMetadata, ToolResult, ToolCapability
from agent_core.runtime.interfaces import RuntimeType
from .manager import BrowserManager

# -----------------------------------------------------------------------------
# Base Browser Tool
# -----------------------------------------------------------------------------

class BaseBrowserTool(ToolInterface):
    """浏览器工具基类"""
    
    def _get_manager(self, context: Any) -> BrowserManager:
        """
        从 RuntimeContext 获取 BrowserManager
        
        约定: context.extra["browser_manager"] 必须存在
        """
        manager = context.extra.get("browser_manager")
        if not manager:
            raise ValueError("BrowserManager not found in RuntimeContext.extra")
        return manager

# -----------------------------------------------------------------------------
# Navigate Tool
# -----------------------------------------------------------------------------

class NavigateArgs(BaseModel):
    url: str = Field(..., description="要访问的 URL")

class NavigateTool(BaseBrowserTool):
    metadata = ToolMetadata(
        name="browser_navigate",
        description="在该浏览器中访问指定 URL",
        capabilities=[ToolCapability.BROWSER_AUTOMATION],
        supported_runtimes=[RuntimeType.LOCAL],
    )

    async def execute(self, ctx: Any, **kwargs) -> ToolResult:
        url = kwargs.get("url")
        if not url:
            return ToolResult(success=False, error="Missing 'url'")
            
        try:
            manager = self._get_manager(ctx)
            page = await manager.get_page()
            await page.goto(url)
            await page.wait_for_load_state("domcontentloaded")
            title = await page.title()
            return ToolResult(success=True, data={"title": title, "url": page.url})
        except Exception as e:
            return ToolResult(success=False, error=str(e))

    def get_schema(self) -> Dict[str, Any]:
        return NavigateArgs.model_json_schema()

# -----------------------------------------------------------------------------
# Screenshot Tool
# -----------------------------------------------------------------------------

class ScreenshotTool(BaseBrowserTool):
    metadata = ToolMetadata(
        name="browser_screenshot",
        description="获取当前页面的截图 (base64)",
        capabilities=[ToolCapability.BROWSER_AUTOMATION],
        supported_runtimes=[RuntimeType.LOCAL],
    )
    
    async def execute(self, ctx: Any, **kwargs) -> ToolResult:
        try:
            manager = self._get_manager(ctx)
            page = await manager.get_page()
            screenshot_bytes = await page.screenshot(type="jpeg", quality=70)
            base64_str = base64.b64encode(screenshot_bytes).decode("utf-8")
            return ToolResult(success=True, data={"base64_image": base64_str})
        except Exception as e:
            return ToolResult(success=False, error=str(e))

    def get_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {},
        }

# -----------------------------------------------------------------------------
# Click Tool
# -----------------------------------------------------------------------------

class ClickArgs(BaseModel):
    selector: str = Field(..., description="CSS 选择器")

class ClickTool(BaseBrowserTool):
    metadata = ToolMetadata(
        name="browser_click",
        description="点击页面元素",
        capabilities=[ToolCapability.BROWSER_AUTOMATION],
        supported_runtimes=[RuntimeType.LOCAL],
    )

    async def execute(self, ctx: Any, **kwargs) -> ToolResult:
        selector = kwargs.get("selector")
        if not selector:
            return ToolResult(success=False, error="Missing 'selector'")
            
        try:
            manager = self._get_manager(ctx)
            page = await manager.get_page()
            await page.click(selector)
            return ToolResult(success=True, data={"message": f"Clicked {selector}"})
        except Exception as e:
            return ToolResult(success=False, error=str(e))

    def get_schema(self) -> Dict[str, Any]:
        return ClickArgs.model_json_schema()

# -----------------------------------------------------------------------------
# Type Tool
# -----------------------------------------------------------------------------

class TypeArgs(BaseModel):
    selector: str = Field(..., description="CSS 选择器")
    text: str = Field(..., description="要输入的文本")

class TypeTool(BaseBrowserTool):
    metadata = ToolMetadata(
        name="browser_type",
        description="在输入框中输入文本",
        capabilities=[ToolCapability.BROWSER_AUTOMATION],
        supported_runtimes=[RuntimeType.LOCAL],
    )

    async def execute(self, ctx: Any, **kwargs) -> ToolResult:
        selector = kwargs.get("selector")
        text = kwargs.get("text")
        if not selector or text is None:
             return ToolResult(success=False, error="Missing 'selector' or 'text'")

        try:
            manager = self._get_manager(ctx)
            page = await manager.get_page()
            await page.fill(selector, text)
            return ToolResult(success=True, data={"message": f"Typed '{text}' into {selector}"})
        except Exception as e:
            return ToolResult(success=False, error=str(e))

    def get_schema(self) -> Dict[str, Any]:
        return TypeArgs.model_json_schema()
