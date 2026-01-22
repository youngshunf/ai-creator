"""
抖音平台适配器
@author Ysf
"""

import json
import logging
import re
import time
from typing import Any, Optional

from .base import PlatformAdapter, ContentSpec, LoginResult, UserProfile, AdaptedContent, PublishResult


class DouyinAdapter(PlatformAdapter):
    """抖音平台适配器"""

    platform_name = "douyin"
    platform_display_name = "抖音"
    login_url = "https://creator.douyin.com/"

    @property
    def spec(self) -> ContentSpec:
        return ContentSpec(
            title_max_length=55,
            title_min_length=0,
            content_max_length=2200,
            content_min_length=0,
            image_max_count=35,
            image_min_count=0,
            video_max_count=1,
            video_max_duration=900,
            supported_formats=["text", "image", "video"],
            hashtag_max_count=5,
            mention_supported=True,
            location_supported=True,
        )

    async def check_login_status(
        self, cookies: list[dict], local_storage: dict[str, Any], current_url: str
    ) -> LoginResult:
        """检查抖音创作者平台登录状态"""
        # 检查关键 cookie
        has_session = any(c.get("name") == "sessionid_ss" for c in cookies)
        # has_passport = any(c.get("name") == "passport_csrf_token" for c in cookies)

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
                    # 格式: __tea_cache_tokens_2906: {"user_unique_id":"6974395981",...}
                    for key, value in local_storage.items():
                        if key.startswith("__tea_cache_tokens_") and isinstance(value, str):
                            try:
                                data = json.loads(value)
                                if "user_unique_id" in data:
                                    uid = data["user_unique_id"]
                                    # 过滤掉非数字的 ID (有时候是 verify_... 这种)
                                    if uid and uid.isdigit():
                                        user_id = uid
                                        break
                            except:
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
                                 except:
                                     continue

                except Exception as e:
                    logging.getLogger(__name__).warning(f"[Douyin] 从 localStorage 提取 UserID 失败: {e}")
            
            # 如果还是没有 user_id，但在登录页之后，可以认为已登录但未获取到 ID
            # 为了避免一直卡在检查状态，可以先返回 True，后续 get_user_profile 会再次获取
            if not user_id and "/creator-micro" in current_url:
                 # 尝试从 URL 提取（虽然不太可能在 URL 里）
                 return LoginResult(is_logged_in=True)

            if user_id:
                return LoginResult(is_logged_in=True, platform_user_id=user_id)

        return LoginResult(is_logged_in=False)

    async def get_user_profile(self, page: Any) -> Optional[UserProfile]:
        """获取抖音用户资料 - 导航到创作者中心获取信息"""
        logger = logging.getLogger(__name__)
        try:
            # 导航到创作者中心首页
            logger.info("[Douyin] 正在导航到创作者中心首页...")
            await page.goto("https://creator.douyin.com/creator-micro/home", wait_until="networkidle", timeout=15000)
            await page.wait_for_timeout(2000)

            # 提取用户信息
            profile_data = await page.evaluate("""() => {
                const getName = () => {
                    const el = document.querySelector('[class*="nickname"]') || document.querySelector('[class*="name"]');
                    return el ? el.textContent.trim() : null;
                };
                const getAvatar = () => {
                    const el = document.querySelector('[class*="avatar"] img') || document.querySelector('.user-avatar img');
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
                # 从 cookie 获取
                cookies = await page.context.cookies()
                for c in cookies:
                    if c.get("name") == "LOGIN_STATUS":
                        user_id = c.get("value")
                        break
            
            if not user_id:
                 # 从 localStorage 获取
                 logger.info("[Douyin] 尝试从 localStorage 获取 UserID")
                 try:
                     local_storage = await page.evaluate("() => JSON.stringify(localStorage)")
                     if local_storage:
                         local_storage = json.loads(local_storage)
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
                                 except:
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
                                      except:
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
                except:
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
        except Exception:
            return None

    async def publish(self, page: Any, content: AdaptedContent) -> PublishResult:
        """抖音发布实现"""
        logger = logging.getLogger(__name__)
        
        try:
            # 1. 导航到发布页
            logger.info("[Douyin] 正在跳转发布页...")
            await page.goto("https://creator.douyin.com/creator-micro/content/upload", wait_until="networkidle")
            await page.wait_for_timeout(3000)

            # 2. 上传视频
            if not content.videos:
                return PublishResult(success=False, error_message="抖音发布需要视频文件")
            
            logger.info(f"[Douyin] 上传视频: {content.videos[0]}")
            # 抖音上传区域通常有一个 input[type=file]
            # 有时候需要点击触发，有时候可以直接 set_input_files
            try:
                # 尝试直接 set_input_files
                file_input = await page.wait_for_selector("input[type='file'][accept*='video'], input[type='file']", timeout=10000)
                if file_input:
                    await file_input.set_input_files(content.videos[0])
                else:
                    # 如果找不到 input，尝试点击上传区域
                    upload_area = await page.wait_for_selector("div[class*='upload-btn'], div:has-text('点击上传')", timeout=5000)
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
            try:
                # 等待标题输入框出现，意味着上传成功并进入编辑模式
                # 抖音的标题输入框通常 placeholder 含有 "标题" 或 "作品标题"
                await page.wait_for_selector("input[placeholder*='标题']", timeout=60000)
            except:
                logger.warning("[Douyin] 等待编辑页面超时")

            # 3. 填写标题 (抖音网页版其实主要是“作品描述”，标题可能是指第一句话)
            logger.info(f"[Douyin] 填写描述: {content.title}")
            # 抖音网页版只有一个大输入框作为描述
            desc_input = await page.wait_for_selector("div[contenteditable='true'], textarea[placeholder*='描述']", timeout=5000)
            
            if desc_input:
                final_content = content.title + "\n" + content.content
                if content.hashtags:
                    final_content += " " + " ".join([f"#{tag}" for tag in content.hashtags])
                
                # 抖音输入框可能是 rich text，直接 fill 可能不行，尝试 type
                await desc_input.click()
                await page.keyboard.type(final_content)

            # 4. 选择封面 (可选)
            # 略过复杂的封面选择，使用默认

            # 5. 点击发布
            logger.info("[Douyin] 点击发布按钮")
            submit_btn = await page.wait_for_selector("button:has-text('发布'), div:has-text('发布'):not([disabled])", timeout=5000)
            if submit_btn:
                # 检查是否 disable
                if await submit_btn.is_disabled():
                     return PublishResult(success=False, error_message="发布按钮被禁用，可能还在上传或校验")
                
                await submit_btn.click()
                
                # 6. 等待成功
                try:
                    await page.wait_for_selector("text=发布成功", timeout=10000)
                    logger.info("[Douyin] 发布成功")
                    return PublishResult(success=True)
                except:
                    # 检查是否有弹窗提示
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
                await page.screenshot(path=f"debug_screenshots/douyin_publish_error_{int(time.time())}.png")
            except:
                pass
            return PublishResult(success=False, error_message=str(e))
