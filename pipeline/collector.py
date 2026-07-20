"""httpx + asyncio를 사용한 비동기 API 수집기."""
import asyncio
import logging
from typing import Any

import httpx

from . import config

logger = logging.getLogger(__name__)


async def _fetch_json(client: httpx.AsyncClient, name: str, url: str) -> dict[str, Any]:
    """단일 API를 호출해 JSON 응답을 반환한다. 실패 시 로그를 남기고 예외를 전파한다."""
    try:
        response = await client.get(url, timeout=config.REQUEST_TIMEOUT)
        response.raise_for_status()
    except httpx.HTTPStatusError as e:
        logger.error("[%s] HTTP 오류 (status=%d): %s", name, e.response.status_code, url)
        raise
    except httpx.RequestError as e:
        logger.error("[%s] 요청 실패: %s", name, e)
        raise

    logger.info("[%s] 응답 수신 완료 (status=%d)", name, response.status_code)
    return response.json()


async def collect_all() -> dict[str, Any]:
    """3개 API(날씨/국가정보/IP정보)를 asyncio.gather()로 동시에 호출한다."""
    async with httpx.AsyncClient() as client:
        weather, country, ip_info = await asyncio.gather(
            _fetch_json(client, "weather", config.WEATHER_URL),
            _fetch_json(client, "country", config.COUNTRY_URL),
            _fetch_json(client, "ip", config.IP_URL),
        )
    return {"weather": weather, "country": country, "ip": ip_info}
