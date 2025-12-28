"""
凭证同步客户端 - 将本地凭证同步到云端

@author Ysf
@date 2025-12-28
"""

import os
import json
import base64
import hashlib
import asyncio
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from datetime import datetime

import httpx

from agent_core.crypto.credential_crypto import CredentialCrypto


@dataclass
class SyncResult:
    """同步结果"""
    success: bool
    platform: str
    account_id: str
    version: int = 0
    message: str = ""


class CredentialSyncClient:
    """
    凭证同步客户端

    将本地加密凭证同步到云端，支持：
    - 端到端加密（云端无法解密）
    - 增量同步
    - 冲突检测
    """

    def __init__(
        self,
        api_base_url: str,
        auth_token: str,
        master_key: str,
    ):
        """
        初始化同步客户端

        Args:
            api_base_url: 云端 API 地址
            auth_token: 用户认证 Token
            master_key: 用户主密钥
        """
        self._api_base_url = api_base_url.rstrip("/")
        self._auth_token = auth_token
        self._master_key = master_key
        self._sync_key = self._derive_sync_key(master_key)
        self._sync_key_hash = hashlib.sha256(self._sync_key.encode()).hexdigest()
        self._credentials_dir = Path(os.path.expanduser("~/.ai-creator/credentials"))
        self._sync_state_file = self._credentials_dir / ".sync_state.json"

    def _derive_sync_key(self, master_key: str) -> str:
        """从主密钥派生同步密钥"""
        return hashlib.pbkdf2_hmac(
            "sha256",
            master_key.encode(),
            b"credential_sync_salt",
            100000,
        ).hex()

    def _get_headers(self) -> Dict[str, str]:
        """获取请求头"""
        return {
            "Authorization": f"Bearer {self._auth_token}",
            "Content-Type": "application/json",
            "X-Sync-Key-Hash": self._sync_key_hash,
        }

    def _load_sync_state(self) -> Dict[str, Any]:
        """加载同步状态"""
        if self._sync_state_file.exists():
            with open(self._sync_state_file, "r") as f:
                return json.load(f)
        return {"synced": {}, "last_sync": None}

    def _save_sync_state(self, state: Dict[str, Any]):
        """保存同步状态"""
        self._sync_state_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self._sync_state_file, "w") as f:
            json.dump(state, f, indent=2)

    async def sync_credential(
        self,
        platform: str,
        account_id: str,
    ) -> SyncResult:
        """
        同步单个凭证到云端

        Args:
            platform: 平台名称
            account_id: 账号ID

        Returns:
            同步结果
        """
        cred_path = self._credentials_dir / platform / f"{account_id}.enc"

        if not cred_path.exists():
            return SyncResult(
                success=False,
                platform=platform,
                account_id=account_id,
                message="本地凭证不存在",
            )

        # 读取加密凭证
        with open(cred_path, "rb") as f:
            encrypted_data = f.read()

        # 获取同步状态
        state = self._load_sync_state()
        key = f"{platform}/{account_id}"
        current_version = state["synced"].get(key, {}).get("version", 0) + 1

        # 解密获取账号名称
        try:
            crypto = CredentialCrypto(self._master_key)
            decrypted = crypto.decrypt(encrypted_data)
            cred_data = json.loads(decrypted)
            account_name = cred_data.get("account_name", account_id)
        except Exception:
            account_name = account_id

        # 发送同步请求
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self._api_base_url}/api/v1/credentials/sync",
                    headers=self._get_headers(),
                    json={
                        "platform": platform,
                        "account_id": account_id,
                        "account_name": account_name,
                        "encrypted_data": base64.b64encode(encrypted_data).decode(),
                        "sync_key_hash": self._sync_key_hash,
                        "version": current_version,
                    },
                    timeout=30.0,
                )

                if response.status_code == 200:
                    result = response.json()
                    if result.get("data", {}).get("success"):
                        # 更新同步状态
                        state["synced"][key] = {
                            "version": current_version,
                            "synced_at": datetime.now().isoformat(),
                        }
                        state["last_sync"] = datetime.now().isoformat()
                        self._save_sync_state(state)

                        return SyncResult(
                            success=True,
                            platform=platform,
                            account_id=account_id,
                            version=current_version,
                            message="同步成功",
                        )
                    else:
                        return SyncResult(
                            success=False,
                            platform=platform,
                            account_id=account_id,
                            version=result.get("data", {}).get("version", 0),
                            message=result.get("data", {}).get("message", "同步失败"),
                        )
                else:
                    return SyncResult(
                        success=False,
                        platform=platform,
                        account_id=account_id,
                        message=f"HTTP {response.status_code}",
                    )

            except Exception as e:
                return SyncResult(
                    success=False,
                    platform=platform,
                    account_id=account_id,
                    message=str(e),
                )

    async def sync_all(self) -> List[SyncResult]:
        """
        同步所有本地凭证

        Returns:
            同步结果列表
        """
        results = []

        if not self._credentials_dir.exists():
            return results

        for platform_dir in self._credentials_dir.iterdir():
            if platform_dir.is_dir() and not platform_dir.name.startswith("."):
                for cred_file in platform_dir.glob("*.enc"):
                    account_id = cred_file.stem
                    result = await self.sync_credential(
                        platform=platform_dir.name,
                        account_id=account_id,
                    )
                    results.append(result)

        return results

    async def pull_credential(
        self,
        platform: str,
        account_id: str,
    ) -> SyncResult:
        """
        从云端拉取凭证

        Args:
            platform: 平台名称
            account_id: 账号ID

        Returns:
            拉取结果
        """
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self._api_base_url}/api/v1/credentials/{platform}/{account_id}",
                    headers=self._get_headers(),
                    timeout=30.0,
                )

                if response.status_code == 200:
                    result = response.json()
                    data = result.get("data")

                    if data:
                        # 保存到本地
                        encrypted_data = base64.b64decode(data["encrypted_data"])
                        cred_dir = self._credentials_dir / platform
                        cred_dir.mkdir(parents=True, exist_ok=True)

                        cred_path = cred_dir / f"{account_id}.enc"
                        with open(cred_path, "wb") as f:
                            f.write(encrypted_data)

                        # 设置文件权限
                        try:
                            cred_path.chmod(0o600)
                        except OSError:
                            pass

                        # 更新同步状态
                        state = self._load_sync_state()
                        key = f"{platform}/{account_id}"
                        state["synced"][key] = {
                            "version": data["version"],
                            "synced_at": datetime.now().isoformat(),
                        }
                        self._save_sync_state(state)

                        return SyncResult(
                            success=True,
                            platform=platform,
                            account_id=account_id,
                            version=data["version"],
                            message="拉取成功",
                        )
                    else:
                        return SyncResult(
                            success=False,
                            platform=platform,
                            account_id=account_id,
                            message="凭证不存在",
                        )
                else:
                    return SyncResult(
                        success=False,
                        platform=platform,
                        account_id=account_id,
                        message=f"HTTP {response.status_code}",
                    )

            except Exception as e:
                return SyncResult(
                    success=False,
                    platform=platform,
                    account_id=account_id,
                    message=str(e),
                )

    async def list_remote_credentials(self) -> List[Dict[str, Any]]:
        """
        列出云端凭证

        Returns:
            凭证列表
        """
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self._api_base_url}/api/v1/credentials",
                    headers=self._get_headers(),
                    timeout=30.0,
                )

                if response.status_code == 200:
                    result = response.json()
                    return result.get("data", {}).get("credentials", [])
                else:
                    return []

            except Exception:
                return []
