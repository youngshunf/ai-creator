"""
文件存储工具 - 支持本地和云端文件存储
@author Ysf
"""

import os
import uuid
import base64
from pathlib import Path
from typing import Optional, Union
from enum import Enum

from ..base import (
    ToolInterface,
    ToolMetadata,
    ToolResult,
    ToolCapability,
    ToolExecutionError,
)
from ...runtime.interfaces import RuntimeType
from ...runtime.context import RuntimeContext
from ...resource.uri import AssetURI


class StorageOperation(str, Enum):
    """存储操作类型"""

    SAVE = "save"
    LOAD = "load"
    DELETE = "delete"
    EXISTS = "exists"
    LIST = "list"


class StorageTool(ToolInterface):
    """
    文件存储工具

    支持本地和云端文件存储操作。

    本地模式: 使用本地文件系统
    云端模式: 使用 S3/MinIO 对象存储
    """

    metadata = ToolMetadata(
        name="storage",
        description="文件存储工具，支持保存、读取、删除文件",
        capabilities=[ToolCapability.FILE_STORAGE],
        supported_runtimes=[RuntimeType.LOCAL, RuntimeType.CLOUD],
    )

    def __init__(self):
        """初始化工具"""
        pass

    async def execute(self, ctx: RuntimeContext, **kwargs) -> ToolResult:
        """
        执行存储操作

        Args:
            ctx: 运行时上下文
            **kwargs: 工具参数
                - operation (str): 操作类型 (save/load/delete/exists/list)
                - uri (str, optional): 资源 URI (load/delete/exists 时必填)
                - data (str, optional): 要保存的数据 (save 时必填，base64 编码)
                - asset_type (str, optional): 资源类型 (save 时使用，如 image/text/video)
                - asset_id (str, optional): 资源 ID (save 时可选，不提供则自动生成)
                - prefix (str, optional): 列表查询前缀 (list 时使用)

        Returns:
            ToolResult: 操作结果

        Raises:
            ToolExecutionError: 执行失败
        """
        try:
            operation = kwargs.get("operation")
            if not operation:
                raise ToolExecutionError("缺少必填参数: operation")

            operation = StorageOperation(operation)

            if operation == StorageOperation.SAVE:
                return await self._save(ctx, **kwargs)
            elif operation == StorageOperation.LOAD:
                return await self._load(ctx, **kwargs)
            elif operation == StorageOperation.DELETE:
                return await self._delete(ctx, **kwargs)
            elif operation == StorageOperation.EXISTS:
                return await self._exists(ctx, **kwargs)
            elif operation == StorageOperation.LIST:
                return await self._list(ctx, **kwargs)
            else:
                raise ToolExecutionError(f"不支持的操作类型: {operation}")

        except ToolExecutionError:
            raise
        except ValueError as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"参数错误: {e}",
            )
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"存储操作失败: {e}",
            )

    async def _save(self, ctx: RuntimeContext, **kwargs) -> ToolResult:
        """保存文件"""
        data = kwargs.get("data")
        if not data:
            raise ToolExecutionError("缺少必填参数: data")

        asset_type = kwargs.get("asset_type", "file")
        asset_id = kwargs.get("asset_id") or str(uuid.uuid4())

        # 解码 base64 数据
        try:
            file_data = base64.b64decode(data)
        except Exception:
            # 如果不是 base64，当作普通文本处理
            file_data = data.encode("utf-8")

        if ctx.runtime_type == RuntimeType.LOCAL:
            return await self._save_local(ctx, asset_type, asset_id, file_data)
        else:
            return await self._save_cloud(ctx, asset_type, asset_id, file_data)

    async def _save_local(
        self,
        ctx: RuntimeContext,
        asset_type: str,
        asset_id: str,
        data: bytes,
    ) -> ToolResult:
        """保存到本地文件系统"""
        # 获取基础路径
        base_path = Path(ctx.extra.get("data_path", "~/.ai-creator/data")).expanduser()
        file_path = base_path / asset_type / asset_id

        # 确保目录存在
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # 写入文件
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
            raise ToolExecutionError(f"写入文件失败: {e}")

        # 构建 URI
        uri = f"asset://local/{asset_type}/{asset_id}"

        return ToolResult(
            success=True,
            data={
                "uri": uri,
                "path": str(file_path),
                "size": len(data),
                "asset_type": asset_type,
                "asset_id": asset_id,
            },
            metadata={
                "runtime_type": RuntimeType.LOCAL.value,
            },
        )

    async def _save_cloud(
        self,
        ctx: RuntimeContext,
        asset_type: str,
        asset_id: str,
        data: bytes,
    ) -> ToolResult:
        """保存到云端存储 (S3/MinIO)"""
        try:
            import boto3
            from botocore.exceptions import ClientError
        except ImportError:
            return ToolResult(
                success=False,
                data=None,
                error="未安装 boto3 库，请运行: pip install boto3",
            )

        # 获取 S3 配置
        s3_config = ctx.extra.get("s3", {})
        bucket = s3_config.get("bucket", "ai-creator-assets")
        endpoint_url = s3_config.get("endpoint_url")

        # 获取 AWS 凭证
        aws_access_key = ctx.get_api_key("aws_access_key") or s3_config.get(
            "access_key"
        )
        aws_secret_key = ctx.get_api_key("aws_secret_key") or s3_config.get(
            "secret_key"
        )

        if not aws_access_key or not aws_secret_key:
            raise ToolExecutionError("未配置 AWS/S3 凭证")

        # 创建 S3 客户端
        client_kwargs = {
            "aws_access_key_id": aws_access_key,
            "aws_secret_access_key": aws_secret_key,
        }
        if endpoint_url:
            client_kwargs["endpoint_url"] = endpoint_url

        s3_client = boto3.client("s3", **client_kwargs)

        # 构建对象键
        user_id = ctx.user_id or "anonymous"
        object_key = f"{user_id}/{asset_type}/{asset_id}"

        # 上传文件
        try:
            s3_client.put_object(
                Bucket=bucket,
                Key=object_key,
                Body=data,
            )
        except ClientError as e:
            raise ToolExecutionError(f"上传到 S3 失败: {e}")

        # 构建 URI
        uri = f"asset://cloud/{asset_type}/{asset_id}"

        return ToolResult(
            success=True,
            data={
                "uri": uri,
                "bucket": bucket,
                "key": object_key,
                "size": len(data),
                "asset_type": asset_type,
                "asset_id": asset_id,
            },
            metadata={
                "runtime_type": RuntimeType.CLOUD.value,
            },
        )

    async def _load(self, ctx: RuntimeContext, **kwargs) -> ToolResult:
        """加载文件"""
        uri = kwargs.get("uri")
        if not uri:
            raise ToolExecutionError("缺少必填参数: uri")

        # 解析 URI
        asset_uri = AssetURI.parse(uri)

        if asset_uri.location == "local":
            return await self._load_local(ctx, asset_uri)
        else:
            return await self._load_cloud(ctx, asset_uri)

    async def _load_local(self, ctx: RuntimeContext, asset_uri: AssetURI) -> ToolResult:
        """从本地加载文件"""
        base_path = Path(ctx.extra.get("data_path", "~/.ai-creator/data")).expanduser()
        file_path = base_path / asset_uri.asset_type / asset_uri.asset_id

        if not file_path.exists():
            return ToolResult(
                success=False,
                data=None,
                error=f"文件不存在: {asset_uri.uri}",
            )

        try:
            try:
                import aiofiles

                async with aiofiles.open(file_path, "rb") as f:
                    data = await f.read()
            except ImportError:
                with open(file_path, "rb") as f:
                    data = f.read()
        except Exception as e:
            raise ToolExecutionError(f"读取文件失败: {e}")

        # 返回 base64 编码的数据
        return ToolResult(
            success=True,
            data={
                "uri": asset_uri.uri,
                "data": base64.b64encode(data).decode("utf-8"),
                "size": len(data),
            },
            metadata={
                "path": str(file_path),
            },
        )

    async def _load_cloud(self, ctx: RuntimeContext, asset_uri: AssetURI) -> ToolResult:
        """从云端加载文件"""
        try:
            import boto3
            from botocore.exceptions import ClientError
        except ImportError:
            return ToolResult(
                success=False,
                data=None,
                error="未安装 boto3 库",
            )

        # 获取 S3 配置
        s3_config = ctx.extra.get("s3", {})
        bucket = s3_config.get("bucket", "ai-creator-assets")
        endpoint_url = s3_config.get("endpoint_url")

        aws_access_key = ctx.get_api_key("aws_access_key") or s3_config.get(
            "access_key"
        )
        aws_secret_key = ctx.get_api_key("aws_secret_key") or s3_config.get(
            "secret_key"
        )

        if not aws_access_key or not aws_secret_key:
            raise ToolExecutionError("未配置 AWS/S3 凭证")

        client_kwargs = {
            "aws_access_key_id": aws_access_key,
            "aws_secret_access_key": aws_secret_key,
        }
        if endpoint_url:
            client_kwargs["endpoint_url"] = endpoint_url

        s3_client = boto3.client("s3", **client_kwargs)

        # 构建对象键
        user_id = ctx.user_id or "anonymous"
        object_key = f"{user_id}/{asset_uri.asset_type}/{asset_uri.asset_id}"

        try:
            response = s3_client.get_object(Bucket=bucket, Key=object_key)
            data = response["Body"].read()
        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchKey":
                return ToolResult(
                    success=False,
                    data=None,
                    error=f"文件不存在: {asset_uri.uri}",
                )
            raise ToolExecutionError(f"从 S3 读取失败: {e}")

        return ToolResult(
            success=True,
            data={
                "uri": asset_uri.uri,
                "data": base64.b64encode(data).decode("utf-8"),
                "size": len(data),
            },
            metadata={
                "bucket": bucket,
                "key": object_key,
            },
        )

    async def _delete(self, ctx: RuntimeContext, **kwargs) -> ToolResult:
        """删除文件"""
        uri = kwargs.get("uri")
        if not uri:
            raise ToolExecutionError("缺少必填参数: uri")

        asset_uri = AssetURI.parse(uri)

        if asset_uri.location == "local":
            return await self._delete_local(ctx, asset_uri)
        else:
            return await self._delete_cloud(ctx, asset_uri)

    async def _delete_local(
        self, ctx: RuntimeContext, asset_uri: AssetURI
    ) -> ToolResult:
        """从本地删除文件"""
        base_path = Path(ctx.extra.get("data_path", "~/.ai-creator/data")).expanduser()
        file_path = base_path / asset_uri.asset_type / asset_uri.asset_id

        if not file_path.exists():
            return ToolResult(
                success=False,
                data=None,
                error=f"文件不存在: {asset_uri.uri}",
            )

        try:
            os.remove(file_path)
        except Exception as e:
            raise ToolExecutionError(f"删除文件失败: {e}")

        return ToolResult(
            success=True,
            data={
                "uri": asset_uri.uri,
                "deleted": True,
            },
        )

    async def _delete_cloud(
        self, ctx: RuntimeContext, asset_uri: AssetURI
    ) -> ToolResult:
        """从云端删除文件"""
        try:
            import boto3
            from botocore.exceptions import ClientError
        except ImportError:
            return ToolResult(
                success=False,
                data=None,
                error="未安装 boto3 库",
            )

        s3_config = ctx.extra.get("s3", {})
        bucket = s3_config.get("bucket", "ai-creator-assets")
        endpoint_url = s3_config.get("endpoint_url")

        aws_access_key = ctx.get_api_key("aws_access_key") or s3_config.get(
            "access_key"
        )
        aws_secret_key = ctx.get_api_key("aws_secret_key") or s3_config.get(
            "secret_key"
        )

        if not aws_access_key or not aws_secret_key:
            raise ToolExecutionError("未配置 AWS/S3 凭证")

        client_kwargs = {
            "aws_access_key_id": aws_access_key,
            "aws_secret_access_key": aws_secret_key,
        }
        if endpoint_url:
            client_kwargs["endpoint_url"] = endpoint_url

        s3_client = boto3.client("s3", **client_kwargs)

        user_id = ctx.user_id or "anonymous"
        object_key = f"{user_id}/{asset_uri.asset_type}/{asset_uri.asset_id}"

        try:
            s3_client.delete_object(Bucket=bucket, Key=object_key)
        except ClientError as e:
            raise ToolExecutionError(f"从 S3 删除失败: {e}")

        return ToolResult(
            success=True,
            data={
                "uri": asset_uri.uri,
                "deleted": True,
            },
        )

    async def _exists(self, ctx: RuntimeContext, **kwargs) -> ToolResult:
        """检查文件是否存在"""
        uri = kwargs.get("uri")
        if not uri:
            raise ToolExecutionError("缺少必填参数: uri")

        asset_uri = AssetURI.parse(uri)

        if asset_uri.location == "local":
            base_path = Path(
                ctx.extra.get("data_path", "~/.ai-creator/data")
            ).expanduser()
            file_path = base_path / asset_uri.asset_type / asset_uri.asset_id
            exists = file_path.exists()
        else:
            # 云端检查 - 简化处理，尝试加载
            result = await self._load_cloud(ctx, asset_uri)
            exists = result.success

        return ToolResult(
            success=True,
            data={
                "uri": uri,
                "exists": exists,
            },
        )

    async def _list(self, ctx: RuntimeContext, **kwargs) -> ToolResult:
        """列出文件"""
        prefix = kwargs.get("prefix", "")
        asset_type = kwargs.get("asset_type")

        if ctx.runtime_type == RuntimeType.LOCAL:
            base_path = Path(
                ctx.extra.get("data_path", "~/.ai-creator/data")
            ).expanduser()

            if asset_type:
                search_path = base_path / asset_type
            else:
                search_path = base_path

            if not search_path.exists():
                return ToolResult(
                    success=True,
                    data={"files": [], "total": 0},
                )

            files = []
            for f in search_path.rglob("*"):
                if f.is_file():
                    rel_path = f.relative_to(base_path)
                    parts = list(rel_path.parts)
                    if len(parts) >= 2:
                        uri = f"asset://local/{parts[0]}/{parts[1]}"
                        if not prefix or uri.startswith(prefix):
                            files.append({
                                "uri": uri,
                                "size": f.stat().st_size,
                            })

            return ToolResult(
                success=True,
                data={
                    "files": files,
                    "total": len(files),
                },
            )
        else:
            # 云端列表
            return ToolResult(
                success=False,
                data=None,
                error="云端列表功能待实现",
            )

    def get_schema(self) -> dict:
        """
        获取工具参数 Schema

        Returns:
            JSON Schema 定义
        """
        return {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "description": "操作类型",
                    "enum": ["save", "load", "delete", "exists", "list"],
                },
                "uri": {
                    "type": "string",
                    "description": "资源 URI (load/delete/exists 时必填)",
                },
                "data": {
                    "type": "string",
                    "description": "要保存的数据，base64 编码 (save 时必填)",
                },
                "asset_type": {
                    "type": "string",
                    "description": "资源类型，如 image/text/video (save 时使用)",
                },
                "asset_id": {
                    "type": "string",
                    "description": "资源 ID (save 时可选，不提供则自动生成)",
                },
                "prefix": {
                    "type": "string",
                    "description": "列表查询前缀 (list 时使用)",
                },
            },
            "required": ["operation"],
        }
