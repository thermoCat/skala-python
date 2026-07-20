"""pipeline.schemas 모듈의 Pydantic 검증 테스트."""
import pytest
from pydantic import ValidationError

from pipeline.schemas import CountryInfo, IPLocationInfo, WeatherHourlyRecord, parse_weather


def test_weather_record_valid():
    """정상 범위의 날씨 레코드는 그대로 검증을 통과해야 한다."""
    record = WeatherHourlyRecord(
        time="2026-07-20T00:00", temperature_2m=23.2, precipitation_probability=10
    )
    assert record.temperature_2m == 23.2


def test_weather_record_invalid_probability_range():
    """강수확률이 0~100 범위를 벗어나면 ValidationError가 발생해야 한다."""
    with pytest.raises(ValidationError):
        WeatherHourlyRecord(
            time="2026-07-20T00:00", temperature_2m=23.2, precipitation_probability=150
        )


def test_parse_weather_zips_hourly_columns():
    """hourly 컬럼(time/temperature_2m/precipitation_probability)이 행 단위로 올바르게 묶여야 한다."""
    raw = {
        "hourly": {
            "time": ["2026-07-20T00:00", "2026-07-20T01:00"],
            "temperature_2m": [23.2, 22.9],
            "precipitation_probability": [10, 20],
        }
    }
    records = parse_weather(raw)
    assert len(records) == 2
    assert records[1].precipitation_probability == 20


def test_country_info_alias_mapping():
    """countries.dev 응답의 alpha2Code/alpha3Code alias가 정상 매핑되어야 한다."""
    record = CountryInfo(
        name="Korea (Republic of)",
        capital="Seoul",
        region="Asia",
        subregion="Eastern Asia",
        population=51780579,
        area=100210,
        alpha2Code="KR",
        alpha3Code="KOR",
    )
    assert record.alpha2_code == "KR"


def test_ip_location_info_invalid_type():
    """위도(lat)에 숫자로 변환 불가능한 문자열이 오면 ValidationError가 발생해야 한다."""
    with pytest.raises(ValidationError):
        IPLocationInfo(
            query="8.8.8.8",
            country="United States",
            countryCode="US",
            regionName="Virginia",
            city="Ashburn",
            lat="not-a-float",
            lon=-77.5,
            timezone="America/New_York",
            isp="Google LLC",
        )
