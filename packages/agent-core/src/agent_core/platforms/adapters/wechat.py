"""
微信公众号平台适配器

从 sidecar 迁移，使用统一基类和 YAML 配置。

@author Ysf
@date 2026-01-22
"""

import logging
import time
from typing import Any, Optional, List, Dict
from urllib.parse import parse_qs, urlparse

from ..adapter import PlatformAdapter
from ..models import AdaptedContent, LoginResult, UserProfile, PublishResult

logger = logging.getLogger(__name__)


class WechatAdapter(PlatformAdapter):
    """微信公众号平台适配器"""

    # 平台标识（必须）
    platform_name = "wechat"
    
    # 以下属性由基类从 YAML 配置自动加载：
    # - platform_display_name
    # - login_url
    # - spec

    def _get_token(self, url: str) -> Optional[str]:
        """从 URL 提取 token"""
        try:
            parsed = urlparse(url)
            params = parse_qs(parsed.query)
            return params.get("token", [None])[0]
        except Exception:
            return None

    async def check_login_status(
        self,
        cookies: List[Dict],
        local_storage: Dict[str, Any],
        current_url: str,
    ) -> LoginResult:
        """检查微信公众号登录状态"""
        # 微信公众号登录状态强依赖于 URL 中的 token
        token = self._get_token(current_url)
        
        # 检查关键 cookie
        has_uuid = any(c.get("name") == "uuid" for c in cookies)
        has_ticket = any(
            c.get("name") == "ticket" or c.get("name") == "slave_user"
            for c in cookies
        )

        if token and (has_uuid or has_ticket):
            # 尝试从 cookie 获取用户标识
            user_id = "wechat_mp"  # 默认ID
            for c in cookies:
                if c.get("name") == "slave_user":
                    user_id = c.get("value")
                    break
            
            return LoginResult(
                is_logged_in=True,
                platform_user_id=user_id,
                extra={"token": token}
            )

        return LoginResult(is_logged_in=False)

    async def get_user_profile(self, page: Any) -> Optional[UserProfile]:
        """获取微信公众号信息"""
        try:
            # 确保在首页
            if "mp.weixin.qq.com" not in page.url:
                home_url = self.get_url("home")
                if not home_url:
                    home_url = "https://mp.weixin.qq.com/"
                await page.goto(home_url, wait_until="networkidle")
            
            token = self._get_token(page.url)
            if not token:
                logger.warning("[Wechat] 未找到 token，可能未登录")
                return None

            # 提取信息
            profile_data = await page.evaluate("""() => {
                let nickname = null;
                let avatar = null;
                let fakeid = null;

                // 1. 尝试从全局变量 wx.cgiData 获取 (最可靠)
                if (window.wx && window.wx.cgiData) {
                    nickname = window.wx.cgiData.nickname || window.wx.cgiData.nick_name;
                    avatar = window.wx.cgiData.headimg || window.wx.cgiData.head_img;
                    fakeid = window.wx.cgiData.fakeid;
                }

                // 2. DOM 提取作为补充/后备
                if (!nickname) {
                    const selectors = [
                        '.weui-desktop-account__nickname',
                        '.mp-head-nickname',
                        '.user_name',
                        '.account_name',
                        '#account_name',
                        '[class*="nickname"]'
                    ];
                    for (const sel of selectors) {
                        const el = document.querySelector(sel);
                        if (el && el.textContent.trim()) {
                            nickname = el.textContent.trim();
                            break;
                        }
                    }
                }
                
                if (!avatar) {
                    const selectors = [
                        '.weui-desktop-account__img',
                        '.mp-head-logo img',
                        '.avatar',
                        '.account_avatar img',
                        'img[class*="avatar"]'
                    ];
                    for (const sel of selectors) {
                        const el = document.querySelector(sel);
                        if (el && el.src) {
                            avatar = el.src;
                            break;
                        }
                    }
                }

                const getStats = () => {
                    const stats = {
                        followers: null,
                        posts: null,
                        likes: null
                    };
                    
                    // 1. 优先从全局变量获取
                    if (window.wx && window.wx.cgiData) {
                        if (window.wx.cgiData.total_friend_cnt) {
                            stats.followers = window.wx.cgiData.total_friend_cnt;
                        }
                        if (window.wx.cgiData.publish_page && 
                            window.wx.cgiData.publish_page.total_count) {
                            stats.posts = window.wx.cgiData.publish_page.total_count;
                        } else if (window.wx.cgiData.total_count) {
                            stats.posts = window.wx.cgiData.total_count;
                        }
                    }

                    // 2. DOM 提取作为补充
                    if (!stats.followers) {
                        const userCountSelectors = [
                            '.weui-desktop-mass__stat__item__value',
                            '.user_count',
                            '.fans_count',
                            '[class*="fans"] [class*="num"]'
                        ];
                        
                        for (const sel of userCountSelectors) {
                            const el = document.querySelector(sel);
                            if (el && el.textContent.trim()) {
                                stats.followers = el.textContent.trim();
                                break;
                            }
                        }
                    }
                    
                    // 3. 正则匹配兜底
                    if (!stats.followers) {
                        const bodyText = document.body.innerText;
                        const match = bodyText.match(/用户总数[:：]?\\s*(\\d+)/);
                        if (match) stats.followers = match[1];
                    }
                    
                    return stats;
                };
                
                const stats = getStats();
                return { nickname, avatar, fakeid, ...stats };
            }""")
            
            logger.info(f"[Wechat] 页面提取数据: {profile_data}")

            if not profile_data.get("nickname"):
                logger.warning("[Wechat] 无法提取昵称")
                return None

            def parse_count(val):
                if not val:
                    return None
                val = str(val).replace(',', '')
                try:
                    return int(float(val))
                except Exception:
                    return None

            # 优先使用提取到的 fakeid (最准确的ID)
            user_id = profile_data.get("fakeid")
            
            # 如果没有 fakeid，尝试从 cookie 中获取 slave_user
            if not user_id:
                cookies = await page.context.cookies()
                for c in cookies:
                    if c.get("name") == "slave_user":
                        user_id = c.get("value")
                        break
            
            if not user_id:
                user_id = "wechat_mp_unknown"

            return UserProfile(
                platform_user_id=user_id,
                nickname=profile_data.get("nickname"),
                avatar_url=profile_data.get("avatar"),
                followers_count=parse_count(profile_data.get("followers")),
                posts_count=parse_count(profile_data.get("posts")),
                likes_count=parse_count(profile_data.get("likes")),
                extra={"token": token}
            )

        except Exception as e:
            logger.error(f"[Wechat] 获取用户资料失败: {e}")
            return None

    async def publish(self, page: Any, content: AdaptedContent) -> PublishResult:
        """微信公众号发布实现 (基础图文)"""
        try:
            # 1. 获取 Token
            token = self._get_token(page.url)
            if not token:
                logger.warning("[Wechat] 缺少 token，尝试跳转首页获取")
                home_url = self.get_url("home")
                if not home_url:
                    home_url = "https://mp.weixin.qq.com/"
                await page.goto(home_url, wait_until="networkidle")
                token = self._get_token(page.url)
                if not token:
                    return PublishResult(
                        success=False,
                        error_message="未登录或无法获取 token"
                    )

            # 2. 导航到新建图文页 - 使用配置中的 URL
            publish_url = self.get_url("publish")
            if publish_url:
                # 替换 token 占位符
                publish_url = publish_url.replace("{token}", token)
            else:
                publish_url = (
                    f"https://mp.weixin.qq.com/cgi-bin/appmsg?"
                    f"t=media/appmsg_edit_v2&action=item&isNew=1&type=10"
                    f"&create_type=10&token={token}&lang=zh_CN"
                )
            
            logger.info(f"[Wechat] 导航到图文素材页: {publish_url}")
            await page.goto(publish_url, wait_until="networkidle")
            await page.wait_for_timeout(5000)

            # 3. 填写标题 - 使用配置中的选择器
            logger.info(f"[Wechat] 填写标题: {content.title}")
            title_selector = self.get_selector("title_input", "#title")
            title_input = await page.wait_for_selector(title_selector, timeout=10000)
            if title_input:
                await title_input.fill(content.title)
            
            # 4. 填写作者
            author_selector = self.get_selector("author_input", "#author")
            author_input = await page.wait_for_selector(author_selector, timeout=3000)
            if author_input:
                await author_input.fill("AI Creator")

            # 5. 填写正文 (UEditor iframe)
            logger.info("[Wechat] 填写正文")
            content_selector = self.get_selector("content_input", "#ueditor_0")
            try:
                frame_element = await page.wait_for_selector(content_selector, timeout=5000)
                if frame_element:
                    frame = await frame_element.content_frame()
                    if frame:
                        body = await frame.wait_for_selector("body", timeout=5000)
                        if body:
                            html_content = content.content.replace("\n", "<br>")
                            await frame.evaluate(f"document.body.innerHTML = '{html_content}'")
            except Exception as e:
                logger.warning(f"[Wechat] iframe 编辑器填充失败: {e}")
                editor_div = await page.wait_for_selector(
                    ".edui-body-container",
                    timeout=3000
                )
                if editor_div:
                    await editor_div.click()
                    await page.keyboard.type(content.content)

            # 6. 保存草稿
            logger.info("[Wechat] 尝试保存草稿")
            submit_selector = self.get_selector("submit_btn", "#js_submit")
            save_btn = await page.wait_for_selector(submit_selector, timeout=5000)
            if not save_btn:
                save_btn = await page.wait_for_selector(
                    "button:has-text('保存')",
                    timeout=5000
                )
            
            if save_btn:
                await save_btn.click()
                success_selector = self.get_selector(
                    "success_indicator",
                    "text=保存成功"
                )
                try:
                    await page.wait_for_selector(success_selector, timeout=10000)
                    logger.info("[Wechat] 保存草稿成功")
                    return PublishResult(success=True, extra={"status": "draft"})
                except Exception:
                    logger.warning("[Wechat] 未检测到保存成功信号")
            
            return PublishResult(
                success=False,
                error_message="微信发布流程复杂，尤其是封面设置，建议使用 browser-use 辅助"
            )

        except Exception as e:
            logger.error(f"[Wechat] 发布出错: {e}")
            try:
                import os
                os.makedirs("debug_screenshots", exist_ok=True)
                await page.screenshot(
                    path=f"debug_screenshots/wechat_publish_error_{int(time.time())}.png"
                )
            except Exception:
                pass
            return PublishResult(success=False, error_message=str(e))
