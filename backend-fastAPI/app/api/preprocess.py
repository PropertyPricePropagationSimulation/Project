from typing import Any, Dict

from fastapi import APIRouter, Query

from app.services.preprocessor import get_preprocess_status, run_preprocess

router = APIRouter()


@router.post("/run")
async def run_preprocess_endpoint(
    min_deal_count: int = Query(3, ge=1, description="분석 신뢰도 판단에 사용할 월별 최소 거래 건수입니다."),
    save_cleaned: bool = Query(True, description="정제된 거래 데이터를 processed/에 저장할지 여부입니다."),
    save_summary: bool = Query(True, description="월별·지역별 집계 요약 데이터를 저장할지 여부입니다."),
) -> Dict[str, Any]:
    return run_preprocess(
        min_deal_count=min_deal_count,
        save_cleaned=save_cleaned,
        save_summary=save_summary,
    )


@router.get("/status")
async def preprocess_status() -> Dict[str, Any]:
    return get_preprocess_status()
