from typing import Any, Dict

from app.services.duckdb_service import SUMMARY_TABLE, get_connection, init_schema


def _row_to_event(row: tuple) -> Dict[str, Any]:
    event_id, name, event_type, event_date, event_ym, source, description = row
    return {
        "id": event_id,
        "name": name,
        "event_type": event_type,
        "event_date": event_date.isoformat() if hasattr(event_date, "isoformat") else str(event_date),
        "event_ym": event_ym,
        "source": source,
        "description": description,
    }


def _add_months(ym: str, months: int) -> str:
    year = int(ym[:4])
    month = int(ym[4:6])
    month_index = year * 12 + (month - 1) + months
    new_year = month_index // 12
    new_month = month_index % 12 + 1
    return f"{new_year:04d}{new_month:02d}"


def _pct_change(before: float | None, after: float | None) -> float | None:
    if before is None or after is None or before == 0:
        return None
    return (after - before) / before * 100


def _month_diff(base_ym: str, target_ym: str) -> int:
    base_year = int(base_ym[:4])
    base_month = int(base_ym[4:6])
    target_year = int(target_ym[:4])
    target_month = int(target_ym[4:6])
    return (target_year - base_year) * 12 + (target_month - base_month)


def _round(value: Any, digits: int = 2) -> Any:
    if isinstance(value, float):
        return round(value, digits)
    return value


def _event_by_id(con: Any, event_id: int) -> Dict[str, Any] | None:
    row = con.execute(
        """
        SELECT id, name, event_type, event_date, event_ym, source, description
        FROM events
        WHERE id = ?
        """,
        [event_id],
    ).fetchone()
    return _row_to_event(row) if row else None


def _available_summary_range(con: Any) -> Dict[str, str | None]:
    min_ym, max_ym = con.execute(
        f"SELECT MIN(year_month), MAX(year_month) FROM {SUMMARY_TABLE}"
    ).fetchone()
    return {"min_year_month": min_ym, "max_year_month": max_ym}


def _monthly_index_rows(
    con: Any,
    start_ym: str,
    end_ym: str,
    region_codes: list[str] | None,
) -> list[dict[str, Any]]:
    region_filter = ""
    params: list[Any] = [start_ym, end_ym]
    if region_codes:
        placeholders = ", ".join(["?"] * len(region_codes))
        region_filter = f"AND dong_code IN ({placeholders})"
        params.extend(region_codes)

    cursor = con.execute(
        f"""
        SELECT
            dong_code,
            year_month,
            deal_count,
            avg_deal_amount,
            median_deal_amount,
            avg_price_per_sqm,
            is_low_volume
        FROM {SUMMARY_TABLE}
        WHERE year_month BETWEEN ? AND ?
            {region_filter}
        ORDER BY dong_code, year_month
        """,
        params,
    )
    columns = [column[0] for column in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def _group_by_region(rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        grouped.setdefault(row["dong_code"], []).append(row)
    return grouped


def _first_reaction(
    monthly: list[dict[str, Any]],
    threshold_pct: float,
) -> tuple[str | None, int | None]:
    for row in monthly:
        if row["relative_month"] <= 0:
            continue
        price_change = row.get("price_change_from_event_pct")
        if price_change is not None and abs(price_change) >= threshold_pct:
            return row["year_month"], row["relative_month"]
    return None, None


def _average(values: list[float | None]) -> float | None:
    numbers = [value for value in values if value is not None]
    if not numbers:
        return None
    return sum(numbers) / len(numbers)


def _rank_item(region: dict[str, Any]) -> dict[str, Any]:
    summary = region["window_summary"]
    return {
        "dong_code": region["dong_code"],
        "final_price_change_pct": summary["final_price_change_pct"],
        "final_deal_amount_change_pct": summary["final_deal_amount_change_pct"],
        "final_volume_change_pct": summary["final_volume_change_pct"],
        "reaction_ym": summary["reaction_ym"],
        "lag_months": summary["lag_months"],
        "impact_score": summary["impact_score"],
    }


def _top_rankings(regions: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    def with_value(key: str) -> list[dict[str, Any]]:
        return [row for row in regions if row["window_summary"].get(key) is not None]

    price_regions = with_value("final_price_change_pct")
    volume_regions = with_value("final_volume_change_pct")
    impact_regions = with_value("impact_score")
    reaction_regions = [
        row for row in regions if row["window_summary"].get("lag_months") is not None
    ]

    return {
        "top_price_rise": [
            _rank_item(row)
            for row in sorted(
                price_regions,
                key=lambda row: row["window_summary"]["final_price_change_pct"],
                reverse=True,
            )[:5]
        ],
        "top_price_drop": [
            _rank_item(row)
            for row in sorted(
                price_regions,
                key=lambda row: row["window_summary"]["final_price_change_pct"],
            )[:5]
        ],
        "top_volume_rise": [
            _rank_item(row)
            for row in sorted(
                volume_regions,
                key=lambda row: row["window_summary"]["final_volume_change_pct"],
                reverse=True,
            )[:5]
        ],
        "fastest_reaction": [
            _rank_item(row)
            for row in sorted(
                reaction_regions,
                key=lambda row: (
                    row["window_summary"]["lag_months"],
                    -(row["window_summary"]["impact_score"] or 0),
                ),
            )[:5]
        ],
        "highest_impact": [
            _rank_item(row)
            for row in sorted(
                impact_regions,
                key=lambda row: row["window_summary"]["impact_score"],
                reverse=True,
            )[:5]
        ],
    }


def run_event_window_analysis(payload: Dict[str, Any]) -> Dict[str, Any]:
    event_id = payload["event_id"]
    window_months = payload["window_months"]
    region_codes = payload.get("region_codes")

    if window_months not in {3, 6, 12}:
        return {
            "status": "invalid_window",
            "message": "window_months must be one of 3, 6, or 12.",
        }

    init_schema()
    con = get_connection()
    event = _event_by_id(con, event_id)
    if event is None:
        return {"status": "not_found", "event_id": event_id}

    event_ym = event["event_ym"]
    start_ym = _add_months(event_ym, -window_months)
    end_ym = _add_months(event_ym, window_months)
    threshold_pct = 5.0
    data_range = _available_summary_range(con)

    rows = _monthly_index_rows(con, start_ym, end_ym, region_codes)
    grouped_rows = _group_by_region(rows)

    regions = []
    for dong_code, monthly_rows in grouped_rows.items():
        baseline_row = next(
            (row for row in monthly_rows if row["year_month"] == event_ym),
            None,
        )
        if baseline_row is None:
            regions.append(
                {
                    "dong_code": dong_code,
                    "baseline": None,
                    "window_summary": {
                        "final_price_change_pct": None,
                        "final_volume_change_pct": None,
                        "max_price_rise_pct": None,
                        "max_price_drop_pct": None,
                        "reaction_ym": None,
                        "lag_months": None,
                        "direction": "unknown",
                        "impact_score": None,
                        "is_complete_window": False,
                        "missing_reason": "event_month_data_missing",
                    },
                    "monthly": [],
                }
            )
            continue

        baseline_price = baseline_row["avg_deal_amount"]
        baseline_median_price = baseline_row["median_deal_amount"]
        baseline_price_per_sqm = baseline_row["avg_price_per_sqm"]
        baseline_volume = baseline_row["deal_count"]

        monthly = []
        for row in monthly_rows:
            relative_month = _month_diff(event_ym, row["year_month"])
            deal_amount_change = _pct_change(baseline_price, row["avg_deal_amount"])
            median_price_change = _pct_change(
                baseline_median_price,
                row["median_deal_amount"],
            )
            price_change = _pct_change(
                baseline_price_per_sqm,
                row["avg_price_per_sqm"],
            )
            volume_change = _pct_change(baseline_volume, row["deal_count"])
            monthly.append(
                {
                    "year_month": row["year_month"],
                    "relative_month": relative_month,
                    "avg_deal_amount": _round(row["avg_deal_amount"]),
                    "median_deal_amount": _round(row["median_deal_amount"]),
                    "avg_price_per_sqm": _round(row["avg_price_per_sqm"]),
                    "deal_count": row["deal_count"],
                    "price_change_from_event_pct": _round(price_change),
                    "deal_amount_change_from_event_pct": _round(deal_amount_change),
                    "median_price_change_from_event_pct": _round(median_price_change),
                    "volume_change_from_event_pct": _round(volume_change),
                    "is_low_volume": row["is_low_volume"],
                }
            )

        final_row = next(
            (row for row in monthly if row["relative_month"] == window_months),
            None,
        )
        post_rows = [row for row in monthly if row["relative_month"] > 0]
        expected_month_count = window_months * 2 + 1
        reaction_ym, lag_months = _first_reaction(monthly, threshold_pct)

        final_price_change = (
            final_row["price_change_from_event_pct"] if final_row else None
        )
        final_deal_amount_change = (
            final_row["deal_amount_change_from_event_pct"] if final_row else None
        )
        final_volume_change = (
            final_row["volume_change_from_event_pct"] if final_row else None
        )
        post_price_changes = [
            row["price_change_from_event_pct"]
            for row in post_rows
            if row["price_change_from_event_pct"] is not None
        ]
        max_price_rise = max(post_price_changes) if post_price_changes else None
        max_price_drop = min(post_price_changes) if post_price_changes else None

        direction = "unknown"
        if final_price_change is not None:
            if final_price_change > 0:
                direction = "rise"
            elif final_price_change < 0:
                direction = "drop"
            else:
                direction = "flat"

        impact_score = None
        if final_price_change is not None and final_volume_change is not None:
            impact_score = abs(final_price_change) * 0.6 + abs(final_volume_change) * 0.4

        regions.append(
            {
                "dong_code": dong_code,
                "baseline": {
                    "year_month": event_ym,
                    "avg_deal_amount": _round(baseline_price),
                    "median_deal_amount": _round(baseline_median_price),
                    "avg_price_per_sqm": _round(baseline_price_per_sqm),
                    "deal_count": baseline_volume,
                    "is_low_volume": baseline_row["is_low_volume"],
                },
                "window_summary": {
                    "final_price_change_pct": _round(final_price_change),
                    "final_deal_amount_change_pct": _round(final_deal_amount_change),
                    "final_volume_change_pct": _round(final_volume_change),
                    "max_price_rise_pct": _round(max_price_rise),
                    "max_price_drop_pct": _round(max_price_drop),
                    "reaction_ym": reaction_ym,
                    "lag_months": lag_months,
                    "direction": direction,
                    "impact_score": _round(impact_score),
                    "is_complete_window": len(monthly) == expected_month_count,
                    "observed_month_count": len(monthly),
                    "expected_month_count": expected_month_count,
                },
                "monthly": monthly,
            }
        )

    final_price_changes = [
        region["window_summary"]["final_price_change_pct"]
        for region in regions
        if region["window_summary"]["final_price_change_pct"] is not None
    ]
    final_volume_changes = [
        region["window_summary"]["final_volume_change_pct"]
        for region in regions
        if region["window_summary"]["final_volume_change_pct"] is not None
    ]
    complete_count = sum(
        1 for region in regions if region["window_summary"]["is_complete_window"]
    )
    rising_count = sum(
        1
        for region in regions
        if (region["window_summary"]["final_price_change_pct"] or 0) > 0
    )
    falling_count = sum(
        1
        for region in regions
        if (
            region["window_summary"]["final_price_change_pct"] is not None
            and region["window_summary"]["final_price_change_pct"] < 0
        )
    )
    strong_reaction_count = sum(
        1 for region in regions if region["window_summary"]["reaction_ym"] is not None
    )

    return {
        "status": "success",
        "event": event,
        "analysis": {
            "mode": "event_month_indexed",
            "window_months": window_months,
            "baseline_ym": event_ym,
            "period": {
                "start_ym": start_ym,
                "end_ym": end_ym,
            },
            "threshold_pct": threshold_pct,
        },
        "data_range": data_range,
        "requested_region_count": len(region_codes) if region_codes else None,
        "summary": {
            "region_count": len(regions),
            "complete_window_count": complete_count,
            "avg_price_change_after_window_pct": _round(_average(final_price_changes)),
            "avg_volume_change_after_window_pct": _round(_average(final_volume_changes)),
            "rising_region_count": rising_count,
            "falling_region_count": falling_count,
            "strong_reaction_region_count": strong_reaction_count,
        },
        "rankings": _top_rankings(regions),
        "result_count": len(regions),
        "complete_window_count": complete_count,
        "regions": regions,
    }


def run_analysis() -> Dict[str, Any]:
    return {"status": "not implemented", "detail": "Use run_event_window_analysis()."}


def get_event_lag(event_id: int) -> Dict[str, Any]:
    return {"status": "not implemented", "event_id": event_id}


def get_analysis_result() -> Dict[str, Any]:
    return {"status": "not implemented", "result": []}
