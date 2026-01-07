"""
LLM 配置管理器

桌面端用户登录后自动获取 API Token，无需手动配置。

@author Ysf
@date 2025-12-28
"""

import os
import json
from pathlib import Path
from typing import Optional

from .interface import LLMConfig


class LLMConfigManager:
    """
    LLM 配置管理器

    - 桌面端: 用户登录后自动获取并保存 API Token
    - 无需手动配置，Token 由服务端分发
    - 支持开发/生产环境切换 (仅开发者使用)
    """

    # 默认配置路径
    DEFAULT_CONFIG_PATH = "~/.ai-creator/llm-config.json"

    # 默认网关地址 (固定，用户无需配置)
    DEFAULT_URLS = {
        "development": "http://localhost:8010",
        "production": "https://api.ai-creator.com",
    }

    def __init__(self, config_path: Optional[str] = None):
        """
        初始化配置管理器

        Args:
            config_path: 配置文件路径 (可选)
        """
        self.config_path = Path(
            config_path or os.path.expanduser(self.DEFAULT_CONFIG_PATH)
        )
        self._config: Optional[LLMConfig] = None

    def load(self, environment: str = "production") -> LLMConfig:
        """
        加载配置

        Args:
            environment: 环境名称 (development | production)

        Returns:
            LLMConfig: LLM 配置
        """
        # 从配置文件读取 (自动保存的 Token)
        if self.config_path.exists():
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)

                env_config = data.get(environment, {})
                return LLMConfig(
                    base_url=self.DEFAULT_URLS.get(environment, self.DEFAULT_URLS["production"]),
                    api_token=env_config.get("api_token", ""),
                    access_token=env_config.get("access_token", ""),
                    access_token_expire_time=env_config.get("access_token_expire_time", ""),
                    refresh_token=env_config.get("refresh_token", ""),
                    refresh_token_expire_time=env_config.get("refresh_token_expire_time", ""),
                    environment=environment,
                    default_model=env_config.get("default_model", "claude-sonnet-4-5-20250929"),
                    timeout_seconds=env_config.get("timeout_seconds", 120),
                )
            except (json.JSONDecodeError, IOError):
                pass

        # 返回默认配置 (无 Token，需要登录)
        return LLMConfig(
            base_url=self.DEFAULT_URLS.get(environment, self.DEFAULT_URLS["production"]),
            api_token="",
            access_token="",
            environment=environment,
        )

    def save_token(
        self,
        api_token: str,
        environment: str = "production",
        access_token: str = "",
        access_token_expire_time: str = "",
        refresh_token: str = "",
        refresh_token_expire_time: str = "",
    ):
        """
        保存 Token (用户登录后自动调用)

        Args:
            api_token: LLM API Key (sk-cf-xxx)
            environment: 环境名称
            access_token: JWT Token (用于用户认证)
            access_token_expire_time: JWT 过期时间 (ISO 格式)
            refresh_token: 刷新令牌
            refresh_token_expire_time: 刷新令牌过期时间 (ISO 格式)
        """
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

        # 读取现有配置
        data = {}
        if self.config_path.exists():
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except (json.JSONDecodeError, IOError):
                pass

        # 更新 Token
        if environment not in data:
            data[environment] = {}
        data[environment]["api_token"] = api_token
        if access_token:
            data[environment]["access_token"] = access_token
        if access_token_expire_time:
            data[environment]["access_token_expire_time"] = access_token_expire_time
        if refresh_token:
            data[environment]["refresh_token"] = refresh_token
        if refresh_token_expire_time:
            data[environment]["refresh_token_expire_time"] = refresh_token_expire_time

        # 写入配置
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        # 设置文件权限 (仅所有者可读写)
        try:
            self.config_path.chmod(0o600)
        except OSError:
            pass  # Windows 可能不支持

    def clear_token(self, environment: str = "production"):
        """
        清除 Token (用户登出时调用)

        Args:
            environment: 环境名称
        """
        if not self.config_path.exists():
            return

        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            if environment in data:
                data[environment]["api_token"] = ""
                data[environment]["access_token"] = ""
                data[environment]["access_token_expire_time"] = ""
                data[environment]["refresh_token"] = ""
                data[environment]["refresh_token_expire_time"] = ""

            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except (json.JSONDecodeError, IOError):
            pass

    def is_logged_in(self, environment: str = "production") -> bool:
        """
        检查用户是否已登录 (是否有 Token)

        Args:
            environment: 环境名称

        Returns:
            bool: True 表示已登录
        """
        config = self.load(environment)
        return bool(config.api_token)

    def get_current_environment(self) -> str:
        """
        获取当前环境

        Returns:
            str: 环境名称
        """
        return os.environ.get("AI_CREATOR_ENV", "production")

    def update_default_model(self, model: str, environment: str = "production"):
        """
        更新默认模型

        Args:
            model: 模型名称
            environment: 环境名称
        """
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

        data = {}
        if self.config_path.exists():
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except (json.JSONDecodeError, IOError):
                pass

        if environment not in data:
            data[environment] = {}
        data[environment]["default_model"] = model

        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
