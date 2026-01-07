"""
小红书平台适配器
@author Ysf
"""

import json
import re
from typing import Any, Optional

from .base import PlatformAdapter, ContentSpec, LoginResult, UserProfile


class XiaohongshuAdapter(PlatformAdapter):
    """小红书平台适配器"""

    platform_name = "xiaohongshu"
    platform_display_name = "小红书"
    login_url = "https://www.xiaohongshu.com/login"

    @property
    def spec(self) -> ContentSpec:
        return ContentSpec(
            title_max_length=20,
            title_min_length=0,
            content_max_length=1000,
            content_min_length=5,
            image_max_count=9,
            image_min_count=0,
            video_max_count=1,
            video_max_duration=300,
            supported_formats=["text", "image", "video"],
            hashtag_max_count=10,
            mention_supported=True,
            location_supported=True,
        )

    async def check_login_status(
        self, cookies: list[dict], local_storage: dict[str, Any], current_url: str
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
                    import json
                    user_data = json.loads(value) if isinstance(value, str) else value
                    user_id = user_data.get("user_id") or user_data.get("userId")
                    if user_id:
                        return LoginResult(is_logged_in=True, platform_user_id=user_id)
                except:
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
        import logging
        logger = logging.getLogger(__name__)
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

            # 导航到正确的个人主页 URL
            profile_url = f"https://www.xiaohongshu.com/user/profile/{platform_user_id}"
            logger.info(f"[XHS] 导航到: {profile_url}")
            await page.goto(profile_url, wait_until="networkidle", timeout=15000)
            await page.wait_for_timeout(3000)

            # 调试：截图保存
            import os
            debug_dir = os.path.expanduser("~/.ai-creator/debug")
            os.makedirs(debug_dir, exist_ok=True)
            await page.screenshot(path=f"{debug_dir}/xhs_profile.png")
            logger.info(f"[XHS] 截图已保存到: {debug_dir}/xhs_profile.png")

            # 调试：获取页面标题和 URL
            current_url = page.url
            title = await page.title()
            logger.info(f"[XHS] 当前 URL: {current_url}, 标题: {title}")

            # 调试：获取页面 HTML 结构
            debug_html = await page.evaluate("""() => {
                // 获取页面主要内容区域的 HTML
                const main = document.querySelector('main') || document.querySelector('#app') || document.body;
                return main.innerHTML.substring(0, 3000);
            }""")
            logger.info(f"[XHS] 页面 HTML 片段: {debug_html[:500]}...")

            # 提取用户信息 - 使用更通用的选择器
            profile_data = await page.evaluate("""() => {
                // 尝试多种选择器获取昵称
                const getName = () => {
                    // 小红书个人主页的昵称选择器
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
                    const stats = { followers: null, following: null, likes: null };
                    // 查找所有包含数字的元素
                    const allText = document.body.innerText;

                    // 匹配 "123 粉丝" 或 "粉丝 123" 格式
                    const patterns = [
                        /([\\d.]+[万kKmM]?)\\s*粉丝/,
                        /粉丝\\s*([\\d.]+[万kKmM]?)/,
                        /([\\d.]+[万kKmM]?)\\s*关注/,
                        /关注\\s*([\\d.]+[万kKmM]?)/,
                        /([\\d.]+[万kKmM]?)\\s*获赞/,
                        /获赞[与和收藏]*\\s*([\\d.]+[万kKmM]?)/
                    ];

                    const followersMatch = allText.match(/([\\d.]+[万kKmM]?)\\s*粉丝/) || allText.match(/粉丝\\s*([\\d.]+[万kKmM]?)/);
                    const followingMatch = allText.match(/([\\d.]+[万kKmM]?)\\s*关注/) || allText.match(/关注\\s*([\\d.]+[万kKmM]?)/);
                    const likesMatch = allText.match(/([\\d.]+[万kKmM]?)\\s*获赞/) || allText.match(/获赞[与和收藏]*\\s*([\\d.]+[万kKmM]?)/);

                    if (followersMatch) stats.followers = followersMatch[1];
                    if (followingMatch) stats.following = followingMatch[1];
                    if (likesMatch) stats.likes = likesMatch[1];

                    return stats;
                };

                const stats = getStats();
                return {
                    nickname: getName(),
                    avatar: getAvatar(),
                    followers: stats.followers,
                    following: stats.following,
                    likes: stats.likes
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
                except:
                    return None

            return UserProfile(
                platform_user_id=platform_user_id,
                nickname=profile_data.get("nickname"),
                avatar_url=profile_data.get("avatar"),
                followers_count=parse_count(profile_data.get("followers")),
                following_count=parse_count(profile_data.get("following")),
                likes_count=parse_count(profile_data.get("likes")),
            )
        except Exception:
            return None
