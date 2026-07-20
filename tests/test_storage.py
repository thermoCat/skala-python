"""pipeline.storage 모듈의 저장·성능 비교 로직 테스트 (네트워크 불필요)."""
from pipeline import config, storage
from pipeline.schemas import CountryInfo


def test_save_and_benchmark_writes_both_formats_and_returns_all_timings(tmp_path, monkeypatch):
    """CSV/Parquet 파일이 모두 생성되고, 콜드스타트/평균 8가지 타이밍 값이 모두 0 이상 반환돼야 한다."""
    monkeypatch.setattr(config, "DATA_DIR", tmp_path)
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

    timings = storage.save_and_benchmark(record, "country_test", rounds=2)

    assert (tmp_path / "country_test.csv").exists()
    assert (tmp_path / "country_test.parquet").exists()
    expected_keys = {
        f"{step}_{kind}"
        for step in ("csv_write", "csv_read", "parquet_write", "parquet_read")
        for kind in ("cold", "avg")
    }
    assert set(timings) == expected_keys
    assert all(v >= 0 for v in timings.values())
