"""
资源 URI - 统一资源标识
@author Ysf
"""

from dataclasses import dataclass
from typing import Optional

@dataclass
class AssetURI:
    """统一资源 URI

    格式: asset://{runtime}/{type}/{id}

    runtime: local | cloud
    type: image | video | credential | temp | storage
    id: 资源唯一标识
    """
    runtime: str
    asset_type: str
    asset_id: str

    def __str__(self) -> str:
        """转换为 URI 字符串"""
        return f"asset://{self.runtime}/{self.asset_type}/{self.asset_id}"

    @classmethod
    def parse(cls, uri: str) -> Optional["AssetURI"]:
        """解析 URI 字符串"""
        if not uri.startswith("asset://"):
            return None

        parts = uri[8:].split("/")
        if len(parts) != 3:
            return None

        return cls(runtime=parts[0], asset_type=parts[1], asset_id=parts[2])
