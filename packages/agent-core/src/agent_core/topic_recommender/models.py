"""
选题推荐领域模型

约束：TopicCard 字段需要与 cloud-backend 的 sys_topic 表字段对齐，且保证全字段可落库。
"""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


class HotTopic(BaseModel):
    """
    归一化热点条目

    Provider 负责把外部数据源（TrendRadar/newsnow 等）的输出统一为该结构，供 LLM 分析与选题生成使用。
    """

    topic: str
    heat_index: float = 0.0
    platform_heat: dict[str, float] = Field(default_factory=dict)
    heat_sources: list[Any] = Field(default_factory=list)
    trend: dict[str, Any] = Field(default_factory=dict)
    tags: list[str] = Field(default_factory=list)
    summary: str = ""
    url: str = ""
    raw: dict[str, Any] = Field(default_factory=dict)


class TopicCard(BaseModel):
    """
    选题卡片（全字段落库口径）

    字段对齐 cloud-backend: backend/app/topic/model/topic.py 中的 sys_topic 表。
    """

    title: str
    potential_score: float = 0.0
    heat_index: float = 0.0
    reason: str = ""

    keywords: list[str] = Field(default_factory=list)
    platform_heat: dict[str, Any] = Field(default_factory=dict)
    heat_sources: list[Any] = Field(default_factory=list)
    trend: dict[str, Any] = Field(default_factory=dict)

    industry_tags: list[str] = Field(default_factory=list)
    target_audience: list[str] | dict[str, Any] = Field(default_factory=list)
    creative_angles: list[str] = Field(default_factory=list)
    content_outline: list[str] | dict[str, Any] = Field(default_factory=list)
    format_suggestions: list[str] = Field(default_factory=list)
    material_clues: list[str] | dict[str, Any] = Field(default_factory=list)
    risk_notes: list[str] = Field(default_factory=list)

    source_info: dict[str, Any] = Field(default_factory=dict)

    batch_date: Optional[str] = None
    source_uid: Optional[str] = None

    def ensure_defaults(self) -> "TopicCard":
        """
        确保所有字段可落库（无 None），并对空值进行最小默认填充。

        Returns:
            TopicCard: self
        """

        if self.reason is None:
            self.reason = ""

        if self.keywords is None:
            self.keywords = []

        if self.platform_heat is None:
            self.platform_heat = {}

        if self.heat_sources is None:
            self.heat_sources = []

        if self.trend is None:
            self.trend = {}

        if self.industry_tags is None:
            self.industry_tags = []

        if self.target_audience is None:
            self.target_audience = []

        if self.creative_angles is None:
            self.creative_angles = []

        if self.content_outline is None:
            self.content_outline = []

        if self.format_suggestions is None:
            self.format_suggestions = []

        if self.material_clues is None:
            self.material_clues = []

        if self.risk_notes is None:
            self.risk_notes = []

        if self.source_info is None:
            self.source_info = {}

        return self

