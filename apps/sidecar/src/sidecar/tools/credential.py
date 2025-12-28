"""
本地凭证管理工具 - 安全存储和管理平台凭证

@author Ysf
@date 2025-12-28
"""

import os
import json
import base64
from pathlib import Path
from typing import Any, Dict, Optional, List
from dataclasses import dataclass, asdict

from agent_core.tools.base import (
    ToolInterface,
    ToolMetadata,
    ToolCapability,
    ToolResult,
)
from agent_core.runtime.interfaces import RuntimeType
from agent_core.runtime.context import RuntimeContext
from agent_core.crypto.credential_crypto import CredentialCrypto


@dataclass
class PlatformCredential:
    """平台凭证"""
    platform: str
    account_id: str
    account_name: str
    cookies: List[Dict[str, Any]]
    storage_state: Optional[Dict[str, Any]] = None
    extra: Optional[Dict[str, Any]] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class LocalCredentialTool(ToolInterface):
    """
    本地凭证管理工具

    安全存储和管理社交平台的登录凭证。
    使用 AES-256-GCM 加密存储。
    """

    metadata = ToolMetadata(
        name="credential_manager",
        description="本地安全存储和管理平台登录凭证",
        capabilities=[ToolCapability.CREDENTIAL_STORE],
        supported_runtimes=[RuntimeType.LOCAL],
    )

    def __init__(self, master_key: Optional[str] = None):
        """
        初始化凭证管理工具

        Args:
            master_key: 主密钥 (可选，默认从环境变量获取)
        """
        self._master_key = master_key or os.environ.get("AI_CREATOR_MASTER_KEY")
        self._crypto: Optional[CredentialCrypto] = None
        self._credentials_dir = Path(os.path.expanduser("~/.ai-creator/credentials"))

    def _get_crypto(self) -> CredentialCrypto:
        """获取加密器实例"""
        if self._crypto is None:
            if not self._master_key:
                raise ValueError("主密钥未设置，请设置 AI_CREATOR_MASTER_KEY 环境变量")
            self._crypto = CredentialCrypto(self._master_key)
        return self._crypto

    async def execute(
        self,
        ctx: RuntimeContext,
        *,
        action: str,
        platform: Optional[str] = None,
        account_id: Optional[str] = None,
        credential: Optional[Dict[str, Any]] = None,
    ) -> ToolResult:
        """
        执行凭证操作

        Args:
            ctx: 运行时上下文
            action: 操作类型 (save, load, delete, list)
            platform: 平台名称
            account_id: 账号ID
            credential: 凭证数据 (save 操作时需要)

        Returns:
            ToolResult: 执行结果
        """
        try:
            if action == "save":
                return await self._save_credential(platform, account_id, credential)
            elif action == "load":
                return await self._load_credential(platform, account_id)
            elif action == "delete":
                return await self._delete_credential(platform, account_id)
            elif action == "list":
                return await self._list_credentials(platform)
            else:
                return ToolResult(
                    success=False,
                    data=None,
                    error=f"不支持的操作: {action}",
                )
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=str(e),
            )

    async def _save_credential(
        self,
        platform: str,
        account_id: str,
        credential: Dict[str, Any],
    ) -> ToolResult:
        """
        保存凭证

        Args:
            platform: 平台名称
            account_id: 账号ID
            credential: 凭证数据

        Returns:
            ToolResult: 执行结果
        """
        if not platform or not account_id or not credential:
            return ToolResult(
                success=False,
                data=None,
                error="platform, account_id 和 credential 都是必需的",
            )

        from datetime import datetime

        # 创建凭证对象
        cred = PlatformCredential(
            platform=platform,
            account_id=account_id,
            account_name=credential.get("account_name", account_id),
            cookies=credential.get("cookies", []),
            storage_state=credential.get("storage_state"),
            extra=credential.get("extra"),
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
        )

        # 加密并保存
        cred_dir = self._credentials_dir / platform
        cred_dir.mkdir(parents=True, exist_ok=True)

        cred_path = cred_dir / f"{account_id}.enc"

        try:
            crypto = self._get_crypto()
            encrypted_data = crypto.encrypt(json.dumps(asdict(cred)))

            with open(cred_path, "wb") as f:
                f.write(encrypted_data)

            # 设置文件权限
            try:
                cred_path.chmod(0o600)
            except OSError:
                pass

            return ToolResult(
                success=True,
                data={
                    "platform": platform,
                    "account_id": account_id,
                    "message": "凭证保存成功",
                },
            )

        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"保存凭证失败: {str(e)}",
            )

    async def _load_credential(
        self,
        platform: str,
        account_id: str,
    ) -> ToolResult:
        """
        加载凭证

        Args:
            platform: 平台名称
            account_id: 账号ID

        Returns:
            ToolResult: 执行结果
        """
        if not platform or not account_id:
            return ToolResult(
                success=False,
                data=None,
                error="platform 和 account_id 都是必需的",
            )

        cred_path = self._credentials_dir / platform / f"{account_id}.enc"

        if not cred_path.exists():
            return ToolResult(
                success=False,
                data=None,
                error=f"凭证不存在: {platform}/{account_id}",
            )

        try:
            crypto = self._get_crypto()

            with open(cred_path, "rb") as f:
                encrypted_data = f.read()

            decrypted_data = crypto.decrypt(encrypted_data)
            cred_dict = json.loads(decrypted_data)

            return ToolResult(
                success=True,
                data=cred_dict,
            )

        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"加载凭证失败: {str(e)}",
            )

    async def _delete_credential(
        self,
        platform: str,
        account_id: str,
    ) -> ToolResult:
        """
        删除凭证

        Args:
            platform: 平台名称
            account_id: 账号ID

        Returns:
            ToolResult: 执行结果
        """
        if not platform or not account_id:
            return ToolResult(
                success=False,
                data=None,
                error="platform 和 account_id 都是必需的",
            )

        cred_path = self._credentials_dir / platform / f"{account_id}.enc"

        if not cred_path.exists():
            return ToolResult(
                success=False,
                data=None,
                error=f"凭证不存在: {platform}/{account_id}",
            )

        try:
            cred_path.unlink()

            return ToolResult(
                success=True,
                data={
                    "platform": platform,
                    "account_id": account_id,
                    "message": "凭证删除成功",
                },
            )

        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"删除凭证失败: {str(e)}",
            )

    async def _list_credentials(
        self,
        platform: Optional[str] = None,
    ) -> ToolResult:
        """
        列出凭证

        Args:
            platform: 平台名称 (可选，不指定则列出所有)

        Returns:
            ToolResult: 执行结果
        """
        credentials = []

        try:
            if platform:
                # 列出指定平台的凭证
                platform_dir = self._credentials_dir / platform
                if platform_dir.exists():
                    for cred_file in platform_dir.glob("*.enc"):
                        credentials.append({
                            "platform": platform,
                            "account_id": cred_file.stem,
                        })
            else:
                # 列出所有平台的凭证
                if self._credentials_dir.exists():
                    for platform_dir in self._credentials_dir.iterdir():
                        if platform_dir.is_dir():
                            for cred_file in platform_dir.glob("*.enc"):
                                credentials.append({
                                    "platform": platform_dir.name,
                                    "account_id": cred_file.stem,
                                })

            return ToolResult(
                success=True,
                data={"credentials": credentials},
            )

        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"列出凭证失败: {str(e)}",
            )

    def get_schema(self) -> Dict[str, Any]:
        """获取工具参数 Schema"""
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "description": "操作类型",
                    "enum": ["save", "load", "delete", "list"],
                },
                "platform": {
                    "type": "string",
                    "description": "平台名称",
                },
                "account_id": {
                    "type": "string",
                    "description": "账号ID",
                },
                "credential": {
                    "type": "object",
                    "description": "凭证数据 (save 操作时需要)",
                    "properties": {
                        "account_name": {"type": "string"},
                        "cookies": {"type": "array"},
                        "storage_state": {"type": "object"},
                        "extra": {"type": "object"},
                    },
                },
            },
            "required": ["action"],
        }
