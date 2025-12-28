"""
微博平台适配器 - 实现微博发布

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
class WeiboAdapter(PlatformAdapter):
    """
    微博平台适配器

    支持图文微博发布。
    使用 Playwright 浏览器自动化实现。
    """

    platform_type = PlatformType.WEIBO
    platform_name = "weibo"
    platform_display_name = "微博"
    platform_url = "https://weibo.com"
    requires_login = True

    # 选择器配置
    SELECTORS = {
        "login_check": 'div[class*="gn_name"], a[class*="S_txt1"]',
        "compose_btn": 'div[class*="W_input"], textarea[class*="W_input"]',
        "content_input": 'textarea[class*="W_input"], div[contenteditable="true"]',
        "upload_image": 'input[type="file"][accept*="image"]',
        "topic_btn": 'a[title="插入话题"], span:has-text("#")',
        "topic_input": 'input[placeholder*="话题"]',
        "submit_btn": 'button:has-text("发布"), a[class*="W_btn_a"]',
        "success_indicator": 'div:has-text("发布成功"), div[class*="success"]',
    }

    async def publish(
        self,
        page: Any,
        content: PublishContent,
    ) -> PublishResult:
        """
        发布微博

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
                    error="未登录微博",
                    error_code="NOT_LOGGED_IN",
                )

            # 适配内容
            adapted_content = self.adapt_content(content)

            # 导航到首页
            await page.goto(self.platform_url, wait_until="networkidle")
            await asyncio.sleep(2)

            # 点击发布框
            await self._click_compose(page)
            await asyncio.sleep(1)

            # 填写内容
            await self._fill_content(page, adapted_content.content)

            # 上传图片
            if adapted_content.images:
                await self._upload_images(page, adapted_content.images)
                await asyncio.sleep(2)

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
        """获取微博内容约束"""
        return ContentConstraints(
            max_title_length=0,  # 微博没有标题
            min_title_length=0,
            title_required=False,
            max_content_length=2000,
            min_content_length=1,
            max_images=9,
            min_images=0,
            max_image_size_mb=20.0,
            allowed_image_formats=["jpg", "jpeg", "png", "gif"],
            max_video_duration=300,
            max_video_size_mb=500.0,
            allowed_video_formats=["mp4"],
            max_hashtags=10,
            max_mentions=20,
            allow_external_links=True,
            allow_internal_links=True,
            supported_content_types=[ContentType.TEXT, ContentType.IMAGE_TEXT, ContentType.VIDEO],
        )

    def adapt_content(self, content: PublishContent) -> PublishContent:
        """适配内容到微博规范"""
        # 构建微博正文
        text_parts = []

        # 添加标题（如果有）
        if content.title:
            text_parts.append(f"【{content.title}】")

        # 添加正文
        if content.content:
            text_parts.append(content.content)

        # 添加话题标签
        if content.hashtags:
            tags_text = " ".join([f"#{tag}#" for tag in content.hashtags[:10]])
            text_parts.append(tags_text)

        full_content = "\n".join(text_parts)

        # 截断到2000字符
        if len(full_content) > 2000:
            full_content = full_content[:1997] + "..."

        adapted = PublishContent(
            title=None,  # 微博没有标题字段
            content=full_content,
            images=content.images[:9],
            video=content.video,
            cover_image=content.cover_image,
            hashtags=content.hashtags[:10],
            mentions=content.mentions[:20],
            location=content.location,
            scheduled_at=content.scheduled_at,
            visibility=content.visibility,
            platform_specific=content.platform_specific,
        )

        return adapted

    async def verify_login(self, page: Any) -> bool:
        """验证微博登录状态"""
        try:
            await page.goto(self.platform_url, wait_until="networkidle")
            await asyncio.sleep(2)

            # 检查是否有用户信息元素
            login_indicator = await page.query_selector(self.SELECTORS["login_check"])
            return login_indicator is not None

        except Exception:
            return False

    async def _click_compose(self, page: Any):
        """点击发布框"""
        compose_btn = await page.query_selector(self.SELECTORS["compose_btn"])
        if compose_btn:
            await compose_btn.click()

    async def _fill_content(self, page: Any, content: str):
        """填写内容"""
        content_input = await page.query_selector(self.SELECTORS["content_input"])
        if content_input:
            await content_input.fill(content)

    async def _upload_images(self, page: Any, images: List[str]):
        """上传图片"""
        file_input = await page.query_selector(self.SELECTORS["upload_image"])
        if file_input:
            await file_input.set_input_files(images)

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
                metadata={"platform": "weibo"},
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

        if not content.content and not content.images and not content.video:
            errors.append("微博必须包含文字、图片或视频")

        # 计算总长度（包括标题和标签）
        total_length = 0
        if content.title:
            total_length += len(content.title) + 4  # 【】
        if content.content:
            total_length += len(content.content)
        if content.hashtags:
            total_length += sum(len(tag) + 2 for tag in content.hashtags)  # ##

        if total_length > 2000:
            errors.append("微博内容总长度不能超过2000个字符")

        if content.images and len(content.images) > 9:
            errors.append("图片数量不能超过9张")

        return errors
