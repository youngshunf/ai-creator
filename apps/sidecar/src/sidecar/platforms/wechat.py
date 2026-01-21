"""
微信公众号平台适配器
@author Ysf
"""

import json
import logging
import re
import time
from typing import Any, Optional
from urllib.parse import parse_qs, urlparse

from .base import PlatformAdapter, ContentSpec, LoginResult, UserProfile, AdaptedContent, PublishResult


class WechatAdapter(PlatformAdapter):
    """微信公众号平台适配器"""

    platform_name = "wechat"
    platform_display_name = "微信公众号"
    login_url = "https://mp.weixin.qq.com/"

    @property
    def spec(self) -> ContentSpec:
        return ContentSpec(
            title_max_length=64,
            title_min_length=1,
            content_max_length=20000,
            content_min_length=10,
            image_max_count=20,
            image_min_count=0,
            video_max_count=1,
            video_max_duration=1800,
            supported_formats=["text", "image", "video"],
            hashtag_max_count=3,
            mention_supported=False,
            location_supported=False,
        )

    def _get_token(self, url: str) -> Optional[str]:
        """从 URL 提取 token"""
        try:
            parsed = urlparse(url)
            params = parse_qs(parsed.query)
            return params.get("token", [None])[0]
        except:
            return None

    async def check_login_status(
        self, cookies: list[dict], local_storage: dict[str, Any], current_url: str
    ) -> LoginResult:
        """检查微信公众号登录状态"""
        # 微信公众号登录状态强依赖于 URL 中的 token
        token = self._get_token(current_url)
        
        # 检查关键 cookie
        has_uuid = any(c.get("name") == "uuid" for c in cookies)
        has_ticket = any(c.get("name") == "ticket" or c.get("name") == "slave_user" for c in cookies)

        if token and (has_uuid or has_ticket):
            # 尝试从 cookie 获取用户标识
            user_id = "wechat_mp" # 默认ID
            for c in cookies:
                if c.get("name") == "slave_user":
                    user_id = c.get("value")
                    break
            
            return LoginResult(is_logged_in=True, platform_user_id=user_id, extra={"token": token})

        return LoginResult(is_logged_in=False)

    async def get_user_profile(self, page: Any) -> Optional[UserProfile]:
        """获取微信公众号信息"""
        logger = logging.getLogger(__name__)
        try:
            # 确保在首页
            if "mp.weixin.qq.com" not in page.url:
                await page.goto("https://mp.weixin.qq.com/", wait_until="networkidle")
            
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
                        // 粉丝数
                        if (window.wx.cgiData.total_friend_cnt) {
                            stats.followers = window.wx.cgiData.total_friend_cnt;
                        }
                        
                        // 作品数 (从 publish_page.total_count 获取)
                        if (window.wx.cgiData.publish_page && window.wx.cgiData.publish_page.total_count) {
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
                        const match = bodyText.match(/用户总数[:：]?\s*(\d+)/);
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
                # 截图调试
                try:
                    import os
                    os.makedirs("debug_screenshots", exist_ok=True)
                    await page.screenshot(path=f"debug_screenshots/wechat_profile_error_{int(time.time())}.png")
                except:
                    pass
                return None

            def parse_count(val):
                if not val:
                    return None
                val = str(val).replace(',', '')
                try:
                    return int(float(val))
                except:
                    return None

            # 优先使用提取到的 fakeid (最准确的ID)
            user_id = profile_data.get("fakeid")
            
            # 如果没有 fakeid，尝试从 cookie 中获取 slave_user (通常是 gh_id)
            if not user_id:
                cookies = await page.context.cookies()
                for c in cookies:
                    if c.get("name") == "slave_user":
                        user_id = c.get("value")
                        break
            
            # 最后的兜底
            if not user_id:
                user_id = "wechat_mp_unknown"

            return UserProfile(
                platform_user_id=user_id,
                nickname=profile_data.get("nickname"),
                avatar_url=profile_data.get("avatar"),
                followers_count=parse_count(profile_data.get("followers")),
                posts_count=parse_count(profile_data.get("posts")), # 映射作品数
                likes_count=parse_count(profile_data.get("likes")), # 映射点赞数
                extra={"token": token}
            )

        except Exception:
            return None

    async def publish(self, page: Any, content: AdaptedContent) -> PublishResult:
        """微信公众号发布实现 (基础图文)"""
        logger = logging.getLogger(__name__)
        
        try:
            # 1. 获取 Token
            token = self._get_token(page.url)
            if not token:
                logger.warning("[Wechat] 缺少 token，尝试跳转首页获取")
                await page.goto("https://mp.weixin.qq.com/", wait_until="networkidle")
                token = self._get_token(page.url)
                if not token:
                    return PublishResult(success=False, error_message="未登录或无法获取 token")

            # 2. 导航到新建图文页
            # https://mp.weixin.qq.com/cgi-bin/appmsg?t=media/appmsg_edit&action=manage&type=10&lang=zh_CN&token={token}
            # 注意：这是素材管理页，还需要点击新建
            # 直接跳转到新建页面 (URL 可能变动，建议通过 UI 点击)
            
            logger.info("[Wechat] 导航到图文素材页...")
            await page.goto(f"https://mp.weixin.qq.com/cgi-bin/appmsg?t=media/appmsg_edit_v2&action=item&isNew=1&type=10&create_type=10&token={token}&lang=zh_CN", wait_until="networkidle")
            await page.wait_for_timeout(5000)

            # 3. 填写标题
            logger.info(f"[Wechat] 填写标题: {content.title}")
            title_input = await page.wait_for_selector("#title", timeout=10000)
            if title_input:
                await title_input.fill(content.title)
            
            # 4. 填写作者
            author_input = await page.wait_for_selector("#author", timeout=3000)
            if author_input:
                await author_input.fill("AI Creator") # 默认作者，或者从配置读取

            # 5. 填写正文 (UEditor iframe)
            logger.info("[Wechat] 填写正文")
            # 微信编辑器在一个 iframe 里，或者是一个复杂的 div 结构
            # 现在的版本通常是 ueditor_0 iframe
            try:
                # 尝试定位 iframe
                frame_element = await page.wait_for_selector("#ueditor_0", timeout=5000)
                if frame_element:
                    frame = await frame_element.content_frame()
                    if frame:
                        body = await frame.wait_for_selector("body", timeout=5000)
                        if body:
                            # 替换换行符为 <br>
                            html_content = content.content.replace("\n", "<br>")
                            # 插入内容
                            await frame.evaluate(f"document.body.innerHTML = '{html_content}'")
            except Exception as e:
                logger.warning(f"[Wechat] iframe 编辑器填充失败: {e}")
                # 尝试直接在主页面找编辑区域 (有时候没有 iframe)
                editor_div = await page.wait_for_selector(".edui-body-container", timeout=3000)
                if editor_div:
                    await editor_div.click()
                    await page.keyboard.type(content.content)

            # 6. 上传封面 (非常麻烦，需要从素材库选或上传)
            # 简化版：跳过封面，直接尝试保存/发布
            # 微信强制要求封面，如果没有封面，发布会失败。
            # 这里我们尝试返回失败，让 browser-use 接手处理封面选择
            
            # 检查是否有封面错误提示
            # ...

            # 7. 保存/发布
            # 这里我们只做保存草稿，因为群发需要扫码确认，自动化很难完成
            logger.info("[Wechat] 尝试保存草稿")
            save_btn = await page.wait_for_selector("#js_submit", timeout=5000) # 保存按钮 ID
            if not save_btn:
                save_btn = await page.wait_for_selector("button:has-text('保存')", timeout=5000)
            
            if save_btn:
                await save_btn.click()
                # 等待保存成功
                try:
                    await page.wait_for_selector("text=保存成功", timeout=10000)
                    logger.info("[Wechat] 保存草稿成功")
                    return PublishResult(success=True, extra={"status": "draft"})
                except:
                    logger.warning("[Wechat] 未检测到保存成功信号")
            
            # 如果到这里还没成功，或者需要封面，返回失败并提示原因
            return PublishResult(success=False, error_message="微信发布流程复杂，尤其是封面设置，建议使用 browser-use 辅助")

        except Exception as e:
            logger.error(f"[Wechat] 发布出错: {e}")
            return PublishResult(success=False, error_message=str(e))
