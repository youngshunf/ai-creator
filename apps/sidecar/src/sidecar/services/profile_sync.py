"""
用户资料同步客户端 - 将本地用户资料同步到云端

@author Ysf
@date 2026-01-15
"""

import logging
from typing import Dict, Any, Optional
import httpx

logger = logging.getLogger(__name__)

class ProfileSyncClient:
    """
    用户资料同步客户端
    
    负责将本地获取的平台账号资料（Profile）同步到云端后端。
    """
    
    def __init__(self, api_base_url: str, auth_token: str):
        """
        初始化同步客户端
        
        Args:
            api_base_url: API 基础地址
            auth_token: 认证 Token
        """
        self.api_base_url = api_base_url.rstrip("/")
        self.auth_token = auth_token
        
    async def sync_profile(self, platform: str, account_id: str, profile_data: Dict[str, Any]) -> bool:
        """
        同步用户资料到云端
        
        Args:
            platform: 平台名称
            account_id: 账号ID
            profile_data: 资料数据 (nickname, avatar_url, stats...)
            
        Returns:
            bool: 是否成功
        """
        url = f"{self.api_base_url}/api/v1/accounts/sync-profile"
        headers = {
            "Authorization": f"Bearer {self.auth_token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "platform": platform,
            "account_id": account_id,
            "profile": profile_data
        }
        
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(url, json=payload, headers=headers, timeout=10.0)
                
                if resp.status_code == 200:
                    result = resp.json()
                    if result.get("success", False) or result.get("code") == 0:
                        logger.info(f"[PROFILE_SYNC] Synced {platform}:{account_id} to cloud")
                        return True
                    else:
                        logger.warning(f"[PROFILE_SYNC] Failed to sync: {result}")
                        return False
                else:
                    logger.error(f"[PROFILE_SYNC] HTTP error {resp.status_code}: {resp.text}")
                    return False
                    
        except Exception as e:
            logger.error(f"[PROFILE_SYNC] Network error: {e}")
            return False
