"""
设备指纹生成器 - 生成随机浏览器指纹以规避检测

@author Ysf
@date 2025-12-28
"""

import random
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class BrowserFingerprint:
    """浏览器指纹"""
    user_agent: str
    viewport_width: int
    viewport_height: int
    device_scale_factor: float
    locale: str
    timezone_id: str
    webgl_vendor: str
    webgl_renderer: str


class FingerprintGenerator:
    """
    设备指纹生成器

    生成随机但合理的浏览器指纹，用于规避平台检测。
    """

    # 常见 User-Agent 列表 (Chrome on macOS/Windows)
    USER_AGENTS = [
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    ]

    # 常见分辨率
    VIEWPORTS = [
        (1920, 1080),
        (1440, 900),
        (1536, 864),
        (1366, 768),
        (2560, 1440),
    ]

    # WebGL 渲染器
    WEBGL_RENDERERS = [
        ("Google Inc. (Apple)", "ANGLE (Apple, Apple M1 Pro, OpenGL 4.1)"),
        ("Google Inc. (NVIDIA)", "ANGLE (NVIDIA, NVIDIA GeForce RTX 3060, OpenGL 4.5)"),
        ("Google Inc. (Intel)", "ANGLE (Intel, Intel(R) UHD Graphics 630, OpenGL 4.1)"),
        ("Google Inc. (AMD)", "ANGLE (AMD, AMD Radeon Pro 5500M, OpenGL 4.1)"),
    ]

    # 时区
    TIMEZONES = [
        "Asia/Shanghai",
        "Asia/Hong_Kong",
        "Asia/Taipei",
    ]

    def generate(self, seed: Optional[int] = None) -> BrowserFingerprint:
        """
        生成随机浏览器指纹

        Args:
            seed: 随机种子 (可选，用于生成可复现的指纹)

        Returns:
            BrowserFingerprint: 生成的指纹
        """
        if seed is not None:
            random.seed(seed)

        viewport = random.choice(self.VIEWPORTS)
        webgl = random.choice(self.WEBGL_RENDERERS)

        return BrowserFingerprint(
            user_agent=random.choice(self.USER_AGENTS),
            viewport_width=viewport[0],
            viewport_height=viewport[1],
            device_scale_factor=random.choice([1.0, 1.25, 1.5, 2.0]),
            locale="zh-CN",
            timezone_id=random.choice(self.TIMEZONES),
            webgl_vendor=webgl[0],
            webgl_renderer=webgl[1],
        )

    def generate_for_account(self, account_id: str) -> BrowserFingerprint:
        """
        为特定账号生成固定指纹

        使用账号ID作为种子，确保同一账号始终使用相同指纹。

        Args:
            account_id: 账号ID

        Returns:
            BrowserFingerprint: 生成的指纹
        """
        seed = hash(account_id) & 0xFFFFFFFF
        return self.generate(seed=seed)
