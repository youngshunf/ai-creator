"""
抖音平台适配器 - 实现抖音视频/图文发布

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
class DouyinAdapter(PlatformAdapter):
    """
    抖音平台适配器

    支持视频和图文发布。
    使用 Playwright 浏览器自动化实现。
    """

    platform_type = PlatformType.DOUYIN
    platform_name = "douyin"
    platform_display_name = "抖音"
    platform_url = "https://creator.douyin.com"
    requires_login = True

    SELECTORS = {
        "login_check": 'div[class*="user-info"], div[class*="avatar"]',
        "upload_video": 'input[type="file"][accept*="video"]',
        "upload_image": 'input[type="file"][accept*="image"]',
        "title_input": 'input[placeholder*="标题"], div[class*="title"] input',
        "content_input": 'textarea[placeholder*="描述"], div[contenteditable="true"]',
        "tag_input": 'input[placeholder*="话题"], input[placeholder*="标签"]',
        "submit_btn": 'button:has-text("发布"), button[class*="publish"]',
        "success_indicator": 'div:has-text("发布成功"), div[class*="success"]',
    }

    async def publish(
        self,
        page: Any,
        content: PublishContent,
    ) -> PublishResult:
        """发布内容到抖音"""
        try:
            if not await self.verify_login(page):
                return PublishResult(
                    success=False,
                    error="未登录抖音创作者中心",
                    error_code="NOT_LOGGED_IN",
                )

            adapted_content = self.adapt_content(content)

            # 导航到发布页面
            await page.goto(f"{self.platform_url}/creator-micro/content/upload", wait_until="networkidle")
            await asyncio.sleep(2)

            # 上传视频或图片
            if adapted_content.video:
                await self._upload_video(page, adapted_content.video)
            elif adapted_content.images:
                await self._upload_images(page, adapted_content.images)
            else:
                return PublishResult(
                    success=False,
                    error="抖音发布必须包含视频或图片",
                    error_code="NO_MEDIA",
                )

            await asyncio.sleep(5)

            # 填写标题
            if adapted_content.title:
                await self._fill_title(page, adapted_content.title)

            # 填写描述
            if adapted_content.content:
                await self._fill_content(page, adapted_content.content)

            # 添加话题
            if adapted_content.hashtags:
                await self._add_hashtags(page, adapted_content.hashtags)

            # 发布
            await self._click_publish(page)

            return await self._wait_for_result(page)

        except Exception as e:
            return PublishResult(
                success=False,
                error=f"发布失败: {str(e)}",
                error_code="PUBLISH_ERROR",
            )

    async def get_content_constraints(self) -> ContentConstraints:
        """获取抖音内容约束"""
        return ContentConstraints(
            max_title_length=55,
            min_title_length=0,
            title_required=False,
            max_content_length=2200,
            min_content_length=0,
            max_images=35,
            min_images=0,
            max_image_size_mb=20.0,
            allowed_image_formats=["jpg", "jpeg", "png"],
            max_video_duration=900,  # 15分钟
            max_video_size_mb=4096.0,  # 4GB
            allowed_video_formats=["mp4", "mov"],
            max_hashtags=5,
            max_mentions=10,
            allow_external_links=False,
            allow_internal_links=True,
            supported_content_types=[ContentType.VIDEO, ContentType.IMAGE_TEXT],
        )

    def adapt_content(self, content: PublishContent) -> PublishContent:
        """适配内容到抖音规范"""
        return PublishContent(
            title=content.title[:55] if content.title else None,
            content=content.content[:2200] if content.content else "",
            images=content.images[:35],
            video=content.video,
            cover_image=content.cover_image,
            hashtags=content.hashtags[:5],
            mentions=content.mentions[:10],
            location=content.location,
            scheduled_at=content.scheduled_at,
            visibility=content.visibility,
            platform_specific=content.platform_specific,
        )

    async def verify_login(self, page: Any) -> bool:
        """验证抖音登录状态"""
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

    async def _upload_images(self, page: Any, images: List[str]):
        """上传图片"""
        file_input = await page.query_selector(self.SELECTORS["upload_image"])
        if file_input:
            await file_input.set_input_files(images)

    async def _fill_title(self, page: Any, title: str):
        """填写标题"""
        title_input = await page.query_selector(self.SELECTORS["title_input"])
        if title_input:
            await title_input.fill(title)

    async def _fill_content(self, page: Any, content: str):
        """填写描述"""
        content_input = await page.query_selector(self.SELECTORS["content_input"])
        if content_input:
            await content_input.fill(content)

    async def _add_hashtags(self, page: Any, hashtags: List[str]):
        """添加话题"""
        tag_input = await page.query_selector(self.SELECTORS["tag_input"])
        if tag_input:
            for tag in hashtags[:5]:
                await tag_input.fill(f"#{tag}")
                await page.keyboard.press("Enter")
                await asyncio.sleep(0.5)

    async def _click_publish(self, page: Any):
        """点击发布"""
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
                metadata={"platform": "douyin"},
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

        if not content.images and not content.video:
            errors.append("抖音发布必须包含视频或图片")

        if content.title and len(content.title) > 55:
            errors.append("标题不能超过55个字符")

        if content.content and len(content.content) > 2200:
            errors.append("描述不能超过2200个字符")

        return errors
