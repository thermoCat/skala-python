"""
데이터 수집 미니 파이프라인 진입점

[프로그램 설명]
Open-Meteo(서울 3일 시간대별 기온·강수확률), countries.dev(한국 국가 정보),
ip-api(IP 기반 지역 정보) 3개 API를 asyncio.gather()로 동시에 수집한 뒤
Pydantic v2로 스키마를 검증하고, CSV/Parquet 두 형식으로 저장하며
읽기/쓰기 성능을 비교한다.
"""
import asyncio
import logging
import sys

import httpx
from pydantic import ValidationError

from .collector import collect_all
from .schemas import parse_country, parse_ip, parse_weather
from .storage import render_summary_table, save_and_benchmark

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def main() -> None:
    try:
        raw = asyncio.run(collect_all())
    except (httpx.HTTPStatusError, httpx.RequestError):
        logger.error("API 수집 단계 실패로 파이프라인을 종료합니다.")
        sys.exit(1)

    try:
        weather_records = parse_weather(raw["weather"])
        country_record = parse_country(raw["country"])
        ip_record = parse_ip(raw["ip"])
    except ValidationError:
        logger.error("스키마 검증 실패로 파이프라인을 종료합니다.")
        sys.exit(1)

    results = {
        "weather": save_and_benchmark(weather_records, "weather"),
        "country": save_and_benchmark(country_record, "country"),
        "ip": save_and_benchmark(ip_record, "ip"),
    }
    logger.info("저장/성능 비교 결과\n%s", render_summary_table(results))
    logger.info("파이프라인 실행 완료")


if __name__ == "__main__":
    main()
