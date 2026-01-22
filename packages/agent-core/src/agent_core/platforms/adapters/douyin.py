"""
抖音平台适配器

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


class DouyinAdapter(PlatformAdapter):
    """抖音平台适配器"""

    # 平台标识（必须）
    platform_name = "douyin"
    
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
        """检查抖音创作者平台登录状态"""
        # 检查关键 cookie
        has_session = any(c.get("name") == "sessionid_ss" for c in cookies)

        if has_session:
            # 从 cookie 提取 user_id
            user_id = None
            for c in cookies:
                if c.get("name") == "LOGIN_STATUS":
                    user_id = c.get("value")
                    break
            
            # 如果 cookie 中没有 user_id，尝试从 localStorage 获取
            if not user_id and local_storage:
                try:
                    # 1. 尝试从 __tea_cache_tokens_* 获取
                    for key, value in local_storage.items():
                        if key.startswith("__tea_cache_tokens_") and isinstance(value, str):
                            try:
                                data = json.loads(value)
                                if "user_unique_id" in data:
                                    uid = data["user_unique_id"]
                                    if uid and uid.isdigit():
                                        user_id = uid
                                        break
                            except Exception:
                                continue
                    
                    # 2. 尝试从 SLARDARdouyin_creator_longvideo 获取
                    if not user_id:
                        for key, value in local_storage.items():
                            if key == "SLARDARdouyin_creator_longvideo" and isinstance(value, str):
                                try:
                                    data = json.loads(value)
                                    if "userId" in data:
                                        user_id = data["userId"]
                                        break
                                except Exception:
                                    continue

                except Exception as e:
                    logger.warning(f"[Douyin] 从 localStorage 提取 UserID 失败: {e}")
            
            if not user_id and "/creator-micro" in current_url:
                return LoginResult(is_logged_in=True)

            if user_id:
                return LoginResult(is_logged_in=True, platform_user_id=user_id)

        return LoginResult(is_logged_in=False)

    async def get_user_profile(self, page: Any) -> Optional[UserProfile]:
        """获取抖音用户资料 - 导航到创作者中心获取信息"""
        try:
            # 导航到创作者中心首页 - 使用配置中的 URL
            creator_url = self.get_url("creator")
            if not creator_url:
                creator_url = "https://creator.douyin.com/creator-micro/home"
            
            logger.info(f"[Douyin] 正在导航到创作者中心: {creator_url}")
            await page.goto(creator_url, wait_until="networkidle", timeout=15000)
            await page.wait_for_timeout(2000)

            # 提取用户信息
            profile_data = await page.evaluate("""() => {
                const getName = () => {
                    const el = document.querySelector('[class*="nickname"]') || 
                               document.querySelector('[class*="name"]');
                    return el ? el.textContent.trim() : null;
                };
                const getAvatar = () => {
                    const el = document.querySelector('[class*="avatar"] img') || 
                               document.querySelector('.user-avatar img');
                    return el ? el.src : null;
                };
                const getStats = () => {
                    const stats = {};
                    const items = document.querySelectorAll('[class*="stat"], [class*="count"], [class*="data-item"]');
                    for (const item of items) {
                        const text = item.textContent;
                        if (text.includes('粉丝')) stats.followers = text.match(/[\\d.]+[万kKmM]?/)?.[0];
                        if (text.includes('关注')) stats.following = text.match(/[\\d.]+[万kKmM]?/)?.[0];
                        if (text.includes('获赞')) stats.likes = text.match(/[\\d.]+[万kKmM]?/)?.[0];
                        if (text.includes('作品')) stats.posts = text.match(/[\\d.]+[万kKmM]?/)?.[0];
                    }
                    return stats;
                };
                return { nickname: getName(), avatar: getAvatar(), ...getStats() };
            }""")
            
            logger.info(f"[Douyin] 页面提取数据: {profile_data}")

            # 尝试从 URL 或页面获取用户 ID
            user_id = await page.evaluate("""() => {
                const match = window.location.href.match(/user\\/([\\w]+)/);
                if (match) return match[1];
                const el = document.querySelector('[data-user-id]');
                return el ? el.getAttribute('data-user-id') : null;
            }""")

            if not user_id:
                cookies = await page.context.cookies()
                for c in cookies:
                    if c.get("name") == "LOGIN_STATUS":
                        user_id = c.get("value")
                        break
            
            if not user_id:
                logger.info("[Douyin] 尝试从 localStorage 获取 UserID")
                try:
                    local_storage_str = await page.evaluate("() => JSON.stringify(localStorage)")
                    if local_storage_str:
                        local_storage = json.loads(local_storage_str)
                        for key, value in local_storage.items():
                            if key.startswith("__tea_cache_tokens_") and isinstance(value, str):
                                try:
                                    data = json.loads(value)
                                    if "user_unique_id" in data:
                                        uid = data["user_unique_id"]
                                        if uid and uid.isdigit():
                                            user_id = uid
                                            break
                                except Exception:
                                    continue
                except Exception as e:
                    logger.warning(f"[Douyin] localStorage 提取失败: {e}")

            if not user_id:
                logger.warning("[Douyin] 无法获取 UserID")
                return None
            
            logger.info(f"[Douyin] 获取到 UserID: {user_id}")

            def parse_count(val):
                if not val:
                    return None
                val = str(val).replace(',', '')
                if '万' in val or 'w' in val.lower():
                    return int(float(val.replace('万', '').replace('w', '').replace('W', '')) * 10000)
                if 'k' in val.lower():
                    return int(float(val.replace('k', '').replace('K', '')) * 1000)
                if 'm' in val.lower():
                    return int(float(val.replace('m', '').replace('M', '')) * 1000000)
                try:
                    return int(float(val))
                except Exception:
                    return None

            return UserProfile(
                platform_user_id=user_id,
                nickname=profile_data.get("nickname"),
                avatar_url=profile_data.get("avatar"),
                followers_count=parse_count(profile_data.get("followers")),
                following_count=parse_count(profile_data.get("following")),
                likes_count=parse_count(profile_data.get("likes")),
                posts_count=parse_count(profile_data.get("posts")),
            )
        except Exception as e:
            logger.error(f"[Douyin] 获取用户资料失败: {e}")
            return None

    async def publish(self, page: Any, content: AdaptedContent) -> PublishResult:
        """抖音发布实现"""
        try:
            # 1. 导航到发布页 - 使用配置中的 URL
            publish_url = self.get_url("publish")
            if not publish_url:
                publish_url = "https://creator.douyin.com/creator-micro/content/upload"
            
            logger.info(f"[Douyin] 正在跳转发布页: {publish_url}")
            await page.goto(publish_url, wait_until="networkidle")
            await page.wait_for_timeout(3000)

            # 2. 上传视频
            if not content.videos:
                return PublishResult(success=False, error_message="抖音发布需要视频文件")
            
            logger.info(f"[Douyin] 上传视频: {content.videos[0]}")
            upload_selector = self.get_selector(
                "upload_video",
                "input[type='file'][accept*='video'], input[type='file']"
            )
            try:
                file_input = await page.wait_for_selector(upload_selector, timeout=10000)
                if file_input:
                    await file_input.set_input_files(content.videos[0])
                else:
                    upload_area = await page.wait_for_selector(
                        "div[class*='upload-btn'], div:has-text('点击上传')",
                        timeout=5000
                    )
                    if upload_area:
                        async with page.expect_file_chooser() as fc_info:
                            await upload_area.click()
                        file_chooser = await fc_info.value
                        await file_chooser.set_files(content.videos[0])
            except Exception as e:
                logger.error(f"[Douyin] 上传文件步骤失败: {e}")
                return PublishResult(success=False, error_message=f"上传视频失败: {e}")

            # 等待上传进度条完成或进入编辑页
            logger.info("[Douyin] 等待视频上传...")
            title_selector = self.get_selector("title_input", "input[placeholder*='标题']")
            try:
                await page.wait_for_selector(title_selector, timeout=60000)
            except Exception:
                logger.warning("[Douyin] 等待编辑页面超时")

            # 3. 填写描述
            logger.info(f"[Douyin] 填写描述: {content.title}")
            content_selector = self.get_selector(
                "content_input",
                "div[contenteditable='true'], textarea[placeholder*='描述']"
            )
            desc_input = await page.wait_for_selector(content_selector, timeout=5000)
            
            if desc_input:
                final_content = content.title + "\n" + content.content
                if content.hashtags:
                    hashtag_format = self.spec.hashtag_format
                    tags = [hashtag_format.replace("{tag}", tag) for tag in content.hashtags]
                    final_content += " " + " ".join(tags)
                
                await desc_input.click()
                await page.keyboard.type(final_content)

            # 4. 点击发布
            logger.info("[Douyin] 点击发布按钮")
            submit_selector = self.get_selector(
                "submit_btn",
                "button:has-text('发布'), div:has-text('发布'):not([disabled])"
            )
            submit_btn = await page.wait_for_selector(submit_selector, timeout=5000)
            if submit_btn:
                if await submit_btn.is_disabled():
                    return PublishResult(
                        success=False,
                        error_message="发布按钮被禁用，可能还在上传或校验"
                    )
                
                await submit_btn.click()
                
                # 5. 等待成功
                success_selector = self.get_selector("success_indicator", "text=发布成功")
                try:
                    await page.wait_for_selector(success_selector, timeout=10000)
                    logger.info("[Douyin] 发布成功")
                    return PublishResult(success=True)
                except Exception:
                    if await page.query_selector("div[class*='success']"):
                        return PublishResult(success=True)
                    
                    logger.warning("[Douyin] 未检测到明确的成功信号")
                    return PublishResult(success=True, error_message="可能需人工确认")

            return PublishResult(success=False, error_message="找不到发布按钮")

        except Exception as e:
            logger.error(f"[Douyin] 发布出错: {e}")
            try:
                import os
                os.makedirs("debug_screenshots", exist_ok=True)
                await page.screenshot(
                    path=f"debug_screenshots/douyin_publish_error_{int(time.time())}.png"
                )
            except Exception:
                pass
            return PublishResult(success=False, error_message=str(e))
