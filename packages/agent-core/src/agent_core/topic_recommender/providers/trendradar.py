"""
TrendRadar 热点 Provider

以“可配置 HTTP JSON 接口”方式对接 TrendRadar（或其旁路服务）。
当返回字段不完整时，尽量做宽松解析并输出统一 HotTopic。
"""

from __future__ import annotations

from typing import Any, Sequence

import aiohttp

from ..models import HotTopic


def _safe_float(value: Any) -> float:
    """
    尽量把值转换为 float

    Returns:
        float: 转换失败返回 0.0
    """

    try:
        if value is None:
            return 0.0
        return float(value)
    except Exception:
        return 0.0


class TrendRadarProvider:
    """
    TrendRadar 热点 Provider

    Args:
        base_url: TrendRadar 服务地址（例如 http://localhost:8080）
        endpoint_path: 热点接口路径（默认 /api/hot-topics）
        api_key: 可选的鉴权 key（如 TrendRadar 部署启用鉴权）
        timeout_seconds: 请求超时
    """

    def __init__(
        self,
        *,
        base_url: str,
        endpoint_path: str = "/api/hot-topics",
        payload_mode: str = "trendradar",
        api_key: str = "",
        timeout_seconds: int = 30,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.endpoint_path = endpoint_path
        self.payload_mode = payload_mode
        self.api_key = api_key
        self.timeout_seconds = timeout_seconds

    async def fetch(
        self,
        *,
        industry_name: str,
        keywords: Sequence[str],
        platforms: Sequence[str] | None = None,
        limit: int = 50,
    ) -> list[HotTopic]:
        """
        拉取热点并归一化

        Returns:
            list[HotTopic]: 归一化热点列表
        """

        url = f"{self.base_url}{self.endpoint_path}"
        headers: dict[str, str] = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        payload: dict[str, Any] = {
            "industry": industry_name,
            "keywords": list(keywords),
            "platforms": list(platforms) if platforms else None,
            "limit": limit,
        }
        if self.payload_mode == "bettafish_compat":
            payload = {
                "platform": "all",
                "category": industry_name,
                "keywords": list(keywords),
                "limit": limit,
            }

        timeout = aiohttp.ClientTimeout(total=self.timeout_seconds)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(url, json=payload, headers=headers) as resp:
                resp.raise_for_status()
                data = await resp.json()

        return self._normalize_response(data)

    def _normalize_response(self, data: Any) -> list[HotTopic]:
        """
        将 TrendRadar 返回的任意 JSON 结构尽量归一化为 HotTopic 列表

        兼容常见字段命名：
        - topics/items/list
        - topic/title/name
        - heat_score/hot_value/score
        - tags/keywords
        - platforms/platform_heat/heat_sources
        - trend/trend_points
        """

        items: list[Any] = []
        if isinstance(data, dict):
            for key in ("topics", "items", "list", "data"):
                value = data.get(key)
                if isinstance(value, list):
                    items = value
                    break
            if not items and isinstance(data.get("result"), list):
                items = data["result"]
        elif isinstance(data, list):
            items = data

        results: list[HotTopic] = []
        for item in items:
            if not isinstance(item, dict):
                continue

            topic = (
                item.get("topic")
                or item.get("title")
                or item.get("name")
                or ""
            )
            if not isinstance(topic, str) or not topic.strip():
                continue

            heat_index = float(
                item.get("heat_index")
                or item.get("heat_score")
                or item.get("hot_value")
                or item.get("score")
                or 0.0
            )

            platform_heat = item.get("platform_heat") or item.get("platforms") or {}
            if not isinstance(platform_heat, dict):
                platform_heat = {}

            heat_sources = item.get("heat_sources") or item.get("heat_source") or []
            if not isinstance(heat_sources, list):
                heat_sources = [heat_sources]

            trend = item.get("trend") or item.get("trend_points") or {}
            if not isinstance(trend, dict):
                trend = {"raw": trend}

            tags = item.get("tags") or item.get("keywords") or []
            if isinstance(tags, str):
                tags = [tags]
            if not isinstance(tags, list):
                tags = []
            tags = [str(t) for t in tags if t is not None]

            summary = (
                item.get("summary")
                or item.get("insight")
                or item.get("description")
                or ""
            )
            if not isinstance(summary, str):
                summary = str(summary)

            url = item.get("url") or item.get("link") or ""
            if not isinstance(url, str):
                url = str(url)

            results.append(
                HotTopic(
                    topic=topic.strip(),
                    heat_index=heat_index,
                    platform_heat={str(k): _safe_float(v) for k, v in platform_heat.items()},
                    heat_sources=heat_sources,
                    trend=trend,
                    tags=tags,
                    summary=summary,
                    url=url,
                    raw=item,
                )
            )

        return results
