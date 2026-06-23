"""DuckDB-backed apartment trade summary analysis endpoints."""

from typing import Any, Dict
import logging

from fastapi import APIRouter, Body, HTTPException, Query

from app.schemas import EventWindowAnalysisRequest, EventWindowAnalysisResponse
from app.config import BASE_DIR
from app.services import analysis as analysis_service
from app.services.duckdb_service import SUMMARY_TABLE, get_connection

router = APIRouter()
logger = logging.getLogger(__name__)

DB_PATH = BASE_DIR / "result" / "ssafy.duckdb"


def _rows_to_dicts(cursor) -> list[dict[str, Any]]:
    columns = [column[0] for column in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def _summary_filters(
    region: str | None = None,
    year: int | None = None,
    min_avg_price: int | None = None,
    max_avg_price: int | None = None,
) -> tuple[str, list[Any]]:
    where_parts = []
    params: list[Any] = []
    if region:
        where_parts.append("dong_code = ?")
        params.append(region)
    if year:
        where_parts.append("deal_year = ?")
        params.append(year)
    if min_avg_price:
        where_parts.append("avg_deal_amount >= ?")
        params.append(min_avg_price)
    if max_avg_price:
        where_parts.append("avg_deal_amount <= ?")
        params.append(max_avg_price)

    where_clause = "WHERE " + " AND ".join(where_parts) if where_parts else ""
    return where_clause, params


@router.get("/search/houses")
async def search_houses(
    region: str | None = Query(None, description="LAWD_CD region code, for example 11680."),
    year: int | None = Query(None, description="Deal year, for example 2023."),
    min_price: int | None = Query(None, description="Minimum average deal amount."),
    max_price: int | None = Query(None, description="Maximum average deal amount."),
    limit: int = Query(100, le=1000, description="Maximum number of rows."),
) -> Dict[str, Any]:
    """Return monthly region-level apartment trade summaries."""
    try:
        conn = get_connection(str(DB_PATH))
        where_clause, params = _summary_filters(region, year, min_price, max_price)
        params.append(limit)
        cursor = conn.execute(
            f"""
            SELECT
                dong_code,
                deal_year,
                deal_month,
                year_month,
                deal_count,
                avg_deal_amount,
                median_deal_amount,
                avg_price_per_sqm,
                min_price_per_sqm,
                max_price_per_sqm,
                is_low_volume
            FROM {SUMMARY_TABLE}
            {where_clause}
            ORDER BY year_month DESC, dong_code
            LIMIT ?
            """,
            params,
        )

        data = _rows_to_dicts(cursor)
        return {
            "status": "success",
            "count": len(data),
            "filters": {
                "region": region,
                "year": year,
                "min_price": min_price,
                "max_price": max_price,
            },
            "data": data,
        }
    except Exception as exc:
        logger.exception("Error searching house monthly summaries: %s", exc)
        return {"status": "error", "message": str(exc)}


@router.get("/stats/by-region")
async def get_stats_by_region(
    year: int | None = Query(None, description="Deal year for aggregation."),
) -> Dict[str, Any]:
    """Return region-level yearly aggregates from monthly summary rows."""
    try:
        conn = get_connection(str(DB_PATH))
        where_clause = "WHERE deal_year = ?" if year else ""
        params = [year] if year else []
        cursor = conn.execute(
            f"""
            SELECT
                dong_code,
                SUM(deal_count) AS deal_count,
                AVG(avg_deal_amount) AS avg_deal_amount,
                AVG(median_deal_amount) AS avg_median_deal_amount,
                AVG(avg_price_per_sqm) AS avg_price_per_sqm,
                MIN(min_price_per_sqm) AS min_price_per_sqm,
                MAX(max_price_per_sqm) AS max_price_per_sqm
            FROM {SUMMARY_TABLE}
            {where_clause}
            GROUP BY dong_code
            ORDER BY deal_count DESC
            """,
            params,
        )
        return {"status": "success", "year": year, "data": _rows_to_dicts(cursor)}
    except Exception as exc:
        logger.exception("Error getting stats by region: %s", exc)
        return {"status": "error", "message": str(exc)}


@router.get("/stats/by-year")
async def get_stats_by_year(
    region: str | None = Query(None, description="LAWD_CD region code."),
) -> Dict[str, Any]:
    """Return yearly aggregates from monthly summary rows."""
    try:
        conn = get_connection(str(DB_PATH))
        where_clause = "WHERE dong_code = ?" if region else ""
        params = [region] if region else []
        cursor = conn.execute(
            f"""
            SELECT
                deal_year,
                SUM(deal_count) AS deal_count,
                AVG(avg_deal_amount) AS avg_deal_amount,
                AVG(median_deal_amount) AS avg_median_deal_amount,
                AVG(avg_price_per_sqm) AS avg_price_per_sqm,
                MIN(min_price_per_sqm) AS min_price_per_sqm,
                MAX(max_price_per_sqm) AS max_price_per_sqm
            FROM {SUMMARY_TABLE}
            {where_clause}
            GROUP BY deal_year
            ORDER BY deal_year DESC
            """,
            params,
        )
        return {"status": "success", "region": region, "data": _rows_to_dicts(cursor)}
    except Exception as exc:
        logger.exception("Error getting stats by year: %s", exc)
        return {"status": "error", "message": str(exc)}


@router.post("/run")
async def run_analysis():
    return {
        "message": "Analysis execution endpoint placeholder.",
        "note": "Use GET /analysis/search/houses and /analysis/stats/* for prepared DuckDB summaries.",
    }


@router.post("/event-window", response_model=EventWindowAnalysisResponse)
async def run_event_window_analysis(
    payload: EventWindowAnalysisRequest = Body(
        ...,
        openapi_examples={
            "all_regions": {
                "summary": "Analyze all regions",
                "value": {
                    "event_id": 30,
                    "window_months": 3,
                    "region_codes": None,
                },
            },
            "selected_regions": {
                "summary": "Analyze selected regions",
                "value": {
                    "event_id": 30,
                    "window_months": 3,
                    "region_codes": ["11650", "11680"],
                },
            },
        },
    ),
):
    result = analysis_service.run_event_window_analysis(payload.model_dump())
    if result["status"] == "not_found":
        raise HTTPException(status_code=404, detail="Event not found.")
    if result["status"] == "invalid_window":
        raise HTTPException(status_code=422, detail=result["message"])
    return result


@router.get("/{event_id}/lag")
async def get_event_lag(event_id: int):
    return {"message": "Event lag analysis endpoint placeholder.", "event_id": event_id}


@router.get("/result")
async def get_analysis_result():
    return {"message": "Analysis result endpoint placeholder."}
