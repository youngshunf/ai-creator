"""
图像生成工具 - 支持多种图像生成 API
@author Ysf
"""

import base64
from typing import Optional, List, Dict, Any
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


class ImageGenProvider(str, Enum):
    """图像生成提供商"""

    OPENAI = "openai"  # DALL-E
    COMFYUI = "comfyui"  # ComfyUI (Stable Diffusion)
    REPLICATE = "replicate"  # Replicate API


class ImageGenTool(ToolInterface):
    """
    图像生成工具

    支持多种图像生成 API:
    - OpenAI DALL-E
    - ComfyUI (Stable Diffusion)
    - Replicate API

    注意: 图像生成通常需要较长时间和较高成本
    """

    metadata = ToolMetadata(
        name="image_gen",
        description="使用 AI 生成图像",
        capabilities=[ToolCapability.IMAGE_GEN],
        supported_runtimes=[RuntimeType.CLOUD],  # 仅云端支持
        fallback_tool="web_search",  # 本地回退到搜索图片
    )

    def __init__(self):
        """初始化工具"""
        pass

    async def execute(self, ctx: RuntimeContext, **kwargs) -> ToolResult:
        """
        执行图像生成

        Args:
            ctx: 运行时上下文
            **kwargs: 工具参数
                - prompt (str): 图像描述提示词
                - negative_prompt (str, optional): 负面提示词（排除元素）
                - style (str, optional): 图像风格
                - size (str, optional): 图像尺寸 (1024x1024, 512x512 等)
                - count (int, optional): 生成数量，默认 1
                - provider (str, optional): 使用的提供商
                - model (str, optional): 使用的模型

        Returns:
            ToolResult: 包含生成的图像 URL 或 base64 数据

        Raises:
            ToolExecutionError: 执行失败
        """
        try:
            # 提取参数
            prompt = kwargs.get("prompt")
            if not prompt:
                raise ToolExecutionError("缺少必填参数: prompt")

            provider = kwargs.get("provider", ImageGenProvider.OPENAI.value)
            provider = ImageGenProvider(provider)

            if provider == ImageGenProvider.OPENAI:
                return await self._generate_with_openai(ctx, **kwargs)
            elif provider == ImageGenProvider.COMFYUI:
                return await self._generate_with_comfyui(ctx, **kwargs)
            elif provider == ImageGenProvider.REPLICATE:
                return await self._generate_with_replicate(ctx, **kwargs)
            else:
                raise ToolExecutionError(f"不支持的提供商: {provider}")

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
                error=f"图像生成失败: {e}",
            )

    async def _generate_with_openai(
        self, ctx: RuntimeContext, **kwargs
    ) -> ToolResult:
        """使用 OpenAI DALL-E 生成图像"""
        try:
            from openai import AsyncOpenAI
        except ImportError:
            return ToolResult(
                success=False,
                data=None,
                error="未安装 openai 库，请运行: pip install openai",
            )

        # 获取 API 密钥
        api_key = ctx.get_api_key("openai")
        if not api_key:
            raise ToolExecutionError("未配置 OpenAI API 密钥")

        # 提取参数
        prompt = kwargs.get("prompt")
        size = kwargs.get("size", "1024x1024")
        count = min(kwargs.get("count", 1), 4)  # DALL-E 最多 4 张
        model = kwargs.get("model", "dall-e-3")
        quality = kwargs.get("quality", "standard")
        style = kwargs.get("style", "vivid")

        # 创建客户端
        client = AsyncOpenAI(api_key=api_key)

        try:
            response = await client.images.generate(
                model=model,
                prompt=prompt,
                size=size,
                n=count,
                quality=quality,
                style=style,
                response_format="url",
            )
        except Exception as e:
            raise ToolExecutionError(f"OpenAI API 错误: {e}")

        # 处理结果
        images = []
        for item in response.data:
            images.append({
                "url": item.url,
                "revised_prompt": getattr(item, "revised_prompt", None),
            })

        return ToolResult(
            success=True,
            data={
                "images": images,
                "count": len(images),
                "prompt": prompt,
            },
            metadata={
                "provider": ImageGenProvider.OPENAI.value,
                "model": model,
                "size": size,
            },
        )

    async def _generate_with_comfyui(
        self, ctx: RuntimeContext, **kwargs
    ) -> ToolResult:
        """使用 ComfyUI 生成图像"""
        try:
            import aiohttp
        except ImportError:
            return ToolResult(
                success=False,
                data=None,
                error="未安装 aiohttp 库，请运行: pip install aiohttp",
            )

        # 获取 ComfyUI 配置
        comfyui_config = ctx.extra.get("comfyui", {})
        server_url = comfyui_config.get("server_url")

        if not server_url:
            raise ToolExecutionError("未配置 ComfyUI 服务器地址")

        # 提取参数
        prompt = kwargs.get("prompt")
        negative_prompt = kwargs.get("negative_prompt", "")
        size = kwargs.get("size", "1024x1024")
        count = kwargs.get("count", 1)
        model = kwargs.get("model", "sd_xl_base_1.0.safetensors")
        steps = kwargs.get("steps", 20)
        cfg_scale = kwargs.get("cfg_scale", 7.0)
        seed = kwargs.get("seed", -1)

        # 解析尺寸
        try:
            width, height = map(int, size.split("x"))
        except ValueError:
            width, height = 1024, 1024

        # 构建 ComfyUI 工作流
        workflow = self._build_comfyui_workflow(
            prompt=prompt,
            negative_prompt=negative_prompt,
            width=width,
            height=height,
            batch_size=count,
            model=model,
            steps=steps,
            cfg_scale=cfg_scale,
            seed=seed,
        )

        # 提交任务
        async with aiohttp.ClientSession() as session:
            # 提交工作流
            async with session.post(
                f"{server_url}/prompt",
                json={"prompt": workflow},
            ) as resp:
                if resp.status != 200:
                    raise ToolExecutionError(f"ComfyUI 提交失败: {await resp.text()}")
                result = await resp.json()
                prompt_id = result.get("prompt_id")

            # 等待完成并获取结果
            images = await self._wait_for_comfyui_result(
                session, server_url, prompt_id
            )

        return ToolResult(
            success=True,
            data={
                "images": images,
                "count": len(images),
                "prompt": prompt,
            },
            metadata={
                "provider": ImageGenProvider.COMFYUI.value,
                "model": model,
                "size": size,
                "steps": steps,
            },
        )

    def _build_comfyui_workflow(
        self,
        prompt: str,
        negative_prompt: str,
        width: int,
        height: int,
        batch_size: int,
        model: str,
        steps: int,
        cfg_scale: float,
        seed: int,
    ) -> Dict[str, Any]:
        """构建 ComfyUI 工作流"""
        # 标准 SDXL 工作流
        return {
            "3": {
                "inputs": {
                    "seed": seed if seed >= 0 else 0,
                    "steps": steps,
                    "cfg": cfg_scale,
                    "sampler_name": "euler",
                    "scheduler": "normal",
                    "denoise": 1,
                    "model": ["4", 0],
                    "positive": ["6", 0],
                    "negative": ["7", 0],
                    "latent_image": ["5", 0],
                },
                "class_type": "KSampler",
            },
            "4": {
                "inputs": {"ckpt_name": model},
                "class_type": "CheckpointLoaderSimple",
            },
            "5": {
                "inputs": {
                    "width": width,
                    "height": height,
                    "batch_size": batch_size,
                },
                "class_type": "EmptyLatentImage",
            },
            "6": {
                "inputs": {
                    "text": prompt,
                    "clip": ["4", 1],
                },
                "class_type": "CLIPTextEncode",
            },
            "7": {
                "inputs": {
                    "text": negative_prompt,
                    "clip": ["4", 1],
                },
                "class_type": "CLIPTextEncode",
            },
            "8": {
                "inputs": {
                    "samples": ["3", 0],
                    "vae": ["4", 2],
                },
                "class_type": "VAEDecode",
            },
            "9": {
                "inputs": {
                    "filename_prefix": "ComfyUI",
                    "images": ["8", 0],
                },
                "class_type": "SaveImage",
            },
        }

    async def _wait_for_comfyui_result(
        self,
        session,
        server_url: str,
        prompt_id: str,
        timeout: int = 300,
    ) -> List[Dict[str, Any]]:
        """等待 ComfyUI 结果"""
        import asyncio

        start_time = asyncio.get_event_loop().time()

        while True:
            # 检查超时
            if asyncio.get_event_loop().time() - start_time > timeout:
                raise ToolExecutionError("ComfyUI 生成超时")

            # 查询状态
            async with session.get(f"{server_url}/history/{prompt_id}") as resp:
                if resp.status != 200:
                    await asyncio.sleep(1)
                    continue

                history = await resp.json()
                if prompt_id in history:
                    outputs = history[prompt_id].get("outputs", {})
                    # 查找图像输出
                    for node_id, node_output in outputs.items():
                        if "images" in node_output:
                            images = []
                            for img in node_output["images"]:
                                # 获取图像 URL
                                filename = img.get("filename")
                                subfolder = img.get("subfolder", "")
                                url = f"{server_url}/view?filename={filename}&subfolder={subfolder}&type=output"
                                images.append({
                                    "url": url,
                                    "filename": filename,
                                })
                            return images

            await asyncio.sleep(1)

    async def _generate_with_replicate(
        self, ctx: RuntimeContext, **kwargs
    ) -> ToolResult:
        """使用 Replicate API 生成图像"""
        try:
            import replicate
        except ImportError:
            return ToolResult(
                success=False,
                data=None,
                error="未安装 replicate 库，请运行: pip install replicate",
            )

        # 获取 API 密钥
        api_token = ctx.get_api_key("replicate")
        if not api_token:
            raise ToolExecutionError("未配置 Replicate API Token")

        # 设置环境变量
        import os

        os.environ["REPLICATE_API_TOKEN"] = api_token

        # 提取参数
        prompt = kwargs.get("prompt")
        negative_prompt = kwargs.get("negative_prompt", "")
        size = kwargs.get("size", "1024x1024")
        model = kwargs.get(
            "model", "stability-ai/sdxl:39ed52f2a78e934b3ba6e2a89f5b1c712de7dfea535525255b1aa35c5565e08b"
        )

        # 解析尺寸
        try:
            width, height = map(int, size.split("x"))
        except ValueError:
            width, height = 1024, 1024

        try:
            output = replicate.run(
                model,
                input={
                    "prompt": prompt,
                    "negative_prompt": negative_prompt,
                    "width": width,
                    "height": height,
                },
            )
        except Exception as e:
            raise ToolExecutionError(f"Replicate API 错误: {e}")

        # 处理结果
        images = []
        if isinstance(output, list):
            for url in output:
                images.append({"url": url})
        elif isinstance(output, str):
            images.append({"url": output})

        return ToolResult(
            success=True,
            data={
                "images": images,
                "count": len(images),
                "prompt": prompt,
            },
            metadata={
                "provider": ImageGenProvider.REPLICATE.value,
                "model": model,
                "size": size,
            },
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
                "prompt": {
                    "type": "string",
                    "description": "图像描述提示词",
                },
                "negative_prompt": {
                    "type": "string",
                    "description": "负面提示词，描述不想出现的元素",
                },
                "style": {
                    "type": "string",
                    "description": "图像风格 (vivid/natural)",
                    "enum": ["vivid", "natural"],
                    "default": "vivid",
                },
                "size": {
                    "type": "string",
                    "description": "图像尺寸",
                    "enum": ["1024x1024", "1024x1792", "1792x1024", "512x512"],
                    "default": "1024x1024",
                },
                "count": {
                    "type": "integer",
                    "description": "生成数量",
                    "default": 1,
                    "minimum": 1,
                    "maximum": 4,
                },
                "provider": {
                    "type": "string",
                    "description": "图像生成提供商",
                    "enum": ["openai", "comfyui", "replicate"],
                    "default": "openai",
                },
                "model": {
                    "type": "string",
                    "description": "使用的模型（可选）",
                },
                "quality": {
                    "type": "string",
                    "description": "图像质量 (standard/hd)，仅 OpenAI 支持",
                    "enum": ["standard", "hd"],
                    "default": "standard",
                },
            },
            "required": ["prompt"],
        }
