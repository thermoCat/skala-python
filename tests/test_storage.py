"""pipeline.storage 모듈의 저장·성능 비교 로직 테스트 (네트워크 불필요)."""
from pipeline import config, storage
from pipeline.schemas import CountryInfo


def _sample_country() -> CountryInfo:
    return CountryInfo(
        name="Korea (Republic of)",
        capital="Seoul",
        region="Asia",
        subregion="Eastern Asia",
        population=51780579,
        area=100210,
        alpha2Code="KR",
        alpha3Code="KOR",
    )


def test_save_and_benchmark_writes_both_formats_and_returns_all_timings(tmp_path, monkeypatch):
    """CSV/Parquet 파일이 모두 생성되고, rows·콜드스타트/평균 타이밍 값이 모두 반환돼야 한다."""
    monkeypatch.setattr(config, "DATA_DIR", tmp_path)

    timings = storage.save_and_benchmark(_sample_country(), "country_test", rounds=2)

    assert (tmp_path / "country_test.csv").exists()
    assert (tmp_path / "country_test.parquet").exists()
    expected_keys = {"rows"} | {
        f"{step}_{kind}"
        for step in ("csv_write", "csv_read", "parquet_write", "parquet_read")
        for kind in ("cold", "avg")
    }
    assert set(timings) == expected_keys
    assert timings["rows"] == 1
    assert all(v >= 0 for v in timings.values())


def test_render_summary_table_aligns_korean_headers_with_data_rows(tmp_path, monkeypatch):
    """표 헤더와 데이터 행이 한글 폭을 고려해 줄마다 동일한 길이로 정렬돼야 한다."""
    monkeypatch.setattr(config, "DATA_DIR", tmp_path)
    timings = storage.save_and_benchmark(_sample_country(), "country_test", rounds=1)

    table = storage.render_summary_table({"country": timings})
    lines = table.splitlines()

    assert len(lines) == 5  # 상단 구분선, 헤더, 구분선, 데이터 1행, 하단 구분선
    # len()이 아닌 실제 터미널 표시 폭 기준으로 모든 줄이 같은 폭이어야 정렬된 것
    display_widths = {storage._display_width(line) for line in lines}
    assert len(display_widths) == 1
