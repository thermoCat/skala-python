"""검증된 데이터를 CSV/Parquet으로 저장하고 읽기·쓰기 성능을 비교한다."""
import logging
import time
import unicodedata

import pandas as pd
from pydantic import BaseModel

from . import config

logger = logging.getLogger(__name__)

_TABLE_HEADERS = [
    "데이터셋",
    "행수",
    "CSV 쓰기(평균/콜드)",
    "CSV 읽기(평균/콜드)",
    "Parquet 쓰기(평균/콜드)",
    "Parquet 읽기(평균/콜드)",
]


def _to_dataframe(records: list[BaseModel] | BaseModel) -> pd.DataFrame:
    """단일 모델 또는 모델 리스트를 DataFrame으로 변환한다."""
    if isinstance(records, BaseModel):
        records = [records]
    return pd.DataFrame([r.model_dump() for r in records])


def _benchmark_step(fn, rounds: int) -> tuple[float, float]:
    """fn을 rounds회 반복 실행해 (콜드스타트 값, 평균 값)을 초 단위로 반환한다.

    1회차(콜드스타트)는 pyarrow 최초 로딩 등 일회성 비용이 섞여 매번 새 프로세스로
    실행할 때 사용자가 실제 체감하는 시간에 가깝고, 평균값은 그 노이즈를 걷어낸
    포맷 자체의 순수한 처리 성능 비교에 가깝다. 두 값을 함께 남겨 용도에 맞게 참고한다.
    """
    durations = []
    for _ in range(rounds):
        start = time.perf_counter()
        fn()
        durations.append(time.perf_counter() - start)
    return durations[0], sum(durations) / rounds


def save_and_benchmark(
    records: list[BaseModel] | BaseModel, name: str, rounds: int = 3
) -> dict[str, float]:
    """CSV/Parquet으로 저장 후 재읽기를 rounds회 반복해 콜드스타트/평균 소요 시간을 측정·로깅한다."""
    config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    df = _to_dataframe(records)
    csv_path = config.DATA_DIR / f"{name}.csv"
    parquet_path = config.DATA_DIR / f"{name}.parquet"

    steps = {
        "csv_write": lambda: df.to_csv(csv_path, index=False),
        "csv_read": lambda: pd.read_csv(csv_path),
        "parquet_write": lambda: df.to_parquet(parquet_path, index=False),
        "parquet_read": lambda: pd.read_parquet(parquet_path),
    }
    timings: dict[str, float] = {"rows": len(df)}
    for step_name, fn in steps.items():
        cold, avg = _benchmark_step(fn, rounds)
        timings[f"{step_name}_cold"] = cold
        timings[f"{step_name}_avg"] = avg

    return timings


def _display_width(text: str) -> int:
    """한글 등 동아시아 넓은 문자를 2칸으로 계산해 터미널 표시 폭을 구한다."""
    return sum(2 if unicodedata.east_asian_width(ch) in "WF" else 1 for ch in text)


def _pad(text: str, width: int) -> str:
    """표시 폭 기준으로 오른쪽에 공백을 채워 열을 정렬한다."""
    return text + " " * (width - _display_width(text))


def render_summary_table(results: dict[str, dict[str, float]]) -> str:
    """데이터셋별 저장/성능 비교 결과를 정렬된 표 문자열로 렌더링한다."""
    rows = [
        [
            name,
            str(int(t["rows"])),
            f"{t['csv_write_avg']:.4f}s / {t['csv_write_cold']:.4f}s",
            f"{t['csv_read_avg']:.4f}s / {t['csv_read_cold']:.4f}s",
            f"{t['parquet_write_avg']:.4f}s / {t['parquet_write_cold']:.4f}s",
            f"{t['parquet_read_avg']:.4f}s / {t['parquet_read_cold']:.4f}s",
        ]
        for name, t in results.items()
    ]

    widths = [
        max(_display_width(_TABLE_HEADERS[i]), *(_display_width(r[i]) for r in rows))
        for i in range(len(_TABLE_HEADERS))
    ]
    separator = "+" + "+".join("-" * (w + 2) for w in widths) + "+"

    def format_row(cols: list[str]) -> str:
        return "| " + " | ".join(_pad(c, widths[i]) for i, c in enumerate(cols)) + " |"

    lines = [separator, format_row(_TABLE_HEADERS), separator]
    lines += [format_row(r) for r in rows]
    lines.append(separator)
    return "\n".join(lines)
