"""파이프라인 전역 설정값 (API 엔드포인트, 저장 경로 등)."""
from pathlib import Path

# 서울 좌표 (Open-Meteo 조회 기준점)
SEOUL_LATITUDE = 37.5665
SEOUL_LONGITUDE = 126.9780

WEATHER_URL = (
    "https://api.open-meteo.com/v1/forecast"
    f"?latitude={SEOUL_LATITUDE}&longitude={SEOUL_LONGITUDE}"
    "&hourly=temperature_2m,precipitation_probability"
    "&forecast_days=3&timezone=Asia/Seoul"
)
COUNTRY_URL = "https://countries.dev/alpha/KOR"
IP_URL = "http://ip-api.com/json/8.8.8.8"

REQUEST_TIMEOUT = 10.0  # 초 단위 요청 타임아웃

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
