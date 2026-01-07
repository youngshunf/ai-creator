"""
微信公众号平台适配器
@author Ysf
"""

from .base import PlatformAdapter, ContentSpec


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
            content_min_length=100,
            image_max_count=20,
            image_min_count=0,
            video_max_count=1,
            video_max_duration=1800,
            supported_formats=["text", "image", "video"],
            hashtag_max_count=3,
            mention_supported=False,
            location_supported=False,
        )
