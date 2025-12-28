"""
微信公众号平台适配器 - 实现公众号文章发布

@author Ysf
@date 2025-12-28
"""

import asyncio
from typing import Any, List, Optional
from datetime import datetime

from .base import (
    PlatformAdapter,
    PlatformRegistry,
    PlatformType,
    ContentType,
    ContentConstraints,
    PublishContent,
    PublishResult,
)


@PlatformRegistry.register
class WeChatMPAdapter(PlatformAdapter):
    """
    微信公众号平台适配器

    支持图文消息发布。
    使用 Playwright 浏览器自动化实现。
    """

    platform_type = PlatformType.WEIXIN
    platform_name = "wechat_mp"
    platform_display_name = "微信公众号"
    platform_url = "https://mp.weixin.qq.com"
    requires_login = True

    # 选择器配置
    SELECTORS = {
        "login_check": 'div[class*="weui-desktop-account"], a[class*="nickname"]',
        "new_article_btn": 'a:has-text("图文消息"), div[class*="new-creation"]',
        "title_input": 'input[placeholder*="标题"], #title',
        "content_editor": 'div[id="ueditor_0"], div[class*="edui-editor"]',
        "cover_upload": 'input[type="file"][accept*="image"]',
        "publish_btn": 'button:has-text("发表"), a:has-text("群发")',
        "save_draft_btn": 'button:has-text("保存"), a:has-text("保存为草稿")',
        "success_indicator": 'div:has-text("发送成功"), div[class*="success"]',
    }

    async def publish(
        self,
        page: Any,
        content: PublishContent,
    ) -> PublishResult:
        """
        发布文章到微信公众号

        Args:
            page: Playwright 页面对象
            content: 发布内容

        Returns:
            PublishResult: 发布结果
        """
        try:
            # 验证登录状态
            if not await self.verify_login(page):
                return PublishResult(
                    success=False,
                    error="未登录微信公众平台",
                    error_code="NOT_LOGGED_IN",
                )

            # 适配内容
            adapted_content = self.adapt_content(content)

            # 导航到新建图文页面
            await page.goto(f"{self.platform_url}/cgi-bin/appmsg?t=media/appmsg_edit&action=edit&type=77", wait_until="networkidle")
            await asyncio.sleep(3)

            # 填写标题
            if adapted_content.title:
                await self._fill_title(page, adapted_content.title)

            # 填写正文
            if adapted_content.content:
                await self._fill_content(page, adapted_content.content)

            # 上传封面图
            if adapted_content.cover_image:
                await self._upload_cover(page, adapted_content.cover_image)

            # 保存为草稿（公众号通常需要先保存再群发）
            await self._save_draft(page)
            await asyncio.sleep(2)

            # 发布
            await self._click_publish(page)

            # 等待发布结果
            result = await self._wait_for_result(page)

            return result

        except Exception as e:
            return PublishResult(
                success=False,
                error=f"发布失败: {str(e)}",
                error_code="PUBLISH_ERROR",
            )

    async def get_content_constraints(self) -> ContentConstraints:
        """获取微信公众号内容约束"""
        return ContentConstraints(
            max_title_length=64,
            min_title_length=1,
            title_required=True,
            max_content_length=20000,
            min_content_length=1,
            max_images=20,
            min_images=0,
            max_image_size_mb=10.0,
            allowed_image_formats=["jpg", "jpeg", "png", "gif"],
            max_video_duration=0,  # 图文消息不支持视频
            max_video_size_mb=0,
            max_hashtags=0,  # 公众号不使用话题标签
            max_mentions=0,
            allow_external_links=True,
            allow_internal_links=True,
            supported_content_types=[ContentType.TEXT, ContentType.IMAGE_TEXT],
        )

    def adapt_content(self, content: PublishContent) -> PublishContent:
        """适配内容到微信公众号规范"""
        adapted = PublishContent(
            title=content.title[:64] if content.title else "无标题",
            content=content.content[:20000] if content.content else "",
            images=content.images[:20],
            video=None,  # 图文消息不支持视频
            cover_image=content.cover_image or (content.images[0] if content.images else None),
            hashtags=[],  # 公众号不使用话题标签
            mentions=[],
            location=None,
            scheduled_at=content.scheduled_at,
            visibility=content.visibility,
            platform_specific=content.platform_specific,
        )

        return adapted

    async def verify_login(self, page: Any) -> bool:
        """验证微信公众号登录状态"""
        try:
            await page.goto(self.platform_url, wait_until="networkidle")
            await asyncio.sleep(2)

            # 检查是否有账号信息元素
            login_indicator = await page.query_selector(self.SELECTORS["login_check"])
            return login_indicator is not None

        except Exception:
            return False

    async def _fill_title(self, page: Any, title: str):
        """填写标题"""
        title_input = await page.query_selector(self.SELECTORS["title_input"])
        if title_input:
            await title_input.fill(title)

    async def _fill_content(self, page: Any, content: str):
        """填写正文"""
        # 微信公众号使用富文本编辑器
        editor = await page.query_selector(self.SELECTORS["content_editor"])
        if editor:
            await editor.click()
            await page.keyboard.type(content)

    async def _upload_cover(self, page: Any, cover_path: str):
        """上传封面图"""
        file_input = await page.query_selector(self.SELECTORS["cover_upload"])
        if file_input:
            await file_input.set_input_files(cover_path)

    async def _save_draft(self, page: Any):
        """保存为草稿"""
        save_btn = await page.query_selector(self.SELECTORS["save_draft_btn"])
        if save_btn:
            await save_btn.click()

    async def _click_publish(self, page: Any):
        """点击发布按钮"""
        publish_btn = await page.query_selector(self.SELECTORS["publish_btn"])
        if publish_btn:
            await publish_btn.click()

    async def _wait_for_result(self, page: Any, timeout: int = 60) -> PublishResult:
        """等待发布结果"""
        try:
            await page.wait_for_selector(
                self.SELECTORS["success_indicator"],
                timeout=timeout * 1000,
            )

            return PublishResult(
                success=True,
                published_at=datetime.now().isoformat(),
                metadata={"platform": "wechat_mp"},
            )

        except Exception:
            return PublishResult(
                success=False,
                error="发布超时或失败",
                error_code="PUBLISH_TIMEOUT",
            )

    async def save_draft(
        self,
        page: Any,
        content: PublishContent,
    ) -> PublishResult:
        """保存为草稿"""
        try:
            if not await self.verify_login(page):
                return PublishResult(
                    success=False,
                    error="未登录微信公众平台",
                    error_code="NOT_LOGGED_IN",
                )

            adapted_content = self.adapt_content(content)

            await page.goto(f"{self.platform_url}/cgi-bin/appmsg?t=media/appmsg_edit&action=edit&type=77", wait_until="networkidle")
            await asyncio.sleep(3)

            if adapted_content.title:
                await self._fill_title(page, adapted_content.title)

            if adapted_content.content:
                await self._fill_content(page, adapted_content.content)

            await self._save_draft(page)

            return PublishResult(
                success=True,
                metadata={"platform": "wechat_mp", "type": "draft"},
            )

        except Exception as e:
            return PublishResult(
                success=False,
                error=f"保存草稿失败: {str(e)}",
                error_code="DRAFT_ERROR",
            )

    def validate_content(self, content: PublishContent) -> List[str]:
        """验证内容"""
        errors = super().validate_content(content)

        if not content.title:
            errors.append("微信公众号文章必须有标题")

        if content.title and len(content.title) > 64:
            errors.append("标题不能超过64个字符")

        if content.content and len(content.content) > 20000:
            errors.append("正文不能超过20000个字符")

        return errors
