"""
Bilibili 平台适配器

从 sidecar 迁移，使用统一基类和 YAML 配置。

@author Ysf
@date 2026-01-22
"""

import json
import logging
import time
from typing import Any, Optional, List, Dict

from ..adapter import PlatformAdapter
from ..models import AdaptedContent, LoginResult, UserProfile, PublishResult

logger = logging.getLogger(__name__)


class BilibiliAdapter(PlatformAdapter):
    """Bilibili 平台适配器"""

    # 平台标识（必须）
    platform_name = "bilibili"
    
    # 以下属性由基类从 YAML 配置自动加载：
    # - platform_display_name
    # - login_url
    # - spec

    async def check_login_status(
        self,
        cookies: List[Dict],
        local_storage: Dict[str, Any],
        current_url: str,
    ) -> LoginResult:
        """检查 Bilibili 登录状态"""
        # 1. 检查关键 cookie
        has_sessdata = any(c.get("name") == "SESSDATA" for c in cookies)
        has_bili_jct = any(c.get("name") == "bili_jct" for c in cookies)

        if has_sessdata and has_bili_jct:
            # 尝试从 cookie 提取 DedeUserID
            user_id = None
            for c in cookies:
                if c.get("name") == "DedeUserID":
                    user_id = c.get("value")
                    break
            return LoginResult(is_logged_in=True, platform_user_id=user_id)

        # 2. 检查是否在创作中心且有特定元素
        if "member.bilibili.com" in current_url:
            return LoginResult(is_logged_in=True)

        return LoginResult(is_logged_in=False)

    async def get_user_profile(self, page: Any) -> Optional[UserProfile]:
        """获取 Bilibili 用户资料"""
        try:
            # 导航到创作中心首页 - 使用配置中的 URL
            creator_url = self.get_url("creator")
            if not creator_url:
                creator_url = "https://member.bilibili.com/platform/home"
            
            logger.info(f"[Bilibili] 导航到创作中心: {creator_url}")
            await page.goto(creator_url, wait_until="networkidle", timeout=15000)
            await page.wait_for_timeout(2000)

            # 提取用户信息
            profile_data = await page.evaluate("""() => {
                const getName = () => {
                    const el = document.querySelector('.h-name') || 
                               document.querySelector('.header-entry-mini');
                    return el ? el.textContent.trim() : null;
                };
                const getAvatar = () => {
                    const el = document.querySelector('.h-avatar img') || 
                               document.querySelector('.header-avatar-mini img');
                    return el ? el.src : null;
                };
                const getStats = () => {
                    const stats = { followers: null, likes: null, plays: null };
                    const items = document.querySelectorAll('.cc-nav-item, .data-card-item');
                    for (const item of items) {
                        const text = item.textContent;
                        if (text.includes('粉丝')) {
                            stats.followers = item.querySelector('.num-text')?.textContent || 
                                             text.match(/[\\d.]+[万kKmM]?/)?.[0];
                        }
                        if (text.includes('获赞') || text.includes('点赞')) {
                            stats.likes = item.querySelector('.num-text')?.textContent || 
                                         text.match(/[\\d.]+[万kKmM]?/)?.[0];
                        }
                        if (text.includes('播放')) {
                            stats.plays = item.querySelector('.num-text')?.textContent || 
                                         text.match(/[\\d.]+[万kKmM]?/)?.[0];
                        }
                    }
                    return stats;
                };
                
                // 获取 UID
                const getUid = () => {
                   const el = document.querySelector('.h-user-id') || 
                              document.querySelector('.header-entry-mini');
                   if (el && el.href) {
                       const match = el.href.match(/space\\.bilibili\\.com\\/(\\d+)/);
                       if (match) return match[1];
                   }
                   return null;
                };

                const stats = getStats();
                return { 
                    nickname: getName(), 
                    avatar: getAvatar(), 
                    uid: getUid(),
                    ...stats 
                };
            }""")

            # 如果没有获取到 UID，尝试从 Cookie 获取
            user_id = profile_data.get("uid")
            if not user_id:
                cookies = await page.context.cookies()
                for c in cookies:
                    if c.get("name") == "DedeUserID":
                        user_id = c.get("value")
                        break
            
            if not user_id:
                logger.warning("[Bilibili] 无法获取 User ID")
                return None

            def parse_count(val):
                if not val:
                    return None
                val = str(val).replace(',', '').strip()
                if '万' in val:
                    return int(float(val.replace('万', '')) * 10000)
                if '亿' in val:
                    return int(float(val.replace('亿', '')) * 100000000)
                try:
                    return int(float(val))
                except Exception:
                    return None

            return UserProfile(
                platform_user_id=user_id,
                nickname=profile_data.get("nickname"),
                avatar_url=profile_data.get("avatar"),
                followers_count=parse_count(profile_data.get("followers")),
                likes_count=parse_count(profile_data.get("likes")),
                extra={
                    "plays_count": parse_count(profile_data.get("plays"))
                }
            )

        except Exception as e:
            logger.error(f"[Bilibili] 获取用户信息失败: {e}")
            return None

    async def publish(self, page: Any, content: AdaptedContent) -> PublishResult:
        """Bilibili 视频发布实现"""
        try:
            # 1. 导航到发布页 - 使用配置中的 URL
            publish_url = self.get_url("publish")
            if not publish_url:
                publish_url = "https://member.bilibili.com/platform/upload/video/frame"
            
            logger.info(f"[Bilibili] 正在跳转发布页: {publish_url}")
            await page.goto(publish_url, wait_until="networkidle")
            await page.wait_for_timeout(3000)

            # 2. 上传视频
            if not content.videos:
                return PublishResult(success=False, error_message="Bilibili 发布需要视频文件")
            
            logger.info(f"[Bilibili] 上传视频: {content.videos[0]}")
            upload_selector = self.get_selector(
                "upload_video",
                "input[type='file'][accept*='video'], input[type='file']"
            )
            file_input = await page.wait_for_selector(upload_selector, timeout=10000)
            if file_input:
                await file_input.set_input_files(content.videos[0])
                logger.info("[Bilibili] 等待视频上传和转码预处理...")
                try:
                    title_selector = self.get_selector(
                        "title_input",
                        "input[placeholder*='标题'], .video-title input"
                    )
                    await page.wait_for_selector(title_selector, timeout=60000)
                except Exception:
                    logger.warning("[Bilibili] 等待编辑页面超时，可能上传太慢或已在编辑页")

            # 3. 填写标题
            logger.info(f"[Bilibili] 填写标题: {content.title}")
            title_selector = self.get_selector(
                "title_input",
                "input[placeholder*='标题'], .video-title input"
            )
            title_input = await page.wait_for_selector(title_selector, timeout=5000)
            if title_input:
                await title_input.fill(content.title)

            # 4. 填写简介 (正文)
            logger.info("[Bilibili] 填写简介")
            content_selector = self.get_selector(
                "content_input",
                "textarea[placeholder*='简介'], .video-desc textarea"
            )
            desc_input = await page.wait_for_selector(content_selector, timeout=5000)
            if desc_input:
                final_content = content.content
                if content.hashtags:
                    hashtag_format = self.spec.hashtag_format
                    tags = [hashtag_format.replace("{tag}", tag) for tag in content.hashtags]
                    final_content += "\n" + " ".join(tags)
                await desc_input.fill(final_content)

            # 5. 填写标签
            if content.hashtags:
                logger.info("[Bilibili] 填写标签")
                tag_selector = self.get_selector(
                    "tag_input",
                    "input[placeholder*='标签'], .tag-input input"
                )
                tag_input = await page.wait_for_selector(tag_selector, timeout=5000)
                if tag_input:
                    for tag in content.hashtags[:5]:  # B站限制标签数量
                        await tag_input.fill(tag)
                        await page.keyboard.press("Enter")
                        await page.wait_for_timeout(500)
            
            # 6. 选择分区 (如果需要)
            try:
                type_select = await page.wait_for_selector(
                    ".select-item-cont, .type-check-item",
                    timeout=3000
                )
                if type_select:
                    await type_select.click()
            except Exception:
                pass

            # 7. 点击发布
            logger.info("[Bilibili] 点击投稿按钮")
            submit_selector = self.get_selector(
                "submit_btn",
                "span:has-text('立即投稿'), div:has-text('立即投稿')"
            )
            submit_btn = await page.wait_for_selector(submit_selector, timeout=5000)
            if submit_btn:
                await submit_btn.click()
                
                # 8. 等待成功
                success_selector = self.get_selector("success_indicator", "text=投稿成功")
                try:
                    await page.wait_for_selector(success_selector, timeout=10000)
                    logger.info("[Bilibili] 投稿成功")
                    return PublishResult(success=True)
                except Exception:
                    logger.warning("[Bilibili] 未检测到明确的成功信号")
                    error_msg = await page.evaluate(
                        "() => document.querySelector('.error-text')?.textContent"
                    )
                    if error_msg:
                        return PublishResult(
                            success=False,
                            error_message=f"投稿失败: {error_msg}"
                        )
                    return PublishResult(success=True, error_message="可能需人工确认")

            return PublishResult(success=False, error_message="找不到发布按钮")

        except Exception as e:
            logger.error(f"[Bilibili] 发布出错: {e}")
            try:
                import os
                os.makedirs("debug_screenshots", exist_ok=True)
                await page.screenshot(
                    path=f"debug_screenshots/bili_publish_error_{int(time.time())}.png"
                )
            except Exception:
                pass
            return PublishResult(success=False, error_message=str(e))
