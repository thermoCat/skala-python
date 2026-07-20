"""검증된 데이터를 CSV/Parquet으로 저장하고 읽기·쓰기 성능을 비교한다."""
import logging
import time

import pandas as pd
from pydantic import BaseModel

from . import config

logger = logging.getLogger(__name__)


def _to_dataframe(records: list[BaseModel] | BaseModel) -> pd.DataFrame:
    """단일 모델 또는 모델 리스트를 DataFrame으로 변환한다."""
    if isinstance(records, BaseModel):
        records = [records]
    return pd.DataFrame([r.model_dump() for r in records])


def save_and_benchmark(records: list[BaseModel] | BaseModel, name: str) -> dict[str, float]:
    """CSV/Parquet으로 저장 후 재읽기하여 각 단계 소요 시간을 측정·로깅한다."""
    config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    df = _to_dataframe(records)
    csv_path = config.DATA_DIR / f"{name}.csv"
    parquet_path = config.DATA_DIR / f"{name}.parquet"

    timings: dict[str, float] = {}

    start = time.perf_counter()
    df.to_csv(csv_path, index=False)
    timings["csv_write"] = time.perf_counter() - start

    start = time.perf_counter()
    pd.read_csv(csv_path)
    timings["csv_read"] = time.perf_counter() - start

    start = time.perf_counter()
    df.to_parquet(parquet_path, index=False)
    timings["parquet_write"] = time.perf_counter() - start

    start = time.perf_counter()
    pd.read_parquet(parquet_path)
    timings["parquet_read"] = time.perf_counter() - start

    logger.info(
        "[%s] %d행 저장 완료 — CSV 쓰기 %.4fs/읽기 %.4fs, Parquet 쓰기 %.4fs/읽기 %.4fs",
        name,
        len(df),
        timings["csv_write"],
        timings["csv_read"],
        timings["parquet_write"],
        timings["parquet_read"],
    )
    return timings
