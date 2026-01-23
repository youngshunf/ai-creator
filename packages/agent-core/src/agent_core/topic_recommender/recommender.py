"""
选题推荐引擎

将“热点聚合”与“LLM 结构化生成”解耦为 Provider 与 Analyzer，便于端云复用。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, Sequence

from .models import HotTopic, TopicCard


class HotTopicProvider(Protocol):
    """
    热点数据源抽象

    负责把 TrendRadar/newsnow 等外部数据转为统一的 HotTopic 列表。
    """

    async def fetch(
        self,
        *,
        industry_name: str,
        keywords: Sequence[str],
        platforms: Sequence[str] | None = None,
        limit: int = 50,
    ) -> list[HotTopic]:
        """
        获取热点条目列表

        Args:
            industry_name: 行业名称
            keywords: 关键词列表
            platforms: 平台过滤（可选）
            limit: 最大条数

        Returns:
            list[HotTopic]: 归一化热点列表
        """


class TopicAnalyzer(Protocol):
    """
    选题分析器抽象

    负责调用 LLM 网关并输出可落库的 TopicCard 列表。
    """

    async def analyze(
        self,
        *,
        industry_name: str,
        keywords: Sequence[str],
        hot_topics: Sequence[HotTopic],
        count: int = 10,
    ) -> list[TopicCard]:
        """
        生成选题卡片列表

        Args:
            industry_name: 行业名称
            keywords: 关键词列表
            hot_topics: 热点输入
            count: 生成数量

        Returns:
            list[TopicCard]: 全字段选题卡片
        """


@dataclass
class TopicRecommender:
    """
    选题推荐编排器
    """

    provider: HotTopicProvider
    analyzer: TopicAnalyzer

    async def run(
        self,
        *,
        industry_name: str,
        keywords: Sequence[str],
        platforms: Sequence[str] | None = None,
        hot_limit: int = 50,
        count: int = 10,
    ) -> list[TopicCard]:
        """
        执行一次选题推荐

        Args:
            industry_name: 行业名称
            keywords: 行业关键词
            platforms: 平台过滤（可选）
            hot_limit: 输入热点条数
            count: 输出选题数量

        Returns:
            list[TopicCard]: 全字段可落库选题卡片
        """

        normalized_keywords = [k.strip() for k in keywords if k and k.strip()]
        hot_topics = await self.provider.fetch(
            industry_name=industry_name,
            keywords=normalized_keywords,
            platforms=platforms,
            limit=hot_limit,
        )

        cards = await self.analyzer.analyze(
            industry_name=industry_name,
            keywords=normalized_keywords,
            hot_topics=hot_topics,
            count=count,
        )

        return [c.ensure_defaults() for c in cards]

