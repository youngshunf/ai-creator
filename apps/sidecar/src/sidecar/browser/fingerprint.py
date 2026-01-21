"""
设备指纹生成器 - 生成随机浏览器指纹以规避检测

@author Ysf
@date 2025-12-28
"""

import json
import random
from dataclasses import dataclass, asdict, field
from typing import List, Optional, Dict, Any
from pathlib import Path


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
    # 扩展字段 - 从真实浏览器采集
    platform: str = "MacIntel"
    vendor: str = "Google Inc."
    hardware_concurrency: int = 8
    device_memory: int = 8
    languages: List[str] = field(default_factory=lambda: ["zh-CN", "zh", "en-US", "en"])
    screen_width: int = 1920
    screen_height: int = 1080
    color_depth: int = 24
    pixel_ratio: float = 2.0
    canvas_fingerprint: str = ""
    audio_fingerprint: str = ""
    webgl_fingerprint: str = ""


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

    @staticmethod
    async def extract_from_page(page) -> BrowserFingerprint:
        """
        从真实浏览器页面提取完整指纹
        
        在用户登录时调用，保存真实浏览器信息。
        
        Args:
            page: Playwright Page 对象
            
        Returns:
            BrowserFingerprint: 提取的真实指纹
        """
        fingerprint_data = await page.evaluate("""
            () => {
                // 基本信息
                const fp = {
                    user_agent: navigator.userAgent,
                    platform: navigator.platform,
                    vendor: navigator.vendor,
                    languages: navigator.languages ? [...navigator.languages] : ['zh-CN'],
                    hardware_concurrency: navigator.hardwareConcurrency || 8,
                    device_memory: navigator.deviceMemory || 8,
                    screen_width: window.screen.width,
                    screen_height: window.screen.height,
                    viewport_width: window.innerWidth,
                    viewport_height: window.innerHeight,
                    device_scale_factor: window.devicePixelRatio || 1,
                    color_depth: window.screen.colorDepth,
                    pixel_ratio: window.devicePixelRatio || 1,
                    timezone_id: Intl.DateTimeFormat().resolvedOptions().timeZone,
                    locale: navigator.language || 'zh-CN',
                };
                
                // WebGL 信息
                try {
                    const canvas = document.createElement('canvas');
                    const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
                    if (gl) {
                        const debugInfo = gl.getExtension('WEBGL_debug_renderer_info');
                        if (debugInfo) {
                            fp.webgl_vendor = gl.getParameter(debugInfo.UNMASKED_VENDOR_WEBGL);
                            fp.webgl_renderer = gl.getParameter(debugInfo.UNMASKED_RENDERER_WEBGL);
                        }
                        // WebGL 指纹
                        fp.webgl_fingerprint = gl.getParameter(gl.VERSION) + '|' + gl.getParameter(gl.SHADING_LANGUAGE_VERSION);
                    }
                } catch (e) {
                    fp.webgl_vendor = 'Google Inc. (Apple)';
                    fp.webgl_renderer = 'ANGLE (Apple, Apple M1 Pro, OpenGL 4.1)';
                }
                
                // Canvas 指纹
                try {
                    const canvas = document.createElement('canvas');
                    canvas.width = 200;
                    canvas.height = 50;
                    const ctx = canvas.getContext('2d');
                    ctx.textBaseline = 'top';
                    ctx.font = '14px Arial';
                    ctx.fillStyle = '#f60';
                    ctx.fillRect(125, 1, 62, 20);
                    ctx.fillStyle = '#069';
                    ctx.fillText('Browser Fingerprint', 2, 15);
                    ctx.fillStyle = 'rgba(102, 204, 0, 0.7)';
                    ctx.fillText('Canvas Test', 4, 30);
                    fp.canvas_fingerprint = canvas.toDataURL().slice(0, 100);
                } catch (e) {}
                
                // Audio 指纹
                try {
                    const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
                    fp.audio_fingerprint = audioCtx.sampleRate.toString();
                    audioCtx.close();
                } catch (e) {}
                
                return fp;
            }
        """)
        
        return BrowserFingerprint(
            user_agent=fingerprint_data.get('user_agent', ''),
            viewport_width=fingerprint_data.get('viewport_width', 1920),
            viewport_height=fingerprint_data.get('viewport_height', 1080),
            device_scale_factor=fingerprint_data.get('device_scale_factor', 1.0),
            locale=fingerprint_data.get('locale', 'zh-CN'),
            timezone_id=fingerprint_data.get('timezone_id', 'Asia/Shanghai'),
            webgl_vendor=fingerprint_data.get('webgl_vendor', 'Google Inc. (Apple)'),
            webgl_renderer=fingerprint_data.get('webgl_renderer', 'ANGLE (Apple, Apple M1 Pro, OpenGL 4.1)'),
            platform=fingerprint_data.get('platform', 'MacIntel'),
            vendor=fingerprint_data.get('vendor', 'Google Inc.'),
            hardware_concurrency=fingerprint_data.get('hardware_concurrency', 8),
            device_memory=fingerprint_data.get('device_memory', 8),
            languages=fingerprint_data.get('languages', ['zh-CN', 'zh', 'en-US', 'en']),
            screen_width=fingerprint_data.get('screen_width', 1920),
            screen_height=fingerprint_data.get('screen_height', 1080),
            color_depth=fingerprint_data.get('color_depth', 24),
            pixel_ratio=fingerprint_data.get('pixel_ratio', 2.0),
            canvas_fingerprint=fingerprint_data.get('canvas_fingerprint', ''),
            audio_fingerprint=fingerprint_data.get('audio_fingerprint', ''),
            webgl_fingerprint=fingerprint_data.get('webgl_fingerprint', ''),
        )
    
    @staticmethod
    def to_dict(fp: BrowserFingerprint) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(fp)
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> BrowserFingerprint:
        """从字典创建"""
        return BrowserFingerprint(
            user_agent=data.get('user_agent', ''),
            viewport_width=data.get('viewport_width', 1920),
            viewport_height=data.get('viewport_height', 1080),
            device_scale_factor=data.get('device_scale_factor', 1.0),
            locale=data.get('locale', 'zh-CN'),
            timezone_id=data.get('timezone_id', 'Asia/Shanghai'),
            webgl_vendor=data.get('webgl_vendor', ''),
            webgl_renderer=data.get('webgl_renderer', ''),
            platform=data.get('platform', 'MacIntel'),
            vendor=data.get('vendor', 'Google Inc.'),
            hardware_concurrency=data.get('hardware_concurrency', 8),
            device_memory=data.get('device_memory', 8),
            languages=data.get('languages', ['zh-CN', 'zh', 'en-US', 'en']),
            screen_width=data.get('screen_width', 1920),
            screen_height=data.get('screen_height', 1080),
            color_depth=data.get('color_depth', 24),
            pixel_ratio=data.get('pixel_ratio', 2.0),
            canvas_fingerprint=data.get('canvas_fingerprint', ''),
            audio_fingerprint=data.get('audio_fingerprint', ''),
            webgl_fingerprint=data.get('webgl_fingerprint', ''),
        )
