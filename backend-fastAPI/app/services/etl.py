from pathlib import Path
from datetime import datetime
import json
import duckdb
import pandas as pd

# Use repository-level `processed/` directory (backend-fastAPI/processed)
BASE_DIR = Path(__file__).resolve().parents[2]
PROCESSED_DIR = BASE_DIR / "processed"
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)


def _partition_path(year: int, month: int, dong_code: str | None = None) -> Path:
    parts = [str(year), f"{month:02d}"]
    sub = PROCESSED_DIR.joinpath(*parts)
    sub.mkdir(parents=True, exist_ok=True)
    filename = f"houses{('_' + dong_code) if dong_code else ''}.parquet"
    return sub / filename


def write_parquet_from_df(df: pd.DataFrame, year: int, month: int, dong_code: str | None = None) -> Path:
    """Write DataFrame to Parquet using DuckDB's parquet writer for portability."""
    path = _partition_path(year, month, dong_code)
    # Use DuckDB to write Parquet to avoid pyarrow dependency
    rel = duckdb.from_df(df)
    rel.to_parquet(str(path))
    return path


def create_sample_houses() -> pd.DataFrame:
    data = [
        {
            "no": 1,
            "apt_seq": "A1",
            "apt_name": "샘플아파트A",
            "sido_name": "서울",
            "gugun_name": "강남구",
            "dong_name": "역삼동",
            "dong_code": "11680101",
            "jibun": "1-1",
            "road_name": "테스트로",
            "build_year": 2005,
            "latitude": "37.499",
            "longitude": "127.036",
            "apt_dong": "101동",
            "floor": "10",
            "deal_year": 2023,
            "deal_month": 1,
            "deal_day": 15,
            "exclu_use_ar": 84.97,
            "deal_amount": "100000",
        },
        {
            "no": 2,
            "apt_seq": "A2",
            "apt_name": "샘플아파트B",
            "sido_name": "서울",
            "gugun_name": "강남구",
            "dong_name": "역삼동",
            "dong_code": "11680101",
            "jibun": "2-2",
            "road_name": "테스트로",
            "build_year": 2010,
            "latitude": "37.500",
            "longitude": "127.037",
            "apt_dong": "102동",
            "floor": "5",
            "deal_year": 2023,
            "deal_month": 2,
            "deal_day": 20,
            "exclu_use_ar": 59.82,
            "deal_amount": "200000",
        },
    ]
    return pd.DataFrame(data)


def update_manifest(entry: dict):
    manifest_path = PROCESSED_DIR / "manifest.json"
    manifest = {"processed": []}
    if manifest_path.exists():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except Exception:
            manifest = {"processed": []}

    manifest["processed"].append(entry)
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")


def run_initial_load(sample: bool = True):
    """Run initial ETL: create Parquet files under `processed/` and write manifest.

    If `sample` is True, create sample data. In production, replace sample creation
    with real collector->preprocessor flow that yields DataFrames.
    """
    now = datetime.utcnow().isoformat()
    if sample:
        df = create_sample_houses()
        # group by deal_year, deal_month, dong_code and write per partition
        for (year, month, dong), group in df.groupby(["deal_year", "deal_month", "dong_code"]):
            path = write_parquet_from_df(group, int(year), int(month), dong)
            update_manifest({
                "path": str(path.relative_to(PROCESSED_DIR)),
                "year": int(year),
                "month": int(month),
                "dong_code": dong,
                "rows": len(group),
                "created_at": now,
            })
    else:
        # Placeholder for real ingestion pipeline
        raise NotImplementedError("Non-sample initial load path not implemented yet")
