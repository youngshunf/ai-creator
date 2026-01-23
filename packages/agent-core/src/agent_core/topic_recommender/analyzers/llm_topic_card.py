"""
基于 LLM 网关的选题卡片生成器

输出约束：
- 必须返回可 JSON 解析的对象：{"topics": [TopicCard, ...]}
- 每个 TopicCard 必须包含 sys_topic 全量字段（缺失字段由 ensure_defaults() 补齐）
"""

from __future__ import annotations

import json
import re
from typing import Any, Sequence

from pydantic import ValidationError

from ...llm.interface import LLMClientInterface, LLMMessage
from ..models import HotTopic, TopicCard


_JSON_BLOCK_RE = re.compile(r"\{[\s\S]*\}", re.MULTILINE)


def _extract_json_object(text: str) -> str:
    """
    从文本中提取第一个 JSON 对象片段（容错用）

    Args:
        text: LLM 原始输出

    Returns:
        str: JSON 对象字符串

    Raises:
        ValueError: 无法提取 JSON
    """

    match = _JSON_BLOCK_RE.search(text)
    if not match:
        raise ValueError("无法从输出中提取 JSON 对象")
    return match.group(0)


class LLMTopicCardAnalyzer:
    """
    使用 LLMClientInterface 生成 TopicCard 列表
    """

    def __init__(
        self,
        *,
        client: LLMClientInterface,
        model: str | None = None,
        max_tokens: int = 3000,
        temperature: float = 0.4,
        user_id: str | None = None,
    ) -> None:
        self.client = client
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.user_id = user_id

    async def analyze(
        self,
        *,
        industry_name: str,
        keywords: Sequence[str],
        hot_topics: Sequence[HotTopic],
        count: int = 10,
    ) -> list[TopicCard]:
        """
        基于热点生成选题卡片

        Args:
            industry_name: 行业名称
            keywords: 关键词列表
            hot_topics: 热点输入
            count: 生成数量

        Returns:
            list[TopicCard]: 全字段选题卡片列表
        """

        hot_payload = [
            {
                "topic": ht.topic,
                "heat_index": ht.heat_index,
                "platform_heat": ht.platform_heat,
                "heat_sources": ht.heat_sources,
                "trend": ht.trend,
                "tags": ht.tags,
                "summary": ht.summary,
                "url": ht.url,
            }
            for ht in hot_topics
        ]

        system = (
            "你是资深内容策划与舆情分析专家。"
            "你必须严格按要求输出可解析 JSON，不要输出任何解释文字。"
        )

        prompt = f"""
请基于下面的行业与关键词，以及跨平台热点列表，生成 {count} 个“可直接入库”的选题卡片。\n
行业：{industry_name}\n
关键词：{json.dumps(list(keywords), ensure_ascii=False)}\n
热点列表（JSON）：{json.dumps(hot_payload, ensure_ascii=False)}\n
输出要求（必须严格遵守）：\n
1) 只输出一个 JSON 对象，不要包含 Markdown 代码块标记。\n
2) JSON 格式必须为：{{\"topics\": [ ... ]}}。\n
3) topics 中每一项必须包含以下全部字段（全部必填，不能为空则给空结构）：\n
- title: string\n
- potential_score: number (0-100)\n
- heat_index: number (0-100)\n
- reason: string\n
- keywords: string[]\n
- platform_heat: object\n
- heat_sources: array\n
- trend: object\n
- industry_tags: string[]\n
- target_audience: string[] 或 object\n
- creative_angles: string[]\n
- content_outline: string[] 或 object\n
- format_suggestions: string[]\n
- material_clues: string[] 或 object\n
- risk_notes: string[]\n
- source_info: object\n
4) source_info 必须包含：输入关键词、引用的热点 topic 列表（可截断）、以及你的趋势/情绪判断依据摘要。\n
"""

        response = await self.client.chat(
            [
                LLMMessage(role="user", content=prompt),
            ],
            model=self.model,
            system=system,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            user_id=self.user_id,
        )

        raw_text = response.content.strip()

        parsed: Any
        try:
            parsed = json.loads(raw_text)
        except Exception:
            parsed = json.loads(_extract_json_object(raw_text))

        topics_obj = parsed.get("topics") if isinstance(parsed, dict) else None
        if not isinstance(topics_obj, list):
            raise ValueError("LLM 输出 JSON 缺少 topics 数组")

        cards: list[TopicCard] = []
        for item in topics_obj:
            if not isinstance(item, dict):
                continue
            try:
                card = TopicCard.model_validate(item).ensure_defaults()
            except ValidationError:
                continue
            if not card.title.strip():
                continue
            cards.append(card)

        return cards

