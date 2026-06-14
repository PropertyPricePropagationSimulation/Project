from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field, model_validator

from app.services.collector import (
    collect_ecos_raw,
    collect_legal_dong_code,
    collect_rone_raw,
    collect_sale_data,
    collect_sale_data_for_regions,
    resolve_region_codes,
)

router = APIRouter()


class CollectRequest(BaseModel):
    start_ym: Optional[str] = Field(None, pattern=r"^\d{6}$", description="수집 시작 연월입니다. 예: 202301")
    end_ym: Optional[str] = Field(None, pattern=r"^\d{6}$", description="수집 종료 연월입니다. 예: 202412")
    region_codes: Optional[List[str]] = Field(None, description="국토부 API LAWD_CD 지역 코드 목록입니다. 예: ['11680']")
    region_keyword: Optional[str] = Field(None, description="JUSO API로 법정동 코드를 조회할 지역 검색어입니다.")

    # Backward-compatible fields used by the existing scripts/API.
    start_year: Optional[int] = Field(None, ge=2000)
    end_year: Optional[int] = Field(None, ge=2000)
    region: Optional[str] = None

    save_raw: bool = True
    save_processed: bool = True

    @model_validator(mode="after")
    def validate_period_and_region(self):
        has_ym_period = self.start_ym is not None and self.end_ym is not None
        has_year_period = self.start_year is not None and self.end_year is not None
        if not has_ym_period and not has_year_period:
            raise ValueError("start_ym/end_ym 또는 start_year/end_year 중 하나를 입력해야 합니다.")

        has_region_codes = bool(self.region_codes)
        has_legacy_region = bool(self.region)
        has_keyword = bool(self.region_keyword)
        if not has_region_codes and not has_legacy_region and not has_keyword:
            raise ValueError("region_codes, region, region_keyword 중 하나를 입력해야 합니다.")
        return self


class EcosRawCollectRequest(BaseModel):
    stat_code: str = Field(..., description="ECOS 통계표 코드입니다.")
    cycle: str = Field(..., description="주기입니다. 예: M, Q, A")
    start_time: str = Field(..., description="조회 시작 시점입니다. 예: 202001")
    end_time: str = Field(..., description="조회 종료 시점입니다. 예: 202512")
    item_code1: Optional[str] = Field(None, description="ECOS 항목 코드 1입니다.")
    item_code2: Optional[str] = Field(None, description="ECOS 항목 코드 2입니다.")
    item_code3: Optional[str] = Field(None, description="ECOS 항목 코드 3입니다.")
    item_code4: Optional[str] = Field(None, description="ECOS 항목 코드 4입니다.")
    start_count: int = Field(1, ge=1, description="조회 시작 건수입니다.")
    end_count: int = Field(100000, ge=1, description="조회 종료 건수입니다.")
    language: str = Field("kr", description="응답 언어입니다.")
    output_format: str = Field("json", description="응답 형식입니다. json 또는 xml")


class RoneRawCollectRequest(BaseModel):
    params: Dict[str, Any] = Field(default_factory=dict, description="R-ONE API에 전달할 쿼리 파라미터입니다.")


@router.post("/legal-dong-code")
async def collect_legal_dong_code_endpoint(
    region: str = Query(..., description="법정동 코드를 조회할 지역 검색어입니다."),
    page: int = Query(1, ge=1, description="조회할 페이지 번호입니다."),
    count_per_page: int = Query(100, ge=1, le=1000, description="페이지당 조회 건수입니다."),
) -> Dict[str, Any]:
    try:
        return await collect_legal_dong_code(region, page, count_per_page)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/region-codes")
async def resolve_region_codes_endpoint(
    region_keyword: str = Query(..., description="법정동 코드로 변환할 지역 검색어입니다.")
) -> Dict[str, Any]:
    try:
        return await resolve_region_codes(region_keyword)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/sale-data")
async def collect_sale_data_endpoint(payload: CollectRequest) -> Dict[str, Any]:
    try:
        if payload.start_year is not None and payload.end_year is not None and payload.region:
            return await collect_sale_data(
                start_year=payload.start_year,
                end_year=payload.end_year,
                region=payload.region,
                save_raw=payload.save_raw,
                save_processed=payload.save_processed,
            )

        start_ym = payload.start_ym or f"{payload.start_year}01"
        end_ym = payload.end_ym or f"{payload.end_year}12"
        region_codes = payload.region_codes or ([payload.region] if payload.region else None)

        if payload.region_keyword:
            resolved = await resolve_region_codes(payload.region_keyword)
            region_codes = resolved["region_codes"]

        return await collect_sale_data_for_regions(
            start_ym=start_ym,
            end_ym=end_ym,
            region_codes=region_codes or [],
            save_raw=payload.save_raw,
            save_processed=payload.save_processed,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/ecos/raw")
async def collect_ecos_raw_endpoint(payload: EcosRawCollectRequest) -> Dict[str, Any]:
    try:
        return await collect_ecos_raw(**payload.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/r-one/raw")
async def collect_rone_raw_endpoint(payload: RoneRawCollectRequest) -> Dict[str, Any]:
    try:
        return await collect_rone_raw(params=payload.params)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
