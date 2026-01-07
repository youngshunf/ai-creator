"""
抖音平台适配器
@author Ysf
"""

import json
import re
from typing import Any, Optional

from .base import PlatformAdapter, ContentSpec, LoginResult, UserProfile


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
        has_passport = any(c.get("name") == "passport_csrf_token" for c in cookies)

        if has_session and has_passport:
            # 从 cookie 提取 user_id
            user_id = None
            for c in cookies:
                if c.get("name") == "LOGIN_STATUS":
                    user_id = c.get("value")
                    break
            return LoginResult(is_logged_in=True, platform_user_id=user_id)

        return LoginResult(is_logged_in=False)

    async def get_user_profile(self, page: Any) -> Optional[UserProfile]:
        """获取抖音用户资料 - 导航到创作者中心获取信息"""
        try:
            # 导航到创作者中心首页
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
                return None

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
