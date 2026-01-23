from agent_core.topic_recommender.providers.trendradar import TrendRadarProvider


def test_trendradar_normalize_response_basic():
    provider = TrendRadarProvider(base_url="http://example.com")
    data = {
        "topics": [
            {
                "topic": "测试热点",
                "heat_score": 88,
                "platforms": {"weibo": 90, "zhihu": 70},
                "tags": ["A", "B"],
                "insight": "讨论热度上升",
                "trend": {"direction": "up"},
                "heat_sources": [{"platform": "weibo", "score": 90}],
                "url": "https://example.com/a",
            }
        ]
    }

    topics = provider._normalize_response(data)
    assert len(topics) == 1
    assert topics[0].topic == "测试热点"
    assert topics[0].heat_index == 88.0
    assert topics[0].platform_heat["weibo"] == 90.0
    assert topics[0].trend["direction"] == "up"

