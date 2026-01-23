"""
newsnow 热点 Provider（降级）

TrendRadar 的 README 明确其数据源之一为 newsnow。该 Provider 以“可配置 HTTP JSON 接口”方式接入，
用于在 TrendRadar 不可用或未部署时保证端到端链路可运行。
"""

from __future__ import annotations

from typing import Any, Sequence

import aiohttp

from ..models import HotTopic


class NewsNowProvider:
    """
    newsnow 热点 Provider

    Args:
        base_url: newsnow 服务地址（可以是自建或第三方兼容接口）
        endpoint_path: 热点接口路径（默认 /api/hot）
        timeout_seconds: 请求超时
    """

    def __init__(
        self,
        *,
        base_url: str,
        endpoint_path: str = "/api/hot",
        timeout_seconds: int = 30,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.endpoint_path = endpoint_path
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
        params: dict[str, Any] = {
            "industry": industry_name,
            "keywords": ",".join([k for k in keywords if k]),
            "limit": limit,
        }
        if platforms:
            params["platforms"] = ",".join([p for p in platforms if p])

        timeout = aiohttp.ClientTimeout(total=self.timeout_seconds)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url, params=params) as resp:
                resp.raise_for_status()
                data = await resp.json()

        return self._normalize_response(data)

    def _normalize_response(self, data: Any) -> list[HotTopic]:
        """
        将 newsnow 返回的任意 JSON 结构尽量归一化为 HotTopic 列表
        """

        items: list[Any] = []
        if isinstance(data, dict):
            for key in ("topics", "items", "list", "data"):
                value = data.get(key)
                if isinstance(value, list):
                    items = value
                    break
        elif isinstance(data, list):
            items = data

        results: list[HotTopic] = []
        for item in items:
            if not isinstance(item, dict):
                continue

            topic = item.get("topic") or item.get("title") or item.get("name") or ""
            if not isinstance(topic, str) or not topic.strip():
                continue

            summary = item.get("summary") or item.get("desc") or ""
            if not isinstance(summary, str):
                summary = str(summary)

            url = item.get("url") or item.get("link") or ""
            if not isinstance(url, str):
                url = str(url)

            tags = item.get("tags") or item.get("keywords") or []
            if isinstance(tags, str):
                tags = [tags]
            if not isinstance(tags, list):
                tags = []
            tags = [str(t) for t in tags if t is not None]

            results.append(
                HotTopic(
                    topic=topic.strip(),
                    heat_index=float(item.get("heat_index") or item.get("hot") or 0.0),
                    platform_heat={},
                    heat_sources=[],
                    trend={},
                    tags=tags,
                    summary=summary,
                    url=url,
                    raw=item,
                )
            )

        return results

