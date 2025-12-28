"""
B站平台适配器 - 实现B站视频/专栏发布

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
class BilibiliAdapter(PlatformAdapter):
    """
    B站平台适配器

    支持视频投稿和专栏文章发布。
    使用 Playwright 浏览器自动化实现。
    """

    platform_type = PlatformType.BILIBILI
    platform_name = "bilibili"
    platform_display_name = "哔哩哔哩"
    platform_url = "https://member.bilibili.com"
    requires_login = True

    SELECTORS = {
        "login_check": 'div[class*="header-avatar"], a[class*="header-entry-mini"]',
        "upload_video": 'input[type="file"][accept*="video"]',
        "title_input": 'input[placeholder*="标题"], input[class*="title-input"]',
        "content_input": 'textarea[placeholder*="简介"], div[class*="desc-container"] textarea',
        "tag_input": 'input[placeholder*="标签"], input[class*="tag-input"]',
        "cover_upload": 'input[type="file"][accept*="image"]',
        "submit_btn": 'button:has-text("投稿"), button[class*="submit"]',
        "success_indicator": 'div:has-text("投稿成功"), div[class*="success"]',
        # 专栏相关
        "article_title": 'input[placeholder*="标题"], input[class*="article-title"]',
        "article_content": 'div[class*="ql-editor"], div[contenteditable="true"]',
        "article_submit": 'button:has-text("发布"), button[class*="publish"]',
    }

    async def publish(
        self,
        page: Any,
        content: PublishContent,
    ) -> PublishResult:
        """发布内容到B站"""
        try:
            if not await self.verify_login(page):
                return PublishResult(
                    success=False,
                    error="未登录B站创作中心",
                    error_code="NOT_LOGGED_IN",
                )

            adapted_content = self.adapt_content(content)

            # 根据内容类型选择发布方式
            if adapted_content.video:
                return await self._publish_video(page, adapted_content)
            else:
                return await self._publish_article(page, adapted_content)

        except Exception as e:
            return PublishResult(
                success=False,
                error=f"发布失败: {str(e)}",
                error_code="PUBLISH_ERROR",
            )

    async def _publish_video(self, page: Any, content: PublishContent) -> PublishResult:
        """发布视频"""
        await page.goto(f"{self.platform_url}/platform/upload/video/frame", wait_until="networkidle")
        await asyncio.sleep(2)

        # 上传视频
        await self._upload_video(page, content.video)
        await asyncio.sleep(10)  # 等待上传

        # 填写标题
        if content.title:
            await self._fill_title(page, content.title)

        # 填写简介
        if content.content:
            await self._fill_content(page, content.content)

        # 添加标签
        if content.hashtags:
            await self._add_tags(page, content.hashtags)

        # 上传封面
        if content.cover_image:
            await self._upload_cover(page, content.cover_image)

        # 投稿
        await self._click_submit(page)

        return await self._wait_for_result(page, timeout=120)

    async def _publish_article(self, page: Any, content: PublishContent) -> PublishResult:
        """发布专栏文章"""
        await page.goto(f"{self.platform_url}/platform/upload-manager/article", wait_until="networkidle")
        await asyncio.sleep(2)

        # 点击新建文章
        new_btn = await page.query_selector('button:has-text("新建文章")')
        if new_btn:
            await new_btn.click()
            await asyncio.sleep(2)

        # 填写标题
        title_input = await page.query_selector(self.SELECTORS["article_title"])
        if title_input and content.title:
            await title_input.fill(content.title)

        # 填写正文
        content_editor = await page.query_selector(self.SELECTORS["article_content"])
        if content_editor and content.content:
            await content_editor.click()
            await page.keyboard.type(content.content)

        # 发布
        submit_btn = await page.query_selector(self.SELECTORS["article_submit"])
        if submit_btn:
            await submit_btn.click()

        return await self._wait_for_result(page)

    async def get_content_constraints(self) -> ContentConstraints:
        """获取B站内容约束"""
        return ContentConstraints(
            max_title_length=80,
            min_title_length=1,
            title_required=True,
            max_content_length=10000,  # 视频简介
            min_content_length=0,
            max_images=0,  # 视频投稿不支持图片
            min_images=0,
            max_image_size_mb=10.0,
            allowed_image_formats=["jpg", "jpeg", "png"],
            max_video_duration=14400,  # 4小时
            max_video_size_mb=8192.0,  # 8GB
            allowed_video_formats=["mp4", "flv", "avi", "wmv", "mov", "mkv"],
            max_hashtags=10,
            max_mentions=0,
            allow_external_links=False,
            allow_internal_links=True,
            supported_content_types=[ContentType.VIDEO, ContentType.TEXT],
        )

    def adapt_content(self, content: PublishContent) -> PublishContent:
        """适配内容到B站规范"""
        return PublishContent(
            title=content.title[:80] if content.title else "无标题",
            content=content.content[:10000] if content.content else "",
            images=[],
            video=content.video,
            cover_image=content.cover_image,
            hashtags=content.hashtags[:10],
            mentions=[],
            location=None,
            scheduled_at=content.scheduled_at,
            visibility=content.visibility,
            platform_specific=content.platform_specific,
        )

    async def verify_login(self, page: Any) -> bool:
        """验证B站登录状态"""
        try:
            await page.goto(self.platform_url, wait_until="networkidle")
            await asyncio.sleep(2)
            login_indicator = await page.query_selector(self.SELECTORS["login_check"])
            return login_indicator is not None
        except Exception:
            return False

    async def _upload_video(self, page: Any, video: str):
        """上传视频"""
        file_input = await page.query_selector(self.SELECTORS["upload_video"])
        if file_input:
            await file_input.set_input_files(video)

    async def _fill_title(self, page: Any, title: str):
        """填写标题"""
        title_input = await page.query_selector(self.SELECTORS["title_input"])
        if title_input:
            await title_input.fill(title)

    async def _fill_content(self, page: Any, content: str):
        """填写简介"""
        content_input = await page.query_selector(self.SELECTORS["content_input"])
        if content_input:
            await content_input.fill(content)

    async def _add_tags(self, page: Any, tags: List[str]):
        """添加标签"""
        tag_input = await page.query_selector(self.SELECTORS["tag_input"])
        if tag_input:
            for tag in tags[:10]:
                await tag_input.fill(tag)
                await page.keyboard.press("Enter")
                await asyncio.sleep(0.3)

    async def _upload_cover(self, page: Any, cover: str):
        """上传封面"""
        file_input = await page.query_selector(self.SELECTORS["cover_upload"])
        if file_input:
            await file_input.set_input_files(cover)

    async def _click_submit(self, page: Any):
        """点击投稿"""
        submit_btn = await page.query_selector(self.SELECTORS["submit_btn"])
        if submit_btn:
            await submit_btn.click()

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
                metadata={"platform": "bilibili"},
            )
        except Exception:
            return PublishResult(
                success=False,
                error="发布超时或失败",
                error_code="PUBLISH_TIMEOUT",
            )

    def validate_content(self, content: PublishContent) -> List[str]:
        """验证内容"""
        errors = super().validate_content(content)

        if not content.title:
            errors.append("B站投稿必须有标题")

        if content.title and len(content.title) > 80:
            errors.append("标题不能超过80个字符")

        if not content.video and not content.content:
            errors.append("B站投稿必须包含视频或文章内容")

        return errors
