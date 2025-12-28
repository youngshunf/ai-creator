"""
资源解析器 - 将 URI 解析为实际路径
@author Ysf
"""

import os
import uuid
import hashlib
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Dict, Any, Union

from .uri import AssetURI


class AssetResolver(ABC):
    """
    资源解析器抽象基类

    定义资源解析的通用接口，支持：
    - 解析 URI 到实际路径/URL
    - 存储资源并返回 URI
    - 检查资源是否存在
    - 删除资源
    """

    @abstractmethod
    async def resolve(self, uri: Union[str, AssetURI]) -> Optional[str]:
        """
        将 URI 解析为实际路径或 URL

        Args:
            uri: 资源 URI 字符串或 AssetURI 对象

        Returns:
            实际路径或 URL，如果资源不存在则返回 None
        """
        pass

    @abstractmethod
    async def store(
        self,
        asset_type: str,
        data: bytes,
        asset_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        存储资源并返回 URI

        Args:
            asset_type: 资源类型 (image/text/video/audio 等)
            data: 资源数据
            asset_id: 资源 ID（可选，不提供则自动生成）
            metadata: 资源元数据（可选）

        Returns:
            资源 URI
        """
        pass

    @abstractmethod
    async def exists(self, uri: Union[str, AssetURI]) -> bool:
        """
        检查资源是否存在

        Args:
            uri: 资源 URI

        Returns:
            True 表示存在，False 表示不存在
        """
        pass

    @abstractmethod
    async def delete(self, uri: Union[str, AssetURI]) -> bool:
        """
        删除资源

        Args:
            uri: 资源 URI

        Returns:
            True 表示删除成功，False 表示失败或资源不存在
        """
        pass

    def _parse_uri(self, uri: Union[str, AssetURI]) -> AssetURI:
        """解析 URI 字符串为 AssetURI 对象"""
        if isinstance(uri, AssetURI):
            return uri
        return AssetURI.parse(uri)


class LocalAssetResolver(AssetResolver):
    """
    本地资源解析器

    将 asset://local/... URI 解析为本地文件系统路径。
    支持资源存储、读取、删除等操作。

    目录结构:
        {base_path}/
        ├── image/
        │   ├── {asset_id_1}
        │   └── {asset_id_2}
        ├── text/
        │   └── {asset_id_3}
        └── video/
            └── {asset_id_4}
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化本地资源解析器

        Args:
            config: 配置字典
                - data_path: 数据存储目录，默认 ~/.ai-creator/data
                - cache_path: 缓存目录，默认 ~/.ai-creator/cache
        """
        config = config or {}
        self.base_path = Path(
            config.get("data_path", "~/.ai-creator/data")
        ).expanduser()
        self.cache_path = Path(
            config.get("cache_path", "~/.ai-creator/cache")
        ).expanduser()

        # 确保目录存在
        self.base_path.mkdir(parents=True, exist_ok=True)
        self.cache_path.mkdir(parents=True, exist_ok=True)

    async def resolve(self, uri: Union[str, AssetURI]) -> Optional[str]:
        """
        将 URI 解析为本地文件路径

        Args:
            uri: 资源 URI

        Returns:
            本地文件路径，如果文件不存在则返回 None
        """
        asset_uri = self._parse_uri(uri)

        if asset_uri.location == "cloud":
            # 云端资源需要先下载到本地缓存
            return await self._download_cloud_asset(asset_uri)

        # 本地资源直接返回路径
        file_path = self.base_path / asset_uri.asset_type / asset_uri.asset_id

        if file_path.exists():
            return str(file_path)
        return None

    async def store(
        self,
        asset_type: str,
        data: bytes,
        asset_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        存储资源到本地文件系统

        Args:
            asset_type: 资源类型
            data: 资源数据
            asset_id: 资源 ID（可选）
            metadata: 资源元数据（可选）

        Returns:
            资源 URI
        """
        # 生成或使用提供的 asset_id
        if not asset_id:
            # 使用数据哈希和 UUID 组合生成唯一 ID
            data_hash = hashlib.md5(data).hexdigest()[:8]
            asset_id = f"{data_hash}-{uuid.uuid4().hex[:8]}"

        # 确保类型目录存在
        type_dir = self.base_path / asset_type
        type_dir.mkdir(parents=True, exist_ok=True)

        # 写入文件
        file_path = type_dir / asset_id

        try:
            # 使用 aiofiles 如果可用
            try:
                import aiofiles

                async with aiofiles.open(file_path, "wb") as f:
                    await f.write(data)
            except ImportError:
                # 回退到同步写入
                with open(file_path, "wb") as f:
                    f.write(data)
        except Exception as e:
            raise IOError(f"写入文件失败: {e}")

        # 保存元数据（如果提供）
        if metadata:
            await self._save_metadata(asset_type, asset_id, metadata)

        return f"asset://local/{asset_type}/{asset_id}"

    async def exists(self, uri: Union[str, AssetURI]) -> bool:
        """检查资源是否存在"""
        asset_uri = self._parse_uri(uri)

        if asset_uri.location == "cloud":
            # 检查缓存中是否有该云端资源
            cache_path = self._get_cache_path(asset_uri)
            return cache_path.exists()

        file_path = self.base_path / asset_uri.asset_type / asset_uri.asset_id
        return file_path.exists()

    async def delete(self, uri: Union[str, AssetURI]) -> bool:
        """删除资源"""
        asset_uri = self._parse_uri(uri)

        if asset_uri.location == "cloud":
            # 只能删除本地缓存
            cache_path = self._get_cache_path(asset_uri)
            if cache_path.exists():
                os.remove(cache_path)
                return True
            return False

        file_path = self.base_path / asset_uri.asset_type / asset_uri.asset_id

        if file_path.exists():
            os.remove(file_path)

            # 同时删除元数据
            meta_path = file_path.with_suffix(".meta.json")
            if meta_path.exists():
                os.remove(meta_path)

            return True
        return False

    async def _download_cloud_asset(self, asset_uri: AssetURI) -> Optional[str]:
        """下载云端资源到本地缓存"""
        cache_path = self._get_cache_path(asset_uri)

        # 如果缓存已存在，直接返回
        if cache_path.exists():
            return str(cache_path)

        # 需要 CloudAssetResolver 来下载
        # 这里只是占位，实际实现需要协调两个解析器
        return None

    def _get_cache_path(self, asset_uri: AssetURI) -> Path:
        """获取云端资源的本地缓存路径"""
        return self.cache_path / asset_uri.asset_type / asset_uri.asset_id

    async def _save_metadata(
        self,
        asset_type: str,
        asset_id: str,
        metadata: Dict[str, Any],
    ) -> None:
        """保存资源元数据"""
        import json

        meta_path = self.base_path / asset_type / f"{asset_id}.meta.json"

        try:
            try:
                import aiofiles

                async with aiofiles.open(meta_path, "w", encoding="utf-8") as f:
                    await f.write(json.dumps(metadata, ensure_ascii=False, indent=2))
            except ImportError:
                with open(meta_path, "w", encoding="utf-8") as f:
                    json.dump(metadata, f, ensure_ascii=False, indent=2)
        except Exception:
            pass  # 元数据保存失败不影响主流程

    async def get_metadata(self, uri: Union[str, AssetURI]) -> Optional[Dict[str, Any]]:
        """获取资源元数据"""
        import json

        asset_uri = self._parse_uri(uri)
        meta_path = (
            self.base_path / asset_uri.asset_type / f"{asset_uri.asset_id}.meta.json"
        )

        if not meta_path.exists():
            return None

        try:
            try:
                import aiofiles

                async with aiofiles.open(meta_path, "r", encoding="utf-8") as f:
                    content = await f.read()
                    return json.loads(content)
            except ImportError:
                with open(meta_path, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception:
            return None

    async def list_assets(
        self,
        asset_type: Optional[str] = None,
        prefix: Optional[str] = None,
    ) -> list:
        """
        列出资源

        Args:
            asset_type: 资源类型（可选）
            prefix: 资源 ID 前缀（可选）

        Returns:
            资源 URI 列表
        """
        assets = []

        if asset_type:
            type_dir = self.base_path / asset_type
            if type_dir.exists():
                for f in type_dir.iterdir():
                    if f.is_file() and not f.suffix == ".json":
                        if not prefix or f.name.startswith(prefix):
                            assets.append(
                                f"asset://local/{asset_type}/{f.name}"
                            )
        else:
            for type_dir in self.base_path.iterdir():
                if type_dir.is_dir():
                    for f in type_dir.iterdir():
                        if f.is_file() and not f.suffix == ".json":
                            if not prefix or f.name.startswith(prefix):
                                assets.append(
                                    f"asset://local/{type_dir.name}/{f.name}"
                                )

        return assets


class CloudAssetResolver(AssetResolver):
    """
    云端资源解析器

    将 asset://cloud/... URI 解析为 S3/MinIO 预签名 URL。
    支持资源上传、下载、删除等操作。

    存储结构:
        {bucket}/
        ├── {user_id}/
        │   ├── image/
        │   │   ├── {asset_id_1}
        │   │   └── {asset_id_2}
        │   └── text/
        │       └── {asset_id_3}
        └── ...
    """

    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
    ):
        """
        初始化云端资源解析器

        Args:
            config: 配置字典
                - bucket: S3 存储桶名称
                - endpoint_url: S3/MinIO 端点 URL（可选）
                - region: AWS 区域（可选）
                - access_key: AWS Access Key（可选，也可通过环境变量）
                - secret_key: AWS Secret Key（可选，也可通过环境变量）
                - presign_expires: 预签名 URL 有效期（秒），默认 3600
            user_id: 用户 ID
        """
        config = config or {}
        self.bucket = config.get("bucket", "ai-creator-assets")
        self.endpoint_url = config.get("endpoint_url")
        self.region = config.get("region", "us-east-1")
        self.access_key = config.get("access_key")
        self.secret_key = config.get("secret_key")
        self.presign_expires = config.get("presign_expires", 3600)
        self.user_id = user_id or "anonymous"

        self._client = None

    def _get_client(self):
        """获取或创建 S3 客户端"""
        if self._client is None:
            try:
                import boto3
            except ImportError:
                raise ImportError(
                    "未安装 boto3 库，请运行: pip install boto3"
                )

            client_kwargs = {
                "region_name": self.region,
            }

            if self.access_key and self.secret_key:
                client_kwargs["aws_access_key_id"] = self.access_key
                client_kwargs["aws_secret_access_key"] = self.secret_key

            if self.endpoint_url:
                client_kwargs["endpoint_url"] = self.endpoint_url

            self._client = boto3.client("s3", **client_kwargs)

        return self._client

    def _get_object_key(self, asset_uri: AssetURI) -> str:
        """获取 S3 对象键"""
        return f"{self.user_id}/{asset_uri.asset_type}/{asset_uri.asset_id}"

    async def resolve(self, uri: Union[str, AssetURI]) -> Optional[str]:
        """
        将 URI 解析为 S3 预签名 URL

        Args:
            uri: 资源 URI

        Returns:
            预签名 URL，如果资源不存在则返回 None
        """
        asset_uri = self._parse_uri(uri)

        if asset_uri.location == "local":
            # 本地资源无法直接解析
            return None

        # 检查资源是否存在
        if not await self.exists(uri):
            return None

        return await self.get_presigned_url(uri)

    async def get_presigned_url(
        self,
        uri: Union[str, AssetURI],
        expires_in: Optional[int] = None,
    ) -> str:
        """
        获取预签名下载 URL

        Args:
            uri: 资源 URI
            expires_in: URL 有效期（秒），默认使用配置值

        Returns:
            预签名 URL
        """
        asset_uri = self._parse_uri(uri)
        client = self._get_client()

        object_key = self._get_object_key(asset_uri)
        expires = expires_in or self.presign_expires

        url = client.generate_presigned_url(
            "get_object",
            Params={
                "Bucket": self.bucket,
                "Key": object_key,
            },
            ExpiresIn=expires,
        )

        return url

    async def get_presigned_upload_url(
        self,
        asset_type: str,
        asset_id: Optional[str] = None,
        expires_in: Optional[int] = None,
        content_type: Optional[str] = None,
    ) -> Dict[str, str]:
        """
        获取预签名上传 URL

        Args:
            asset_type: 资源类型
            asset_id: 资源 ID（可选）
            expires_in: URL 有效期（秒）
            content_type: 内容类型

        Returns:
            包含 url 和 asset_id 的字典
        """
        if not asset_id:
            asset_id = f"{uuid.uuid4().hex}"

        client = self._get_client()
        object_key = f"{self.user_id}/{asset_type}/{asset_id}"
        expires = expires_in or self.presign_expires

        params = {
            "Bucket": self.bucket,
            "Key": object_key,
        }

        if content_type:
            params["ContentType"] = content_type

        url = client.generate_presigned_url(
            "put_object",
            Params=params,
            ExpiresIn=expires,
        )

        return {
            "url": url,
            "asset_id": asset_id,
            "uri": f"asset://cloud/{asset_type}/{asset_id}",
        }

    async def store(
        self,
        asset_type: str,
        data: bytes,
        asset_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        上传资源到 S3

        Args:
            asset_type: 资源类型
            data: 资源数据
            asset_id: 资源 ID（可选）
            metadata: 资源元数据（可选）

        Returns:
            资源 URI
        """
        from botocore.exceptions import ClientError

        if not asset_id:
            data_hash = hashlib.md5(data).hexdigest()[:8]
            asset_id = f"{data_hash}-{uuid.uuid4().hex[:8]}"

        client = self._get_client()
        object_key = f"{self.user_id}/{asset_type}/{asset_id}"

        try:
            put_kwargs = {
                "Bucket": self.bucket,
                "Key": object_key,
                "Body": data,
            }

            if metadata:
                put_kwargs["Metadata"] = {
                    k: str(v) for k, v in metadata.items()
                }

            client.put_object(**put_kwargs)
        except ClientError as e:
            raise IOError(f"上传到 S3 失败: {e}")

        return f"asset://cloud/{asset_type}/{asset_id}"

    async def exists(self, uri: Union[str, AssetURI]) -> bool:
        """检查资源是否存在"""
        from botocore.exceptions import ClientError

        asset_uri = self._parse_uri(uri)

        if asset_uri.location == "local":
            return False

        client = self._get_client()
        object_key = self._get_object_key(asset_uri)

        try:
            client.head_object(Bucket=self.bucket, Key=object_key)
            return True
        except ClientError as e:
            if e.response["Error"]["Code"] == "404":
                return False
            raise

    async def delete(self, uri: Union[str, AssetURI]) -> bool:
        """删除资源"""
        from botocore.exceptions import ClientError

        asset_uri = self._parse_uri(uri)

        if asset_uri.location == "local":
            return False

        client = self._get_client()
        object_key = self._get_object_key(asset_uri)

        try:
            client.delete_object(Bucket=self.bucket, Key=object_key)
            return True
        except ClientError:
            return False

    async def download(self, uri: Union[str, AssetURI]) -> Optional[bytes]:
        """
        下载资源数据

        Args:
            uri: 资源 URI

        Returns:
            资源数据，如果不存在则返回 None
        """
        from botocore.exceptions import ClientError

        asset_uri = self._parse_uri(uri)

        if asset_uri.location == "local":
            return None

        client = self._get_client()
        object_key = self._get_object_key(asset_uri)

        try:
            response = client.get_object(Bucket=self.bucket, Key=object_key)
            return response["Body"].read()
        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchKey":
                return None
            raise

    async def list_assets(
        self,
        asset_type: Optional[str] = None,
        prefix: Optional[str] = None,
        max_keys: int = 1000,
    ) -> list:
        """
        列出资源

        Args:
            asset_type: 资源类型（可选）
            prefix: 资源 ID 前缀（可选）
            max_keys: 最大返回数量

        Returns:
            资源 URI 列表
        """
        client = self._get_client()

        # 构建前缀
        list_prefix = f"{self.user_id}/"
        if asset_type:
            list_prefix += f"{asset_type}/"
        if prefix:
            list_prefix += prefix

        response = client.list_objects_v2(
            Bucket=self.bucket,
            Prefix=list_prefix,
            MaxKeys=max_keys,
        )

        assets = []
        for obj in response.get("Contents", []):
            key = obj["Key"]
            # 解析 key: user_id/asset_type/asset_id
            parts = key.split("/")
            if len(parts) >= 3:
                a_type = parts[1]
                a_id = "/".join(parts[2:])
                assets.append(f"asset://cloud/{a_type}/{a_id}")

        return assets
