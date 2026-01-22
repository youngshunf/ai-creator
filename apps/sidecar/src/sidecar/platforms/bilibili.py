"""
Bilibili 平台适配器
@author Ysf
"""

import json
import logging
import time
from typing import Any, Optional

from .base import PlatformAdapter, ContentSpec, LoginResult, UserProfile, AdaptedContent, PublishResult


class BilibiliAdapter(PlatformAdapter):
    """Bilibili 平台适配器"""

    platform_name = "bilibili"
    platform_display_name = "哔哩哔哩"
    login_url = "https://passport.bilibili.com/login"

    @property
    def spec(self) -> ContentSpec:
        return ContentSpec(
            title_max_length=80,
            title_min_length=1,
            content_max_length=2000,
            content_min_length=0,
            image_max_count=0,  # 主要是视频平台
            image_min_count=0,
            video_max_count=1,
            video_max_duration=36000,  # 10小时
            supported_formats=["video"],
            hashtag_max_count=10,
            mention_supported=False,
            location_supported=False,
        )

    async def check_login_status(
        self, cookies: list[dict], local_storage: dict[str, Any], current_url: str
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
             # 如果能访问创作中心，通常意味着已登录
            return LoginResult(is_logged_in=True)

        return LoginResult(is_logged_in=False)

    async def get_user_profile(self, page: Any) -> Optional[UserProfile]:
        """获取 Bilibili 用户资料"""
        logger = logging.getLogger(__name__)
        try:
            # 导航到创作中心首页
            logger.info("[Bilibili] 导航到创作中心获取用户信息...")
            await page.goto("https://member.bilibili.com/platform/home", wait_until="networkidle", timeout=15000)
            await page.wait_for_timeout(2000)

            # 提取用户信息
            profile_data = await page.evaluate("""() => {
                const getName = () => {
                    const el = document.querySelector('.h-name') || document.querySelector('.header-entry-mini');
                    return el ? el.textContent.trim() : null;
                };
                const getAvatar = () => {
                    const el = document.querySelector('.h-avatar img') || document.querySelector('.header-avatar-mini img');
                    return el ? el.src : null;
                };
                const getStats = () => {
                    const stats = { followers: null, likes: null, plays: null };
                    // 尝试从创作中心首页的数据概览获取
                    const items = document.querySelectorAll('.cc-nav-item, .data-card-item');
                    for (const item of items) {
                        const text = item.textContent;
                        if (text.includes('粉丝')) stats.followers = item.querySelector('.num-text')?.textContent || text.match(/[\\d.]+[万kKmM]?/)?.[0];
                        if (text.includes('获赞') || text.includes('点赞')) stats.likes = item.querySelector('.num-text')?.textContent || text.match(/[\\d.]+[万kKmM]?/)?.[0];
                        if (text.includes('播放')) stats.plays = item.querySelector('.num-text')?.textContent || text.match(/[\\d.]+[万kKmM]?/)?.[0];
                    }
                    return stats;
                };
                
                // 获取 UID
                const getUid = () => {
                   const el = document.querySelector('.h-user-id') || document.querySelector('.header-entry-mini');
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
                except:
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
        logger = logging.getLogger(__name__)
        
        try:
            # 1. 导航到发布页
            logger.info("[Bilibili] 正在跳转发布页...")
            # 直接跳转到视频上传页
            await page.goto("https://member.bilibili.com/platform/upload/video/frame", wait_until="networkidle")
            await page.wait_for_timeout(3000)

            # 2. 上传视频
            if not content.videos:
                return PublishResult(success=False, error_message="Bilibili 发布需要视频文件")
            
            logger.info(f"[Bilibili] 上传视频: {content.videos[0]}")
            # 查找上传输入框 - 可能是 iframe 里的，也可能是直接的 input
            # B站现在的上传页面通常是一个 input type=file
            file_input = await page.wait_for_selector("input[type='file'][accept*='video'], input[type='file']", timeout=10000)
            if file_input:
                await file_input.set_input_files(content.videos[0])
                # 等待上传开始和处理
                # B站上传后会自动进入编辑信息页面，需要等待URL变化或元素出现
                logger.info("[Bilibili] 等待视频上传和转码预处理...")
                try:
                    # 等待进入编辑表单页面的标志性元素，例如标题输入框
                    await page.wait_for_selector("input[placeholder*='标题'], .video-title input", timeout=60000) 
                except:
                    logger.warning("[Bilibili] 等待编辑页面超时，可能上传太慢或已在编辑页")

            # 3. 填写标题
            logger.info(f"[Bilibili] 填写标题: {content.title}")
            title_input = await page.wait_for_selector("input[placeholder*='标题'], .video-title input", timeout=5000)
            if title_input:
                await title_input.fill(content.title)

            # 4. 填写简介 (正文)
            logger.info("[Bilibili] 填写简介")
            desc_input = await page.wait_for_selector("textarea[placeholder*='简介'], .video-desc textarea", timeout=5000)
            if desc_input:
                final_content = content.content
                if content.hashtags:
                    final_content += "\n" + " ".join([f"#{tag}" for tag in content.hashtags])
                await desc_input.fill(final_content)

            # 5. 填写标签
            if content.hashtags:
                logger.info("[Bilibili] 填写标签")
                tag_input = await page.wait_for_selector("input[placeholder*='标签'], .tag-input input", timeout=5000)
                if tag_input:
                    for tag in content.hashtags[:5]: # B站限制标签数量
                        await tag_input.fill(tag)
                        await page.keyboard.press("Enter")
                        await page.wait_for_timeout(500)
            
            # 6. 选择分区 (如果需要)
            # 这里可能需要复杂的交互，如果必须选，通常会有默认或推荐。
            # 尝试点击“自动推荐”或选择第一个
            try:
                type_select = await page.wait_for_selector(".select-item-cont, .type-check-item", timeout=3000)
                if type_select:
                    await type_select.click()
            except:
                pass

            # 7. 点击发布
            logger.info("[Bilibili] 点击投稿按钮")
            submit_btn = await page.wait_for_selector("span:has-text('立即投稿'), div:has-text('立即投稿')", timeout=5000)
            if submit_btn:
                await submit_btn.click()
                
                # 8. 等待成功
                try:
                    await page.wait_for_selector("text=投稿成功", timeout=10000)
                    logger.info("[Bilibili] 投稿成功")
                    return PublishResult(success=True)
                except:
                    logger.warning("[Bilibili] 未检测到明确的成功信号")
                    # 检查是否有错误提示
                    error_msg = await page.evaluate("() => document.querySelector('.error-text')?.textContent")
                    if error_msg:
                        return PublishResult(success=False, error_message=f"投稿失败: {error_msg}")
                    return PublishResult(success=True, error_message="可能需人工确认")

            return PublishResult(success=False, error_message="找不到发布按钮")

        except Exception as e:
            logger.error(f"[Bilibili] 发布出错: {e}")
            # 截图
            try:
                import os
                os.makedirs("debug_screenshots", exist_ok=True)
                await page.screenshot(path=f"debug_screenshots/bili_publish_error_{int(time.time())}.png")
            except:
                pass
            return PublishResult(success=False, error_message=str(e))
