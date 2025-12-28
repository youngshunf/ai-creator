"""
热点发现工具 - 获取热点话题和趋势分析
@author Ysf
"""

from typing import List, Dict, Any, Optional
from enum import Enum
from datetime import datetime

from ..base import (
    ToolInterface,
    ToolMetadata,
    ToolResult,
    ToolCapability,
    ToolExecutionError,
)
from ...runtime.interfaces import RuntimeType
from ...runtime.context import RuntimeContext


class Platform(str, Enum):
    """热点来源平台"""

    WEIBO = "weibo"
    DOUYIN = "douyin"
    XIAOHONGSHU = "xiaohongshu"
    BILIBILI = "bilibili"
    ZHIHU = "zhihu"
    BAIDU = "baidu"
    TOUTIAO = "toutiao"
    ALL = "all"


class Category(str, Enum):
    """话题类别"""

    ALL = "all"
    ENTERTAINMENT = "entertainment"  # 娱乐
    TECH = "tech"  # 科技
    FINANCE = "finance"  # 财经
    SPORTS = "sports"  # 体育
    SOCIAL = "social"  # 社会
    FASHION = "fashion"  # 时尚
    FOOD = "food"  # 美食
    TRAVEL = "travel"  # 旅行
    EDUCATION = "education"  # 教育
    HEALTH = "health"  # 健康


class HotTopicTool(ToolInterface):
    """
    热点发现工具

    获取各平台热点话题，分析内容传播趋势。
    支持集成 BettaFish 舆情分析 API。

    功能：
    - 获取多平台热点话题
    - 分析话题热度趋势
    - 推荐相关创作主题
    """

    metadata = ToolMetadata(
        name="hot_topic",
        description="获取热点话题和趋势分析",
        capabilities=[ToolCapability.HOT_TOPIC_DISCOVERY],
        supported_runtimes=[RuntimeType.LOCAL, RuntimeType.CLOUD],
    )

    # 模拟热点数据源（实际应用需要对接真实 API）
    # 这里提供一个结构示例
    MOCK_HOT_TOPICS = {
        Platform.WEIBO: [
            {
                "rank": 1,
                "title": "AI技术创新",
                "hot_value": 9876543,
                "category": Category.TECH.value,
                "trend": "rising",
                "tags": ["科技", "AI", "创新"],
            },
            {
                "rank": 2,
                "title": "年度热门电影",
                "hot_value": 8765432,
                "category": Category.ENTERTAINMENT.value,
                "trend": "stable",
                "tags": ["电影", "娱乐"],
            },
        ],
        Platform.DOUYIN: [
            {
                "rank": 1,
                "title": "美食探店",
                "hot_value": 5432109,
                "category": Category.FOOD.value,
                "trend": "rising",
                "tags": ["美食", "探店"],
            },
        ],
    }

    def __init__(self):
        """初始化工具"""
        pass

    async def execute(self, ctx: RuntimeContext, **kwargs) -> ToolResult:
        """
        执行热点发现

        Args:
            ctx: 运行时上下文
            **kwargs: 工具参数
                - platform (str, optional): 目标平台 (weibo/douyin/xiaohongshu/...)
                - category (str, optional): 话题类别
                - limit (int, optional): 返回数量，默认 10
                - include_analysis (bool, optional): 是否包含趋势分析
                - keyword (str, optional): 关键词过滤

        Returns:
            ToolResult: 热点话题列表

        Raises:
            ToolExecutionError: 执行失败
        """
        try:
            # 提取参数
            platform = Platform(kwargs.get("platform", Platform.ALL.value))
            category = Category(kwargs.get("category", Category.ALL.value))
            limit = min(kwargs.get("limit", 10), 50)
            include_analysis = kwargs.get("include_analysis", False)
            keyword = kwargs.get("keyword", "")

            # 尝试使用 BettaFish API
            bettafish_api_key = ctx.get_api_key("bettafish")
            if bettafish_api_key:
                return await self._fetch_from_bettafish(
                    ctx,
                    bettafish_api_key,
                    platform,
                    category,
                    limit,
                    include_analysis,
                    keyword,
                )

            # 回退到模拟数据或其他数据源
            return await self._fetch_mock_data(
                platform, category, limit, include_analysis, keyword
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
                error=f"热点发现失败: {e}",
            )

    async def _fetch_from_bettafish(
        self,
        ctx: RuntimeContext,
        api_key: str,
        platform: Platform,
        category: Category,
        limit: int,
        include_analysis: bool,
        keyword: str,
    ) -> ToolResult:
        """从 BettaFish API 获取热点"""
        try:
            import aiohttp
        except ImportError:
            return ToolResult(
                success=False,
                data=None,
                error="未安装 aiohttp 库，请运行: pip install aiohttp",
            )

        # BettaFish API 配置
        bettafish_config = ctx.extra.get("bettafish", {})
        base_url = bettafish_config.get(
            "base_url", "https://api.bettafish.ai/v1"
        )

        # 构建请求
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        params = {
            "limit": limit,
        }

        if platform != Platform.ALL:
            params["platform"] = platform.value
        if category != Category.ALL:
            params["category"] = category.value
        if keyword:
            params["keyword"] = keyword

        try:
            async with aiohttp.ClientSession() as session:
                # 获取热点列表
                async with session.get(
                    f"{base_url}/hot-topics",
                    headers=headers,
                    params=params,
                ) as resp:
                    if resp.status != 200:
                        error_text = await resp.text()
                        raise ToolExecutionError(
                            f"BettaFish API 错误: {resp.status} - {error_text}"
                        )

                    data = await resp.json()
                    topics = data.get("topics", [])

                # 获取趋势分析（如果需要）
                analysis = None
                if include_analysis and topics:
                    analysis = await self._fetch_trend_analysis(
                        session, base_url, headers, topics[:5]
                    )

            return ToolResult(
                success=True,
                data={
                    "topics": topics,
                    "total": len(topics),
                    "platform": platform.value,
                    "category": category.value,
                    "analysis": analysis,
                    "timestamp": datetime.now().isoformat(),
                },
                metadata={
                    "source": "bettafish",
                    "include_analysis": include_analysis,
                },
            )

        except aiohttp.ClientError as e:
            raise ToolExecutionError(f"网络请求失败: {e}")

    async def _fetch_trend_analysis(
        self,
        session,
        base_url: str,
        headers: Dict[str, str],
        topics: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """获取趋势分析"""
        topic_ids = [t.get("id") for t in topics if t.get("id")]

        if not topic_ids:
            return None

        try:
            async with session.post(
                f"{base_url}/trend-analysis",
                headers=headers,
                json={"topic_ids": topic_ids},
            ) as resp:
                if resp.status == 200:
                    return await resp.json()
        except Exception:
            pass

        return None

    async def _fetch_mock_data(
        self,
        platform: Platform,
        category: Category,
        limit: int,
        include_analysis: bool,
        keyword: str,
    ) -> ToolResult:
        """获取模拟数据（用于演示和测试）"""
        topics = []

        # 收集指定平台的热点
        if platform == Platform.ALL:
            for p, items in self.MOCK_HOT_TOPICS.items():
                topics.extend(items)
        else:
            topics = self.MOCK_HOT_TOPICS.get(platform, [])

        # 按类别过滤
        if category != Category.ALL:
            topics = [t for t in topics if t.get("category") == category.value]

        # 按关键词过滤
        if keyword:
            topics = [
                t
                for t in topics
                if keyword.lower() in t.get("title", "").lower()
                or any(keyword.lower() in tag.lower() for tag in t.get("tags", []))
            ]

        # 按热度排序
        topics.sort(key=lambda x: x.get("hot_value", 0), reverse=True)

        # 限制数量
        topics = topics[:limit]

        # 添加分析数据（模拟）
        analysis = None
        if include_analysis and topics:
            analysis = {
                "trending_categories": self._analyze_categories(topics),
                "peak_hours": ["10:00", "14:00", "20:00"],
                "content_suggestions": self._generate_suggestions(topics),
            }

        return ToolResult(
            success=True,
            data={
                "topics": topics,
                "total": len(topics),
                "platform": platform.value,
                "category": category.value,
                "analysis": analysis,
                "timestamp": datetime.now().isoformat(),
            },
            metadata={
                "source": "mock",
                "include_analysis": include_analysis,
                "note": "使用模拟数据，生产环境请配置 BettaFish API",
            },
        )

    def _analyze_categories(
        self, topics: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """分析类别分布"""
        category_count: Dict[str, int] = {}
        for topic in topics:
            cat = topic.get("category", "other")
            category_count[cat] = category_count.get(cat, 0) + 1

        return [
            {"category": cat, "count": count, "percentage": count / len(topics) * 100}
            for cat, count in sorted(
                category_count.items(), key=lambda x: x[1], reverse=True
            )
        ]

    def _generate_suggestions(
        self, topics: List[Dict[str, Any]]
    ) -> List[Dict[str, str]]:
        """生成创作建议"""
        suggestions = []

        for topic in topics[:3]:
            title = topic.get("title", "")
            tags = topic.get("tags", [])
            trend = topic.get("trend", "stable")

            if trend == "rising":
                priority = "高"
                reason = "话题热度上升中，建议尽快创作"
            elif trend == "stable":
                priority = "中"
                reason = "话题热度稳定，可持续关注"
            else:
                priority = "低"
                reason = "话题热度下降，需谨慎选题"

            suggestions.append({
                "topic": title,
                "priority": priority,
                "reason": reason,
                "suggested_tags": tags[:5] if tags else [],
            })

        return suggestions

    def get_schema(self) -> dict:
        """
        获取工具参数 Schema

        Returns:
            JSON Schema 定义
        """
        return {
            "type": "object",
            "properties": {
                "platform": {
                    "type": "string",
                    "description": "目标平台",
                    "enum": [
                        "weibo",
                        "douyin",
                        "xiaohongshu",
                        "bilibili",
                        "zhihu",
                        "baidu",
                        "toutiao",
                        "all",
                    ],
                    "default": "all",
                },
                "category": {
                    "type": "string",
                    "description": "话题类别",
                    "enum": [
                        "all",
                        "entertainment",
                        "tech",
                        "finance",
                        "sports",
                        "social",
                        "fashion",
                        "food",
                        "travel",
                        "education",
                        "health",
                    ],
                    "default": "all",
                },
                "limit": {
                    "type": "integer",
                    "description": "返回数量",
                    "default": 10,
                    "minimum": 1,
                    "maximum": 50,
                },
                "include_analysis": {
                    "type": "boolean",
                    "description": "是否包含趋势分析",
                    "default": False,
                },
                "keyword": {
                    "type": "string",
                    "description": "关键词过滤",
                },
            },
        }
