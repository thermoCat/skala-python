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
    temperature_2m: float = Field(..., ge=-50, le=60, description="섭씨 기온")
    precipitation_probability: int = Field(..., ge=0, le=100, description="강수확률(%)")


class CountryInfo(BaseModel):
    """countries.dev 한국 국가 정보."""

    model_config = {"populate_by_name": True}

    name: str
    capital: str
    region: str
    subregion: str
    population: int = Field(..., gt=0)
    area: float = Field(..., gt=0)
    alpha2_code: str = Field(..., alias="alpha2Code")
    alpha3_code: str = Field(..., alias="alpha3Code")


class IPLocationInfo(BaseModel):
    """ip-api IP 기반 위치 정보."""

    model_config = {"populate_by_name": True}

    query: str
    country: str
    country_code: str = Field(..., alias="countryCode")
    region_name: str = Field(..., alias="regionName")
    city: str
    lat: float = Field(..., ge=-90, le=90)
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
