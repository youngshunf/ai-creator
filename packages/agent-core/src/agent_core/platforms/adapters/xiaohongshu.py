"""
小红书平台适配器

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


class XiaohongshuAdapter(PlatformAdapter):
    """小红书平台适配器"""

    # 平台标识（必须）
    platform_name = "xiaohongshu"
    
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
        """检查小红书登录状态"""
        # 1. 检查是否在登录页
        if "/login" in current_url:
            return LoginResult(is_logged_in=False)

        # 2. 检查 localStorage 中的用户信息
        user_id = None
        for key, value in local_storage.items():
            if key == "USER_INFO" or key == "USER_INFO_FOR_BIZ":
                try:
                    user_data = json.loads(value) if isinstance(value, str) else value
                    user_id = user_data.get("user_id") or user_data.get("userId")
                    if user_id:
                        return LoginResult(is_logged_in=True, platform_user_id=user_id)
                except Exception:
                    pass
            # 检查搜索历史键 xhs-pc-search-history-{userId}
            if key.startswith("xhs-pc-search-history-"):
                user_id = key.replace("xhs-pc-search-history-", "")
                return LoginResult(is_logged_in=True, platform_user_id=user_id)

        # 3. 检查关键 cookie
        has_user_id = any(c.get("name") == "customerClientId" for c in cookies)
        has_session = any(c.get("name") == "web_session" for c in cookies)

        if has_user_id and has_session:
            # 从 cookie 提取 user_id
            for c in cookies:
                if c.get("name") == "customerClientId":
                    user_id = c.get("value")
                    break
            return LoginResult(is_logged_in=True, platform_user_id=user_id)

        return LoginResult(is_logged_in=False)

    async def get_user_profile(self, page: Any) -> Optional[UserProfile]:
        """获取小红书用户资料 - 导航到个人主页并提取信息"""
        try:
            # 先从 localStorage 获取用户 ID
            storage_str = await page.evaluate("() => JSON.stringify(localStorage)")
            storage = json.loads(storage_str) if storage_str else {}
            logger.info(f"[XHS] localStorage keys: {list(storage.keys())}")

            platform_user_id = None
            for key in storage:
                if key.startswith("xhs-pc-search-history-"):
                    platform_user_id = key.replace("xhs-pc-search-history-", "")
                    break

            if not platform_user_id:
                logger.warning("[XHS] 无法从 localStorage 获取用户 ID")
                return None

            # 导航到正确的个人主页 URL - 使用配置中的模板
            profile_url = self.get_profile_url(platform_user_id)
            if not profile_url:
                profile_url = f"https://www.xiaohongshu.com/user/profile/{platform_user_id}"
            
            logger.info(f"[XHS] 导航到: {profile_url}")
            await page.goto(profile_url, wait_until="networkidle", timeout=30000)
            
            # 等待关键元素出现（用户信息区域）
            try:
                await page.wait_for_selector(
                    '.user-info, .info-part, [class*="user-name"], [class*="nickname"]',
                    timeout=10000
                )
            except Exception:
                logger.warning("[XHS] 等待用户信息元素超时，继续尝试提取")
            await page.wait_for_timeout(2000)

            # 提取用户信息 - 使用通用的选择器
            profile_data = await page.evaluate("""
            () => {
                // 尝试多种选择器获取昵称
                const getName = () => {
                    const selectors = [
                        '.user-name',
                        '.nickname',
                        '[class*="nickname"]',
                        '[class*="userName"]',
                        '[class*="user-name"]',
                        'h1',
                        '.info-part .name',
                        '[data-v-user-name]'
                    ];
                    for (const sel of selectors) {
                        const el = document.querySelector(sel);
                        if (el && el.textContent.trim()) {
                            return el.textContent.trim();
                        }
                    }
                    return null;
                };

                const getAvatar = () => {
                    const selectors = [
                        '.user-avatar img',
                        '[class*="avatar"] img',
                        '.avatar img',
                        'img[class*="avatar"]'
                    ];
                    for (const sel of selectors) {
                        const el = document.querySelector(sel);
                        if (el && el.src) {
                            return el.src;
                        }
                    }
                    return null;
                };

                // 获取数字统计
                const getStats = () => {
                    const stats = { 
                        followers: null, 
                        following: null, 
                        likes: null, 
                        posts: null,
                        collects: null 
                    };
                    const allText = document.body.innerText;

                    // 粉丝数
                    const followersMatch = allText.match(/([\\d.]+[万kKmM]?)\\s*粉丝/) || 
                                          allText.match(/粉丝\\s*([\\d.]+[万kKmM]?)/);
                    // 关注数
                    const followingMatch = allText.match(/([\\d.]+[万kKmM]?)\\s*关注/) || 
                                          allText.match(/关注\\s*([\\d.]+[万kKmM]?)/);
                    // 获赞与收藏数
                    const likesMatch = allText.match(/获赞[与和收藏]*\\s*([\\d.]+[万kKmM]?)/) || 
                                      allText.match(/([\\d.]+[万kKmM]?)\\s*获赞/);
                    // 笔记/作品数
                    const postsMatch = allText.match(/([\\d.]+[万kKmM]?)\\s*笔记/) || 
                                      allText.match(/笔记\\s*([\\d.]+[万kKmM]?)/) ||
                                      allText.match(/([\\d.]+[万kKmM]?)\\s*作品/) || 
                                      allText.match(/作品\\s*([\\d.]+[万kKmM]?)/);
                    // 收藏数
                    const collectsMatch = allText.match(/([\\d.]+[万kKmM]?)\\s*收藏/) || 
                                         allText.match(/收藏\\s*([\\d.]+[万kKmM]?)/);

                    if (followersMatch) stats.followers = followersMatch[1];
                    if (followingMatch) stats.following = followingMatch[1];
                    if (likesMatch) stats.likes = likesMatch[1];
                    if (postsMatch) stats.posts = postsMatch[1];
                    if (collectsMatch) stats.collects = collectsMatch[1];

                    return stats;
                };

                const stats = getStats();
                return {
                    nickname: getName(),
                    avatar: getAvatar(),
                    followers: stats.followers,
                    following: stats.following,
                    likes: stats.likes,
                    posts: stats.posts,
                    collects: stats.collects
                };
            }""")

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
                platform_user_id=platform_user_id,
                nickname=profile_data.get("nickname"),
                avatar_url=profile_data.get("avatar"),
                followers_count=parse_count(profile_data.get("followers")),
                following_count=parse_count(profile_data.get("following")),
                posts_count=parse_count(profile_data.get("posts")),
                likes_count=parse_count(profile_data.get("likes")),
                extra={
                    "collects_count": parse_count(profile_data.get("collects")),
                },
            )
        except Exception as e:
            logger.error(f"[XHS] 获取用户资料失败: {e}")
            return None

    async def publish(self, page: Any, content: AdaptedContent) -> PublishResult:
        """小红书发布实现"""
        try:
            # 1. 导航到发布页 - 使用配置中的 URL
            publish_url = self.get_url("publish")
            if not publish_url:
                publish_url = "https://creator.xiaohongshu.com/publish/publish?source=official"
            
            logger.info(f"[XHS] 正在跳转发布页: {publish_url}")
            await page.goto(publish_url, wait_until="networkidle")
            await page.wait_for_timeout(3000)
            
            # 2. 上传图片/视频 - 使用配置中的选择器
            if content.images:
                logger.info(f"[XHS] 上传图片: {len(content.images)} 张")
                upload_selector = self.get_selector("upload_image", "input[type='file']")
                file_input = await page.wait_for_selector(upload_selector)
                if file_input:
                    await file_input.set_input_files(content.images)
                    # 等待上传完成
                    await page.wait_for_timeout(5000)
            
            # 3. 填写标题 - 使用配置中的选择器
            logger.info(f"[XHS] 填写标题: {content.title}")
            title_selector = self.get_selector("title_input", "input[placeholder*='标题']")
            title_input = await page.wait_for_selector(title_selector, timeout=5000)
            if title_input:
                await title_input.fill(content.title)
            
            # 4. 填写正文 - 使用配置中的选择器
            logger.info("[XHS] 填写正文")
            content_selector = self.get_selector(
                "content_input",
                ".ql-editor, textarea[placeholder*='正文']"
            )
            content_input = await page.wait_for_selector(content_selector, timeout=5000)
            if content_input:
                # 处理 hashtags: 拼接到正文后面
                final_content = content.content
                if content.hashtags:
                    # 使用配置中的 hashtag 格式
                    hashtag_format = self.spec.hashtag_format
                    tags = [hashtag_format.replace("{tag}", tag) for tag in content.hashtags]
                    final_content += " " + " ".join(tags)
                
                await content_input.fill(final_content)
                
            # 5. 点击发布 - 使用配置中的选择器
            logger.info("[XHS] 点击发布按钮")
            submit_selector = self.get_selector(
                "submit_btn",
                "button.publish-btn, button:has-text('发布')"
            )
            submit_btn = await page.wait_for_selector(submit_selector, timeout=5000)
            if submit_btn:
                is_disabled = await submit_btn.is_disabled()
                if not is_disabled:
                    await submit_btn.click()
                    
                    # 6. 等待发布成功确认
                    success_selector = self.get_selector(
                        "success_indicator",
                        "text=发布成功"
                    )
                    try:
                        await page.wait_for_selector(success_selector, timeout=10000)
                        logger.info("[XHS] 发布成功 detected")
                        return PublishResult(success=True)
                    except Exception:
                        # 也许跳转到了管理页
                        if "manage" in page.url:
                            return PublishResult(success=True)
                        logger.warning("[XHS] 未检测到明确的发布成功信号，但已点击发布")
                        return PublishResult(
                            success=True,
                            error_message="可能需人工确认"
                        )
                else:
                    return PublishResult(
                        success=False,
                        error_message="发布按钮不可点击，可能是内容校验未通过"
                    )
            
            return PublishResult(success=False, error_message="找不到发布按钮")
            
        except Exception as e:
            logger.error(f"[XHS] 发布过程出错: {e}")
            # 截图保存现场
            try:
                import os
                os.makedirs("debug_screenshots", exist_ok=True)
                await page.screenshot(
                    path=f"debug_screenshots/xhs_publish_error_{int(time.time())}.png"
                )
            except Exception:
                pass
            return PublishResult(success=False, error_message=str(e))
