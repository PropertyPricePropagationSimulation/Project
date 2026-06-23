from datetime import date
from typing import Literal
from pydantic import BaseModel, Field


class HouseMonthlySummaryRead(BaseModel):
    dong_code: str | None = None
    deal_year: int | None = None
    deal_month: int | None = None
    deal_count: int | None = None
    avg_deal_amount: float | None = None
    median_deal_amount: float | None = None
    avg_price_per_sqm: float | None = None
    min_price_per_sqm: float | None = None
    max_price_per_sqm: float | None = None
    is_low_volume: bool | None = None
    year_month: str | None = None


class DuckDBColumnInfo(BaseModel):
    name: str
    data_type: str


class DuckDBTableInfo(BaseModel):
    name: str
    table_type: str
    columns: list[DuckDBColumnInfo] = Field(default_factory=list)


class DuckDBSchemaRead(BaseModel):
    base_tables: list[DuckDBTableInfo]
    summary_table_name: str = "house_monthly_summary"


class EventBase(BaseModel):
    name: str
    event_type: str
    event_date: date
    source: str | None = None
    description: str | None = None


class EventCreate(EventBase):
    pass


class EventRead(EventBase):
    id: int
    event_ym: str

    class Config:
        from_attributes = True


class EventWindowAnalysisRequest(BaseModel):
    event_id: int
    window_months: Literal[3, 6, 12] = Field(
        description="Symmetric analysis window in months around the event month."
    )
    region_codes: list[str] | None = Field(
        default=None,
        description="Optional LAWD_CD region list. Use null or omit it to analyze all regions.",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "event_id": 30,
                "window_months": 3,
                "region_codes": None,
            }
        }
    }


class EventWindowAnalysisBaselineRead(BaseModel):
    year_month: str
    baseline_source: str | None = None
    avg_deal_amount: float | None = None
    median_deal_amount: float | None = None
    avg_price_per_sqm: float | None = None
    deal_count: int | None = None
    is_low_volume: bool | None = None


class EventWindowAnalysisMonthlyRead(BaseModel):
    year_month: str
    relative_month: int
    avg_deal_amount: float | None = None
    median_deal_amount: float | None = None
    avg_price_per_sqm: float | None = None
    deal_count: int | None = None
    price_change_from_event_pct: float | None = None
    price_yoy_pct: float | None = None
    peer_avg_price_change_pct: float | None = None
    excess_price_change_pct: float | None = None
    deal_amount_change_from_event_pct: float | None = None
    median_price_change_from_event_pct: float | None = None
    volume_change_from_event_pct: float | None = None
    monthly_price_return_pct: float | None = None
    is_low_volume: bool | None = None


class EventWindowAnalysisWindowSummaryRead(BaseModel):
    window_months: int
    final_price_change_pct: float | None = None
    final_price_yoy_pct: float | None = None
    final_excess_price_change_pct: float | None = None
    final_deal_amount_change_pct: float | None = None
    final_volume_change_pct: float | None = None
    max_price_rise_pct: float | None = None
    max_price_drop_pct: float | None = None
    reaction_ym: str | None = None
    lag_months: int | None = None
    reaction_direction: str | None = None
    reaction_role: str | None = None
    direction: str | None = None
    impact_score: float | None = None
    is_complete_window: bool
    observed_month_count: int | None = None
    expected_month_count: int | None = None
    missing_reason: str | None = None
    warnings: list[str] = Field(default_factory=list)


class EventWindowAnalysisRegionRead(BaseModel):
    dong_code: str
    baseline: EventWindowAnalysisBaselineRead | None = None
    window_summary: EventWindowAnalysisWindowSummaryRead
    monthly: list[EventWindowAnalysisMonthlyRead] = Field(default_factory=list)


class EventWindowRankingItemRead(BaseModel):
    dong_code: str
    final_price_change_pct: float | None = None
    final_price_yoy_pct: float | None = None
    final_excess_price_change_pct: float | None = None
    final_deal_amount_change_pct: float | None = None
    final_volume_change_pct: float | None = None
    reaction_ym: str | None = None
    lag_months: int | None = None
    reaction_direction: str | None = None
    reaction_role: str | None = None
    impact_score: float | None = None


class EventWindowPropagationRead(BaseModel):
    source_dong_code: str
    target_dong_code: str
    direction: str
    source_reaction_ym: str | None = None
    target_reaction_ym: str | None = None
    reaction_gap_months: int
    propagation_lag_months: int
    correlation: float
    observation_count: int


class EventWindowAnalysisResponse(BaseModel):
    status: str
    event: dict
    analysis: dict
    data_range: dict
    requested_region_count: int | None = None
    summary: dict
    rankings: dict[str, list[EventWindowRankingItemRead]]
    propagation_candidates: list[EventWindowPropagationRead] = Field(default_factory=list)
    result_count: int
    complete_window_count: int
    regions: list[EventWindowAnalysisRegionRead] = Field(default_factory=list)
