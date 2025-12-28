"""
内容验证工具 - 检查内容是否符合平台规范
@author Ysf
"""

import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
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


class ValidationLevel(str, Enum):
    """验证级别"""

    ERROR = "error"  # 必须修复
    WARNING = "warning"  # 建议修复
    INFO = "info"  # 提示信息


class Platform(str, Enum):
    """目标平台"""

    XIAOHONGSHU = "xiaohongshu"
    DOUYIN = "douyin"
    WEIXIN = "weixin"
    WEIBO = "weibo"
    BILIBILI = "bilibili"
    GENERAL = "general"


@dataclass
class ValidationIssue:
    """验证问题"""

    level: ValidationLevel
    code: str
    message: str
    field: str = ""
    position: Optional[int] = None
    suggestion: Optional[str] = None


class ContentValidatorTool(ToolInterface):
    """
    内容验证工具

    检查内容是否符合平台规范，包括：
    - 敏感词检测
    - 字数限制检查
    - 格式规范验证
    - 违禁内容检测
    - 广告法合规检查
    """

    metadata = ToolMetadata(
        name="content_validator",
        description="验证内容是否符合平台规范",
        capabilities=[ToolCapability.CONTENT_VALIDATION],
        supported_runtimes=[RuntimeType.LOCAL, RuntimeType.CLOUD],
    )

    # 平台内容约束
    PLATFORM_CONSTRAINTS = {
        Platform.XIAOHONGSHU: {
            "max_title_length": 20,
            "max_content_length": 1000,
            "max_images": 9,
            "min_content_length": 10,
        },
        Platform.DOUYIN: {
            "max_title_length": 55,
            "max_content_length": 300,
            "max_images": 0,
            "min_content_length": 5,
        },
        Platform.WEIXIN: {
            "max_title_length": 64,
            "max_content_length": 20000,
            "max_images": 20,
            "min_content_length": 50,
        },
        Platform.WEIBO: {
            "max_title_length": 0,
            "max_content_length": 2000,
            "max_images": 9,
            "min_content_length": 1,
        },
        Platform.BILIBILI: {
            "max_title_length": 80,
            "max_content_length": 2000,
            "max_images": 10,
            "min_content_length": 10,
        },
        Platform.GENERAL: {
            "max_title_length": 100,
            "max_content_length": 50000,
            "max_images": 100,
            "min_content_length": 1,
        },
    }

    # 敏感词库（示例，实际应用需要更完整的词库）
    SENSITIVE_WORDS = {
        "political": [
            # 政治敏感词（简化示例）
        ],
        "violence": [
            "暴力",
            "血腥",
            "杀人",
        ],
        "adult": [
            # 成人内容敏感词
        ],
        "gambling": [
            "赌博",
            "博彩",
            "彩票",
        ],
        "fraud": [
            "诈骗",
            "骗局",
        ],
    }

    # 广告法违禁词
    AD_LAW_FORBIDDEN_WORDS = [
        "最佳",
        "最好",
        "最高级",
        "最优",
        "第一",
        "顶级",
        "极品",
        "绝对",
        "万能",
        "100%",
        "百分百",
        "纯天然",
        "无副作用",
        "包治百病",
        "立竿见影",
        "药到病除",
        "秒杀",
        "史无前例",
        "独一无二",
        "全网最低",
    ]

    def __init__(self):
        """初始化工具"""
        pass

    async def execute(self, ctx: RuntimeContext, **kwargs) -> ToolResult:
        """
        执行内容验证

        Args:
            ctx: 运行时上下文
            **kwargs: 工具参数
                - content (str): 待验证内容
                - title (str, optional): 标题
                - platform (str, optional): 目标平台
                - images (List[str], optional): 图片列表
                - rules (List[str], optional): 要执行的验证规则
                  可选值: length, sensitive, ad_law, format, link, all

        Returns:
            ToolResult: 验证结果

        Raises:
            ToolExecutionError: 执行失败
        """
        try:
            # 提取参数
            content = kwargs.get("content")
            if not content:
                raise ToolExecutionError("缺少必填参数: content")

            title = kwargs.get("title", "")
            platform = Platform(kwargs.get("platform", Platform.GENERAL.value))
            images = kwargs.get("images", [])
            rules = kwargs.get("rules", ["all"])

            if "all" in rules:
                rules = ["length", "sensitive", "ad_law", "format", "link"]

            # 获取平台约束
            constraints = self.PLATFORM_CONSTRAINTS[platform]

            # 收集验证问题
            issues: List[ValidationIssue] = []

            # 执行各项验证
            if "length" in rules:
                issues.extend(
                    self._validate_length(title, content, images, constraints)
                )

            if "sensitive" in rules:
                issues.extend(self._validate_sensitive_words(content, title))

            if "ad_law" in rules:
                issues.extend(self._validate_ad_law(content, title))

            if "format" in rules:
                issues.extend(self._validate_format(content))

            if "link" in rules:
                issues.extend(self._validate_links(content))

            # 统计问题
            error_count = sum(1 for i in issues if i.level == ValidationLevel.ERROR)
            warning_count = sum(
                1 for i in issues if i.level == ValidationLevel.WARNING
            )
            info_count = sum(1 for i in issues if i.level == ValidationLevel.INFO)

            # 判断是否通过
            is_valid = error_count == 0

            return ToolResult(
                success=True,
                data={
                    "is_valid": is_valid,
                    "issues": [
                        {
                            "level": issue.level.value,
                            "code": issue.code,
                            "message": issue.message,
                            "field": issue.field,
                            "position": issue.position,
                            "suggestion": issue.suggestion,
                        }
                        for issue in issues
                    ],
                    "summary": {
                        "error_count": error_count,
                        "warning_count": warning_count,
                        "info_count": info_count,
                        "total_count": len(issues),
                    },
                    "content_stats": {
                        "title_length": len(title),
                        "content_length": len(content),
                        "image_count": len(images),
                    },
                },
                metadata={
                    "platform": platform.value,
                    "rules_applied": rules,
                    "constraints": constraints,
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
                error=f"内容验证失败: {e}",
            )

    def _validate_length(
        self,
        title: str,
        content: str,
        images: List[str],
        constraints: Dict[str, Any],
    ) -> List[ValidationIssue]:
        """验证长度限制"""
        issues = []

        # 标题长度
        max_title = constraints["max_title_length"]
        if max_title > 0 and len(title) > max_title:
            issues.append(
                ValidationIssue(
                    level=ValidationLevel.ERROR,
                    code="TITLE_TOO_LONG",
                    message=f"标题过长 ({len(title)}/{max_title})",
                    field="title",
                    suggestion=f"请将标题缩短至 {max_title} 字以内",
                )
            )

        # 内容长度
        max_content = constraints["max_content_length"]
        min_content = constraints.get("min_content_length", 1)

        if len(content) > max_content:
            issues.append(
                ValidationIssue(
                    level=ValidationLevel.ERROR,
                    code="CONTENT_TOO_LONG",
                    message=f"内容过长 ({len(content)}/{max_content})",
                    field="content",
                    suggestion=f"请将内容缩短至 {max_content} 字以内",
                )
            )

        if len(content) < min_content:
            issues.append(
                ValidationIssue(
                    level=ValidationLevel.ERROR,
                    code="CONTENT_TOO_SHORT",
                    message=f"内容过短 ({len(content)}/{min_content})",
                    field="content",
                    suggestion=f"请将内容扩充至 {min_content} 字以上",
                )
            )

        # 图片数量
        max_images = constraints["max_images"]
        if max_images > 0 and len(images) > max_images:
            issues.append(
                ValidationIssue(
                    level=ValidationLevel.ERROR,
                    code="TOO_MANY_IMAGES",
                    message=f"图片过多 ({len(images)}/{max_images})",
                    field="images",
                    suggestion=f"请减少图片至 {max_images} 张以内",
                )
            )

        return issues

    def _validate_sensitive_words(
        self, content: str, title: str
    ) -> List[ValidationIssue]:
        """验证敏感词"""
        issues = []
        full_text = f"{title} {content}"

        for category, words in self.SENSITIVE_WORDS.items():
            for word in words:
                if word in full_text:
                    # 找到位置
                    pos = full_text.find(word)
                    field = "title" if pos < len(title) else "content"

                    issues.append(
                        ValidationIssue(
                            level=ValidationLevel.ERROR,
                            code=f"SENSITIVE_WORD_{category.upper()}",
                            message=f"检测到敏感词: {word}",
                            field=field,
                            position=pos,
                            suggestion=f"请移除或替换敏感词 '{word}'",
                        )
                    )

        return issues

    def _validate_ad_law(self, content: str, title: str) -> List[ValidationIssue]:
        """验证广告法合规"""
        issues = []
        full_text = f"{title} {content}"

        for word in self.AD_LAW_FORBIDDEN_WORDS:
            if word in full_text:
                pos = full_text.find(word)
                field = "title" if pos < len(title) else "content"

                issues.append(
                    ValidationIssue(
                        level=ValidationLevel.WARNING,
                        code="AD_LAW_VIOLATION",
                        message=f"可能违反广告法: {word}",
                        field=field,
                        position=pos,
                        suggestion=f"'{word}' 可能违反广告法，建议使用更温和的表述",
                    )
                )

        return issues

    def _validate_format(self, content: str) -> List[ValidationIssue]:
        """验证格式规范"""
        issues = []

        # 检查过多的连续换行
        if "\n\n\n" in content:
            issues.append(
                ValidationIssue(
                    level=ValidationLevel.WARNING,
                    code="EXCESSIVE_NEWLINES",
                    message="内容中有过多的连续换行",
                    field="content",
                    suggestion="建议减少连续空行，保持内容紧凑",
                )
            )

        # 检查过多的标点符号
        punct_pattern = r"[!！?？]{3,}"
        if re.search(punct_pattern, content):
            issues.append(
                ValidationIssue(
                    level=ValidationLevel.WARNING,
                    code="EXCESSIVE_PUNCTUATION",
                    message="内容中有过多的重复标点符号",
                    field="content",
                    suggestion="建议减少重复的感叹号或问号",
                )
            )

        # 检查全大写英文（可能是垃圾内容）
        if re.search(r"[A-Z]{10,}", content):
            issues.append(
                ValidationIssue(
                    level=ValidationLevel.INFO,
                    code="EXCESSIVE_CAPS",
                    message="内容中有过长的全大写英文",
                    field="content",
                    suggestion="全大写文字可能影响阅读体验",
                )
            )

        # 检查特殊字符滥用
        special_chars = r"[@#$%^&*()_+=\[\]{}|\\:\";<>,./~`]{5,}"
        if re.search(special_chars, content):
            issues.append(
                ValidationIssue(
                    level=ValidationLevel.WARNING,
                    code="EXCESSIVE_SPECIAL_CHARS",
                    message="内容中有过多的特殊字符",
                    field="content",
                    suggestion="过多特殊字符可能影响阅读或被平台过滤",
                )
            )

        return issues

    def _validate_links(self, content: str) -> List[ValidationIssue]:
        """验证链接规范"""
        issues = []

        # 查找所有链接
        url_pattern = r"https?://[^\s<>\"']+|www\.[^\s<>\"']+"
        urls = re.findall(url_pattern, content)

        if urls:
            issues.append(
                ValidationIssue(
                    level=ValidationLevel.WARNING,
                    code="CONTAINS_EXTERNAL_LINKS",
                    message=f"内容中包含 {len(urls)} 个外部链接",
                    field="content",
                    suggestion="部分平台可能限制外部链接，请确认平台政策",
                )
            )

        # 检查是否包含短链接服务
        short_url_services = ["bit.ly", "t.co", "goo.gl", "tinyurl", "dwz.cn"]
        for url in urls:
            for service in short_url_services:
                if service in url.lower():
                    issues.append(
                        ValidationIssue(
                            level=ValidationLevel.WARNING,
                            code="SHORT_URL_DETECTED",
                            message=f"检测到短链接: {url}",
                            field="content",
                            suggestion="短链接可能被平台过滤，建议使用原始链接",
                        )
                    )
                    break

        return issues

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
                    "description": "待验证内容",
                },
                "title": {
                    "type": "string",
                    "description": "标题（可选）",
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
                    "description": "图片列表",
                },
                "rules": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "enum": ["length", "sensitive", "ad_law", "format", "link", "all"],
                    },
                    "description": "要执行的验证规则",
                    "default": ["all"],
                },
            },
            "required": ["content"],
        }
