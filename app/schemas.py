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
    window_months: Literal[3, 6, 12]
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
