import pytest

from agent_core.llm.interface import LLMResponse, LLMUsage, LLMMessage, LLMClientInterface
from agent_core.topic_recommender.analyzers.llm_topic_card import LLMTopicCardAnalyzer
from agent_core.topic_recommender.models import HotTopic


class FakeLLMClient(LLMClientInterface):
    def __init__(self, content: str):
        self._content = content

    async def chat(
        self,
        messages: list[LLMMessage],
        *,
        model: str | None = None,
        system: str | None = None,
        tools: list[dict] | None = None,
        max_tokens: int | None = None,
        temperature: float | None = None,
        user_id: str | None = None,
    ) -> LLMResponse:
        return LLMResponse(
            content=self._content,
            model=model or "fake",
            provider="fake",
            usage=LLMUsage(input_tokens=1, output_tokens=1, total_tokens=2),
        )

    async def chat_stream(
        self,
        messages: list[LLMMessage],
        *,
        model: str | None = None,
        system: str | None = None,
        max_tokens: int | None = None,
        temperature: float | None = None,
        user_id: str | None = None,
    ):
        raise NotImplementedError()

    async def get_available_models(self):
        raise NotImplementedError()

    async def get_model_by_type(self, model_type):
        raise NotImplementedError()

    async def get_models_by_type(self, model_type):
        raise NotImplementedError()

    async def get_usage_summary(self, user_id: str, period: str = "month") -> dict:
        raise NotImplementedError()

    async def health_check(self) -> bool:
        return True


@pytest.mark.asyncio
async def test_llm_analyzer_parses_json_and_fills_all_fields():
    content = """
```json
{
  "topics": [
    {
      "title": "标题A",
      "potential_score": 88,
      "heat_index": 90,
      "reason": "理由",
      "keywords": [],
      "platform_heat": {},
      "heat_sources": [],
      "trend": {},
      "industry_tags": [],
      "target_audience": [],
      "creative_angles": [],
      "content_outline": [],
      "format_suggestions": [],
      "material_clues": [],
      "risk_notes": [],
      "source_info": {}
    }
  ]
}
```
"""
    analyzer = LLMTopicCardAnalyzer(client=FakeLLMClient(content))
    hot_topics = [HotTopic(topic="x", heat_index=1)]
    cards = await analyzer.analyze(
        industry_name="测试行业",
        keywords=["k1"],
        hot_topics=hot_topics,
        count=1,
    )
    assert len(cards) == 1
    card = cards[0]
    assert card.title == "标题A"
    assert card.platform_heat is not None
    assert card.heat_sources is not None
    assert card.trend is not None
    assert card.source_info is not None

