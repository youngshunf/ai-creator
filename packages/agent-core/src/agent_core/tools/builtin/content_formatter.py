"""
内容格式化工具 - 根据平台规范格式化内容
@author Ysf
"""

import re
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


class OutputFormat(str, Enum):
    """输出格式"""

    MARKDOWN = "markdown"
    HTML = "html"
    PLAIN_TEXT = "plain_text"
    RICH_TEXT = "rich_text"


class Platform(str, Enum):
    """目标平台"""

    XIAOHONGSHU = "xiaohongshu"
    DOUYIN = "douyin"
    WEIXIN = "weixin"
    WEIBO = "weibo"
    BILIBILI = "bilibili"
    GENERAL = "general"


class ContentFormatterTool(ToolInterface):
    """
    内容格式化工具

    根据目标平台的规范格式化内容，包括：
    - 标题处理（长度限制、格式优化）
    - 正文处理（段落、换行、格式）
    - 图片布局（图文混排）
    - Emoji 和特殊字符处理
    - 平台特定格式（话题标签、@提及等）
    """

    metadata = ToolMetadata(
        name="content_formatter",
        description="根据平台规范格式化内容",
        capabilities=[ToolCapability.CONTENT_FORMATTING],
        supported_runtimes=[RuntimeType.LOCAL, RuntimeType.CLOUD],
    )

    # 平台内容约束
    PLATFORM_CONSTRAINTS = {
        Platform.XIAOHONGSHU: {
            "max_title_length": 20,
            "max_content_length": 1000,
            "max_images": 9,
            "supports_video": True,
            "hashtag_prefix": "#",
            "hashtag_suffix": "#",
        },
        Platform.DOUYIN: {
            "max_title_length": 55,
            "max_content_length": 300,
            "max_images": 0,  # 抖音主要是视频
            "supports_video": True,
            "hashtag_prefix": "#",
            "hashtag_suffix": " ",
        },
        Platform.WEIXIN: {
            "max_title_length": 64,
            "max_content_length": 20000,
            "max_images": 20,
            "supports_video": True,
            "hashtag_prefix": "#",
            "hashtag_suffix": "#",
        },
        Platform.WEIBO: {
            "max_title_length": 0,  # 微博没有标题
            "max_content_length": 2000,
            "max_images": 9,
            "supports_video": True,
            "hashtag_prefix": "#",
            "hashtag_suffix": "#",
        },
        Platform.BILIBILI: {
            "max_title_length": 80,
            "max_content_length": 2000,
            "max_images": 10,
            "supports_video": True,
            "hashtag_prefix": "#",
            "hashtag_suffix": "#",
        },
        Platform.GENERAL: {
            "max_title_length": 100,
            "max_content_length": 50000,
            "max_images": 100,
            "supports_video": True,
            "hashtag_prefix": "#",
            "hashtag_suffix": " ",
        },
    }

    def __init__(self):
        """初始化工具"""
        pass

    async def execute(self, ctx: RuntimeContext, **kwargs) -> ToolResult:
        """
        执行内容格式化

        Args:
            ctx: 运行时上下文
            **kwargs: 工具参数
                - content (str): 原始内容
                - title (str, optional): 标题
                - format (str, optional): 输出格式 (markdown/html/plain_text/rich_text)
                - platform (str, optional): 目标平台
                - images (List[str], optional): 图片 URI 列表
                - hashtags (List[str], optional): 话题标签列表
                - mentions (List[str], optional): @提及用户列表
                - truncate (bool, optional): 是否截断超长内容

        Returns:
            ToolResult: 格式化后的内容

        Raises:
            ToolExecutionError: 执行失败
        """
        try:
            # 提取参数
            content = kwargs.get("content")
            if not content:
                raise ToolExecutionError("缺少必填参数: content")

            title = kwargs.get("title", "")
            output_format = OutputFormat(kwargs.get("format", OutputFormat.MARKDOWN.value))
            platform = Platform(kwargs.get("platform", Platform.GENERAL.value))
            images = kwargs.get("images", [])
            hashtags = kwargs.get("hashtags", [])
            mentions = kwargs.get("mentions", [])
            truncate = kwargs.get("truncate", True)

            # 获取平台约束
            constraints = self.PLATFORM_CONSTRAINTS[platform]

            # 格式化标题
            formatted_title = self._format_title(title, constraints, truncate)

            # 格式化正文
            formatted_content = self._format_content(
                content, constraints, output_format, truncate
            )

            # 添加话题标签
            if hashtags:
                formatted_hashtags = self._format_hashtags(hashtags, constraints)
                formatted_content = f"{formatted_content}\n\n{formatted_hashtags}"

            # 添加 @提及
            if mentions:
                formatted_mentions = self._format_mentions(mentions)
                formatted_content = f"{formatted_content}\n\n{formatted_mentions}"

            # 处理图片布局
            if images:
                image_layout = self._format_image_layout(
                    images, constraints, output_format
                )
            else:
                image_layout = None

            # 验证内容长度
            warnings = []
            if len(formatted_content) > constraints["max_content_length"]:
                if truncate:
                    formatted_content = formatted_content[
                        : constraints["max_content_length"] - 3
                    ] + "..."
                    warnings.append("内容已截断")
                else:
                    warnings.append(
                        f"内容超过平台限制 ({len(formatted_content)}/{constraints['max_content_length']})"
                    )

            if len(images) > constraints["max_images"]:
                warnings.append(
                    f"图片数量超过平台限制 ({len(images)}/{constraints['max_images']})"
                )

            return ToolResult(
                success=True,
                data={
                    "title": formatted_title,
                    "content": formatted_content,
                    "image_layout": image_layout,
                    "format": output_format.value,
                    "platform": platform.value,
                    "char_count": len(formatted_content),
                    "image_count": len(images),
                },
                metadata={
                    "constraints": constraints,
                    "warnings": warnings,
                },
            )

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
                error=f"内容格式化失败: {e}",
            )

    def _format_title(
        self,
        title: str,
        constraints: Dict[str, Any],
        truncate: bool,
    ) -> str:
        """格式化标题"""
        if not title:
            return ""

        # 移除多余空白
        title = " ".join(title.split())

        # 限制长度
        max_length = constraints["max_title_length"]
        if max_length > 0 and len(title) > max_length:
            if truncate:
                title = title[: max_length - 3] + "..."

        return title

    def _format_content(
        self,
        content: str,
        constraints: Dict[str, Any],
        output_format: OutputFormat,
        truncate: bool,
    ) -> str:
        """格式化正文"""
        # 规范化换行符
        content = content.replace("\r\n", "\n").replace("\r", "\n")

        # 移除过多的连续换行
        content = re.sub(r"\n{3,}", "\n\n", content)

        # 移除首尾空白
        content = content.strip()

        # 根据输出格式处理
        if output_format == OutputFormat.PLAIN_TEXT:
            content = self._strip_markdown(content)
        elif output_format == OutputFormat.HTML:
            content = self._markdown_to_html(content)
        elif output_format == OutputFormat.RICH_TEXT:
            content = self._to_rich_text(content)
        # MARKDOWN 格式保持原样

        return content

    def _strip_markdown(self, content: str) -> str:
        """移除 Markdown 格式"""
        # 移除标题
        content = re.sub(r"^#{1,6}\s+", "", content, flags=re.MULTILINE)

        # 移除加粗
        content = re.sub(r"\*\*(.+?)\*\*", r"\1", content)
        content = re.sub(r"__(.+?)__", r"\1", content)

        # 移除斜体
        content = re.sub(r"\*(.+?)\*", r"\1", content)
        content = re.sub(r"_(.+?)_", r"\1", content)

        # 移除链接
        content = re.sub(r"\[(.+?)\]\(.+?\)", r"\1", content)

        # 移除图片
        content = re.sub(r"!\[.*?\]\(.+?\)", "", content)

        # 移除代码块
        content = re.sub(r"```[\s\S]*?```", "", content)
        content = re.sub(r"`(.+?)`", r"\1", content)

        # 移除列表标记
        content = re.sub(r"^[-*+]\s+", "", content, flags=re.MULTILINE)
        content = re.sub(r"^\d+\.\s+", "", content, flags=re.MULTILINE)

        return content

    def _markdown_to_html(self, content: str) -> str:
        """Markdown 转 HTML"""
        # 简单转换，生产环境建议使用 markdown 库
        lines = content.split("\n")
        html_lines = []
        in_list = False
        list_type = None

        for line in lines:
            # 标题
            if line.startswith("# "):
                html_lines.append(f"<h1>{line[2:]}</h1>")
            elif line.startswith("## "):
                html_lines.append(f"<h2>{line[3:]}</h2>")
            elif line.startswith("### "):
                html_lines.append(f"<h3>{line[4:]}</h3>")
            # 无序列表
            elif line.startswith("- ") or line.startswith("* "):
                if not in_list or list_type != "ul":
                    if in_list:
                        html_lines.append(f"</{list_type}>")
                    html_lines.append("<ul>")
                    in_list = True
                    list_type = "ul"
                html_lines.append(f"<li>{line[2:]}</li>")
            # 段落
            elif line.strip():
                if in_list:
                    html_lines.append(f"</{list_type}>")
                    in_list = False
                html_lines.append(f"<p>{line}</p>")
            else:
                if in_list:
                    html_lines.append(f"</{list_type}>")
                    in_list = False

        if in_list:
            html_lines.append(f"</{list_type}>")

        html = "\n".join(html_lines)

        # 处理内联格式
        html = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", html)
        html = re.sub(r"\*(.+?)\*", r"<em>\1</em>", html)
        html = re.sub(r"\[(.+?)\]\((.+?)\)", r'<a href="\2">\1</a>', html)

        return html

    def _to_rich_text(self, content: str) -> str:
        """转换为富文本格式（保留结构信息）"""
        # 返回带结构标记的内容
        # 实际实现可能需要返回更复杂的结构
        return content

    def _format_hashtags(
        self,
        hashtags: List[str],
        constraints: Dict[str, Any],
    ) -> str:
        """格式化话题标签"""
        prefix = constraints.get("hashtag_prefix", "#")
        suffix = constraints.get("hashtag_suffix", " ")

        formatted = []
        for tag in hashtags:
            # 移除可能已有的 # 符号
            tag = tag.strip().lstrip("#").rstrip("#")
            if tag:
                formatted.append(f"{prefix}{tag}{suffix}")

        return "".join(formatted).strip()

    def _format_mentions(self, mentions: List[str]) -> str:
        """格式化 @提及"""
        formatted = []
        for user in mentions:
            # 移除可能已有的 @ 符号
            user = user.strip().lstrip("@")
            if user:
                formatted.append(f"@{user}")

        return " ".join(formatted)

    def _format_image_layout(
        self,
        images: List[str],
        constraints: Dict[str, Any],
        output_format: OutputFormat,
    ) -> Dict[str, Any]:
        """处理图片布局"""
        max_images = constraints["max_images"]
        actual_images = images[:max_images] if max_images > 0 else images

        # 根据图片数量推荐布局
        count = len(actual_images)
        if count == 1:
            layout = "single"
        elif count == 2:
            layout = "horizontal"
        elif count == 3:
            layout = "top-one-bottom-two"
        elif count == 4:
            layout = "grid-2x2"
        elif count <= 6:
            layout = "grid-3x2"
        else:
            layout = "grid-3x3"

        # 生成图片标记
        if output_format == OutputFormat.MARKDOWN:
            image_markup = "\n".join([f"![图片{i+1}]({uri})" for i, uri in enumerate(actual_images)])
        elif output_format == OutputFormat.HTML:
            image_markup = "\n".join([f'<img src="{uri}" alt="图片{i+1}" />' for i, uri in enumerate(actual_images)])
        else:
            image_markup = "\n".join(actual_images)

        return {
            "images": actual_images,
            "count": count,
            "layout": layout,
            "markup": image_markup,
        }

    def get_schema(self) -> dict:
        """
        获取工具参数 Schema

        Returns:
            JSON Schema 定义
        """
        return {
            "type": "object",
            "properties": {
                "content": {
                    "type": "string",
                    "description": "原始内容",
                },
                "title": {
                    "type": "string",
                    "description": "标题（可选）",
                },
                "format": {
                    "type": "string",
                    "description": "输出格式",
                    "enum": ["markdown", "html", "plain_text", "rich_text"],
                    "default": "markdown",
                },
                "platform": {
                    "type": "string",
                    "description": "目标平台",
                    "enum": [
                        "xiaohongshu",
                        "douyin",
                        "weixin",
                        "weibo",
                        "bilibili",
                        "general",
                    ],
                    "default": "general",
                },
                "images": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "图片 URI 列表",
                },
                "hashtags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "话题标签列表",
                },
                "mentions": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "@提及用户列表",
                },
                "truncate": {
                    "type": "boolean",
                    "description": "是否截断超长内容",
                    "default": True,
                },
            },
            "required": ["content"],
        }
