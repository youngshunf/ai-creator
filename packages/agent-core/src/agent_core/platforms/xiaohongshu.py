"""
小红书平台适配器 - 实现小红书图文/视频笔记发布

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
class XiaohongshuAdapter(PlatformAdapter):
    """
    小红书平台适配器

    支持图文笔记和视频笔记发布。
    使用 Playwright 浏览器自动化实现。
    """

    platform_type = PlatformType.XIAOHONGSHU
    platform_name = "xiaohongshu"
    platform_display_name = "小红书"
    platform_url = "https://creator.xiaohongshu.com"
    requires_login = True

    # 选择器配置
    SELECTORS = {
        "login_check": 'div[class*="user-info"], div[class*="creator-info"]',
        "publish_btn": 'div[class*="publish-btn"], button:has-text("发布笔记")',
        "upload_image": 'input[type="file"][accept*="image"]',
        "upload_video": 'input[type="file"][accept*="video"]',
        "title_input": 'input[placeholder*="标题"], div[class*="title"] input',
        "content_input": 'div[class*="content"] div[contenteditable="true"], textarea[placeholder*="正文"]',
        "tag_input": 'input[placeholder*="话题"], input[placeholder*="标签"]',
        "submit_btn": 'button:has-text("发布"), button[class*="submit"]',
        "success_indicator": 'div:has-text("发布成功"), div[class*="success"]',
    }

    async def publish(
        self,
        page: Any,
        content: PublishContent,
    ) -> PublishResult:
        """
        发布笔记到小红书

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
                    error="未登录小红书创作者中心",
                    error_code="NOT_LOGGED_IN",
                )

            # 适配内容
            adapted_content = self.adapt_content(content)

            # 导航到发布页面
            await page.goto(f"{self.platform_url}/publish/publish", wait_until="networkidle")
            await asyncio.sleep(2)

            # 上传图片或视频
            if adapted_content.video:
                await self._upload_video(page, adapted_content.video)
            elif adapted_content.images:
                await self._upload_images(page, adapted_content.images)
            else:
                return PublishResult(
                    success=False,
                    error="小红书笔记必须包含图片或视频",
                    error_code="NO_MEDIA",
                )

            # 等待上传完成
            await asyncio.sleep(3)

            # 填写标题
            if adapted_content.title:
                await self._fill_title(page, adapted_content.title)

            # 填写正文
            if adapted_content.content:
                await self._fill_content(page, adapted_content.content)

            # 添加话题标签
            if adapted_content.hashtags:
                await self._add_hashtags(page, adapted_content.hashtags)

            # 点击发布
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
        """获取小红书内容约束"""
        return ContentConstraints(
            max_title_length=20,
            min_title_length=0,
            title_required=False,
            max_content_length=1000,
            min_content_length=5,
            max_images=18,
            min_images=0,
            max_image_size_mb=20.0,
            allowed_image_formats=["jpg", "jpeg", "png", "webp"],
            image_aspect_ratio="3:4",
            max_video_duration=600,
            max_video_size_mb=500.0,
            allowed_video_formats=["mp4", "mov"],
            max_hashtags=10,
            max_mentions=10,
            allow_external_links=False,
            allow_internal_links=True,
            supported_content_types=[ContentType.IMAGE_TEXT, ContentType.VIDEO],
        )

    def adapt_content(self, content: PublishContent) -> PublishContent:
        """适配内容到小红书规范"""
        adapted = PublishContent(
            title=content.title[:20] if content.title else None,
            content=content.content[:1000] if content.content else "",
            images=content.images[:18],
            video=content.video,
            cover_image=content.cover_image,
            hashtags=content.hashtags[:10],
            mentions=content.mentions[:10],
            location=content.location,
            scheduled_at=content.scheduled_at,
            visibility=content.visibility,
            platform_specific=content.platform_specific,
        )

        # 添加话题标签到正文末尾
        if adapted.hashtags and adapted.content:
            tags_text = " ".join([f"#{tag}" for tag in adapted.hashtags])
            if len(adapted.content) + len(tags_text) + 2 <= 1000:
                adapted.content = f"{adapted.content}\n\n{tags_text}"

        return adapted

    async def verify_login(self, page: Any) -> bool:
        """验证小红书登录状态"""
        try:
            await page.goto(self.platform_url, wait_until="networkidle")
            await asyncio.sleep(2)

            # 检查是否有用户信息元素
            login_indicator = await page.query_selector(self.SELECTORS["login_check"])
            return login_indicator is not None

        except Exception:
            return False

    async def _upload_images(self, page: Any, images: List[str]):
        """上传图片"""
        file_input = await page.query_selector(self.SELECTORS["upload_image"])
        if file_input:
            await file_input.set_input_files(images)

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
        """填写正文"""
        content_input = await page.query_selector(self.SELECTORS["content_input"])
        if content_input:
            await content_input.fill(content)

    async def _add_hashtags(self, page: Any, hashtags: List[str]):
        """添加话题标签"""
        tag_input = await page.query_selector(self.SELECTORS["tag_input"])
        if tag_input:
            for tag in hashtags[:5]:  # 最多添加5个话题
                await tag_input.fill(tag)
                await page.keyboard.press("Enter")
                await asyncio.sleep(0.5)

    async def _click_publish(self, page: Any):
        """点击发布按钮"""
        submit_btn = await page.query_selector(self.SELECTORS["submit_btn"])
        if submit_btn:
            await submit_btn.click()

    async def _wait_for_result(self, page: Any, timeout: int = 30) -> PublishResult:
        """等待发布结果"""
        try:
            await page.wait_for_selector(
                self.SELECTORS["success_indicator"],
                timeout=timeout * 1000,
            )

            return PublishResult(
                success=True,
                published_at=datetime.now().isoformat(),
                metadata={"platform": "xiaohongshu"},
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
            errors.append("小红书笔记必须包含图片或视频")

        if content.title and len(content.title) > 20:
            errors.append("标题不能超过20个字符")

        if content.content and len(content.content) > 1000:
            errors.append("正文不能超过1000个字符")

        if content.images and len(content.images) > 18:
            errors.append("图片数量不能超过18张")

        return errors
