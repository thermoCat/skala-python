"""API 응답 검증용 Pydantic v2 모델과 raw JSON → 모델 파싱 로직."""
import logging
from datetime import datetime
from typing import Any, TypeVar

from pydantic import BaseModel, Field, ValidationError

logger = logging.getLogger(__name__)

ModelT = TypeVar("ModelT", bound=BaseModel)


class WeatherHourlyRecord(BaseModel):
    """Open-Meteo 서울 시간대별 기온·강수확률 레코드."""

    time: datetime
    # 서울 계절 범위가 아니라 지구 지표 기온 관측 극값(최고 약 56.7℃, 최저 약 -89.2℃) 기준으로 스키마 작성
    # 여유를 두고 -50~60으로 설정.
    temperature_2m: float = Field(..., ge=-50, le=60, description="섭씨 기온")
    # 확률(%)의 정의상 0~100을 벗어날 수 없음
    precipitation_probability: int = Field(..., ge=0, le=100, description="강수확률(%)")


class CountryInfo(BaseModel):
    """countries.dev 한국 국가 정보."""

    model_config = {"populate_by_name": True}

    name: str
    capital: str
    region: str
    subregion: str
    # 국가로 존재하는 이상 인구는 항상 1명 이상
    population: int = Field(..., gt=0)
    # 국토 면적도 물리적으로 항상 양수
    area: float = Field(..., gt=0)
    # ISO 3166-1 alpha-2 코드는 고정 2자리 (예: KR)
    alpha2_code: str = Field(..., alias="alpha2Code", min_length=2, max_length=2)
    # ISO 3166-1 alpha-3 코드는 고정 3자리 (예: KOR)
    alpha3_code: str = Field(..., alias="alpha3Code", min_length=3, max_length=3)


class IPLocationInfo(BaseModel):
    """ip-api IP 기반 위치 정보."""

    model_config = {"populate_by_name": True}

    query: str
    country: str
    country_code: str = Field(..., alias="countryCode")
    region_name: str = Field(..., alias="regionName")
    city: str
    # 위도의 정의상 -90(남극)~90(북극)을 벗어날 수 없음
    lat: float = Field(..., ge=-90, le=90)
    # 경도의 정의상 -180~180을 벗어날 수 없음
    lon: float = Field(..., ge=-180, le=180)
    timezone: str
    isp: str


def _validate(model_cls: type[ModelT], payload: dict[str, Any], context: str) -> ModelT:
    """payload를 model_cls로 검증한다. 타입/범위 오류 시 로그를 남기고 예외를 전파한다."""
    try:
        return model_cls.model_validate(payload)
    except ValidationError as e:
        logger.error("[%s] 스키마 검증 실패: %s", context, e)
        raise


def parse_weather(raw: dict[str, Any]) -> list[WeatherHourlyRecord]:
    """hourly 컬럼(time/temperature_2m/precipitation_probability)을 행 단위로 변환·검증한다."""
    hourly = raw["hourly"]
    rows = zip(
        hourly["time"], hourly["temperature_2m"], hourly["precipitation_probability"]
    )
    records = [
        _validate(
            WeatherHourlyRecord,
            {"time": t, "temperature_2m": temp, "precipitation_probability": prob},
            "weather",
        )
        for t, temp, prob in rows
    ]
    logger.info("[weather] %d건 검증 완료", len(records))
    return records


def parse_country(raw: dict[str, Any]) -> CountryInfo:
    """국가 정보 응답을 검증한다."""
    record = _validate(CountryInfo, raw, "country")
    logger.info("[country] 검증 완료: %s", record.name)
    return record


def parse_ip(raw: dict[str, Any]) -> IPLocationInfo:
    """IP 위치 정보 응답을 검증한다."""
    record = _validate(IPLocationInfo, raw, "ip")
    logger.info("[ip] 검증 완료: %s (%s)", record.query, record.city)
    return record
