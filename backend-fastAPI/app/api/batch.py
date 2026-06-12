"""초기 데이터 적재를 위한 배치 API 엔드포인트입니다."""

from datetime import datetime
import logging
from typing import Any, Dict, List

from fastapi import APIRouter, Query

from app.config import BASE_DIR
from app.config_regions import get_region_codes
from app.services import collector
from app.services.duckdb_service import list_tables, register_parquet_files

router = APIRouter()
logger = logging.getLogger(__name__)

DB_PATH = BASE_DIR / "result" / "ssafy.duckdb"


@router.post("/import/sale-data")
async def import_sale_data(
    start_ym: str | None = Query(None, pattern=r"^\d{6}$", description="수집 시작 연월입니다. 예: 202401"),
    end_ym: str | None = Query(None, pattern=r"^\d{6}$", description="수집 종료 연월입니다. 예: 202412"),
    region_codes: List[str] | None = Query(None, description="수집할 지역 코드입니다. 예: 11680.미입력 시 전체 지역이 대상이 됩니다."),
    max_regions: int = Query(49, ge=1, description="Swagger 또는 수동 실행 시 한 번에 처리할 최대 지역 수입니다.최대 49개 지역이 있습니다"),
) -> Dict[str, Any]:
    """국토부 아파트 매매 실거래가 데이터를 수집합니다.

    Swagger 또는 수동 실행에서 공공 API 요청 한도를 바로 소진하지 않도록 기본 범위는 작게 설정되어 있습니다.
    """
    if start_ym is None or end_ym is None:
        current_ym = datetime.now().strftime("%Y%m")
        start_ym = start_ym or current_ym
        end_ym = end_ym or current_ym

    target_regions = (region_codes or get_region_codes())[:max_regions]
    summary: Dict[str, Any] = {
        "status": "running",
        "regions": target_regions,
        "start_ym": start_ym,
        "end_ym": end_ym,
        "save_raw": True,
        "save_processed": False,
        "skip_existing_processed": False,
        "results": [],
    }

    for region_code in target_regions:
        try:
            result = await collector.collect_sale_data_for_period(
                start_ym=start_ym,
                end_ym=end_ym,
                region=region_code,
                save_raw=True,
                save_processed=False,
                skip_existing_processed=False,
            )
            summary["results"].append({
                "region": region_code,
                "status": "success",
                "periods_collected": len(result.get("periods", [])),
                "detail": result.get("periods", []),
            })
        except collector.ApiRateLimitError as exc:
            logger.warning("Rate limited while collecting region %s: %s", region_code, exc)
            summary["results"].append({
                "region": region_code,
                "status": "rate_limited",
                "error": str(exc),
            })
            summary["status"] = "rate_limited"
            summary["message"] = (
                "국토부 API가 429 요청 제한 오류를 반복해서 반환했습니다. "
                "추가 요청을 막기 위해 배치를 중단했습니다. 잠시 후 다시 시도하거나 수집 기간과 지역 수를 줄여주세요."
            )
            return summary
        except Exception as exc:
            logger.exception("Error collecting region %s", region_code)
            summary["results"].append({
                "region": region_code,
                "status": "error",
                "error": str(exc),
            })

    summary["duckdb_registration"] = {
        "status": "skipped",
        "reason": "sale-data import stores public API responses in raw/ only.",
    }

    summary["status"] = "completed"
    return summary


@router.post("/register-parquet-files")
async def register_parquet_files_endpoint() -> Dict[str, Any]:
    """manifest에 기록된 Parquet 파일을 DuckDB에 수동으로 등록합니다."""
    try:
        result = register_parquet_files(str(DB_PATH))
        return {
            "status": "success",
            "result": result,
        }
    except Exception as exc:
        logger.exception("Error registering Parquet files")
        return {
            "status": "error",
            "message": str(exc),
        }


@router.get("/import/sale-data/regions")
async def list_target_regions() -> Dict[str, Any]:
    """배치 수집 대상 지역 코드 목록을 조회합니다."""
    region_codes = get_region_codes()
    return {
        "total_regions": len(region_codes),
        "region_codes": region_codes,
        "description": "Seoul 25 districts + 9 Seoul-metro cities",
    }


@router.get("/status")
async def import_status() -> Dict[str, Any]:
    """수집 및 등록된 데이터 상태를 조회합니다. DuckDB 테이블과 건수를 반환합니다."""
    try:
        tables = list_tables(str(DB_PATH))

        from app.services.duckdb_service import get_connection

        con = get_connection(str(DB_PATH))

        table_info = []
        for table_name, table_type in tables:
            try:
                count = con.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
                table_info.append({
                    "name": table_name,
                    "type": table_type,
                    "record_count": count,
                })
            except Exception:
                table_info.append({
                    "name": table_name,
                    "type": table_type,
                    "record_count": "N/A",
                })

        return {
            "status": "success",
            "db_path": str(DB_PATH),
            "tables": table_info,
        }
    except Exception as exc:
        logger.exception("Error checking import status")
        return {
            "status": "error",
            "message": str(exc),
        }
