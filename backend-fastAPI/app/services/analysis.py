from math import sqrt
from typing import Any, Dict

from app.config_regions import VISIBLE_ANALYSIS_REGION_CODES
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
    region_codes: list[str],
) -> list[dict[str, Any]]:
    if not region_codes:
        return []

    params: list[Any] = [start_ym, end_ym]
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


def _is_eligible_month(row: dict[str, Any] | None) -> bool:
    return bool(row) and not bool(row.get("is_low_volume"))


def _reaction_label(price_change: float | None) -> str:
    if price_change is None:
        return "unknown"
    if price_change > 0:
        return "rise"
    if price_change < 0:
        return "drop"
    return "flat"


def _first_reaction(
    monthly: list[dict[str, Any]],
    threshold_pct: float,
) -> tuple[str | None, int | None, str]:
    for row in monthly:
        if row["relative_month"] <= 0 or row.get("is_low_volume"):
            continue
        price_change = row.get("price_change_from_event_pct")
        if price_change is not None and abs(price_change) >= threshold_pct:
            return row["year_month"], row["relative_month"], _reaction_label(price_change)
    return None, None, "unknown"


def _average(values: list[float | None]) -> float | None:
    numbers = [value for value in values if value is not None]
    if not numbers:
        return None
    return sum(numbers) / len(numbers)


def _pearson_correlation(x_values: list[float], y_values: list[float]) -> float | None:
    if len(x_values) < 2 or len(x_values) != len(y_values):
        return None
    x_mean = sum(x_values) / len(x_values)
    y_mean = sum(y_values) / len(y_values)
    numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(x_values, y_values))
    x_variance = sum((x - x_mean) ** 2 for x in x_values)
    y_variance = sum((y - y_mean) ** 2 for y in y_values)
    denominator = sqrt(x_variance * y_variance)
    if denominator == 0:
        return None
    return numerator / denominator


def _rank_item(region: dict[str, Any]) -> dict[str, Any]:
    summary = region["window_summary"]
    return {
        "dong_code": region["dong_code"],
        "final_price_change_pct": summary["final_price_change_pct"],
        "final_price_yoy_pct": summary["final_price_yoy_pct"],
        "final_excess_price_change_pct": summary["final_excess_price_change_pct"],
        "final_deal_amount_change_pct": summary["final_deal_amount_change_pct"],
        "final_volume_change_pct": summary["final_volume_change_pct"],
        "reaction_ym": summary["reaction_ym"],
        "lag_months": summary["lag_months"],
        "reaction_direction": summary["reaction_direction"],
        "reaction_role": summary["reaction_role"],
        "impact_score": summary["impact_score"],
    }


def _top_rankings(regions: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    def with_value(key: str) -> list[dict[str, Any]]:
        return [row for row in regions if row["window_summary"].get(key) is not None]

    price_regions = with_value("final_price_change_pct")
    yoy_regions = with_value("final_price_yoy_pct")
    excess_regions = with_value("final_excess_price_change_pct")
    volume_regions = with_value("final_volume_change_pct")
    impact_regions = with_value("impact_score")
    reaction_regions = [
        row for row in regions if row["window_summary"].get("lag_months") is not None
    ]
    leader_regions = [
        row
        for row in regions
        if row["window_summary"].get("reaction_role") == "leader"
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
        "top_price_yoy_rise": [
            _rank_item(row)
            for row in sorted(
                yoy_regions,
                key=lambda row: row["window_summary"]["final_price_yoy_pct"],
                reverse=True,
            )[:5]
        ],
        "top_excess_rise": [
            _rank_item(row)
            for row in sorted(
                excess_regions,
                key=lambda row: row["window_summary"]["final_excess_price_change_pct"],
                reverse=True,
            )[:5]
        ],
        "top_excess_drop": [
            _rank_item(row)
            for row in sorted(
                excess_regions,
                key=lambda row: row["window_summary"]["final_excess_price_change_pct"],
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
        "leader_regions": [
            _rank_item(row)
            for row in sorted(
                leader_regions,
                key=lambda row: (
                    row["window_summary"]["lag_months"] or 999,
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


def _annotate_peer_averages(regions: list[dict[str, Any]]) -> None:
    peer_changes_by_month: dict[int, list[float]] = {}
    for region in regions:
        for row in region["monthly"]:
            price_change = row.get("price_change_from_event_pct")
            if row.get("is_low_volume") or price_change is None:
                continue
            peer_changes_by_month.setdefault(row["relative_month"], []).append(price_change)

    for region in regions:
        final_excess = None
        for row in region["monthly"]:
            peer_values = peer_changes_by_month.get(row["relative_month"], [])
            peer_average = _average(peer_values)
            row["peer_avg_price_change_pct"] = _round(peer_average)
            row["excess_price_change_pct"] = _round(
                None if peer_average is None or row.get("price_change_from_event_pct") is None
                else row["price_change_from_event_pct"] - peer_average
            )
            if row["relative_month"] == region["window_summary"]["window_months"]:
                final_excess = row["excess_price_change_pct"]
        region["window_summary"]["final_excess_price_change_pct"] = _round(final_excess)


def _assign_reaction_roles(regions: list[dict[str, Any]]) -> None:
    lag_groups: dict[str, list[int]] = {}
    for region in regions:
        summary = region["window_summary"]
        lag = summary.get("lag_months")
        direction = summary.get("reaction_direction")
        if lag is None or direction in {None, "unknown", "flat"}:
            continue
        lag_groups.setdefault(direction, []).append(lag)

    for region in regions:
        summary = region["window_summary"]
        lag = summary.get("lag_months")
        direction = summary.get("reaction_direction")
        if lag is None or direction in {None, "unknown", "flat"}:
            summary["reaction_role"] = "no_clear_reaction"
            continue

        group_lags = lag_groups.get(direction, [])
        if len(group_lags) <= 1:
            summary["reaction_role"] = "synchronous"
            continue

        min_lag = min(group_lags)
        max_lag = max(group_lags)
        if lag == min_lag and min_lag < max_lag:
            summary["reaction_role"] = "leader"
        elif lag == max_lag and min_lag < max_lag:
            summary["reaction_role"] = "follower"
        else:
            summary["reaction_role"] = "synchronous"


def _build_propagation_candidates(
    regions: list[dict[str, Any]],
    window_months: int,
) -> list[dict[str, Any]]:
    min_observations = 4 if window_months >= 6 else 2
    threshold_correlation = 0.5
    candidates: list[dict[str, Any]] = []

    for source in regions:
        source_summary = source["window_summary"]
        source_lag = source_summary.get("lag_months")
        source_direction = source_summary.get("reaction_direction")
        if source_lag is None or source_direction in {None, "unknown", "flat"}:
            continue

        source_monthly = {row["year_month"]: row for row in source["monthly"]}

        for target in regions:
            if source["dong_code"] == target["dong_code"]:
                continue

            target_summary = target["window_summary"]
            target_lag = target_summary.get("lag_months")
            target_direction = target_summary.get("reaction_direction")
            if (
                target_lag is None
                or target_direction != source_direction
                or target_lag <= source_lag
            ):
                continue

            best_match: dict[str, Any] | None = None
            for lag in range(1, 4):
                x_values: list[float] = []
                y_values: list[float] = []
                for row in target["monthly"]:
                    if row["relative_month"] <= 0 or row.get("is_low_volume"):
                        continue
                    target_return = row.get("monthly_price_return_pct")
                    if target_return is None:
                        continue
                    source_ym = _add_months(row["year_month"], -lag)
                    source_row = source_monthly.get(source_ym)
                    if (
                        source_row is None
                        or source_row["relative_month"] <= 0
                        or source_row.get("is_low_volume")
                    ):
                        continue
                    source_return = source_row.get("monthly_price_return_pct")
                    if source_return is None:
                        continue
                    x_values.append(source_return)
                    y_values.append(target_return)

                correlation = _pearson_correlation(x_values, y_values)
                if correlation is None:
                    continue

                if best_match is None or correlation > best_match["correlation"]:
                    best_match = {
                        "lag": lag,
                        "correlation": correlation,
                        "observations": len(x_values),
                    }

            if (
                best_match
                and best_match["observations"] >= min_observations
                and best_match["correlation"] >= threshold_correlation
            ):
                candidates.append(
                    {
                        "source_dong_code": source["dong_code"],
                        "target_dong_code": target["dong_code"],
                        "direction": source_direction,
                        "source_reaction_ym": source_summary["reaction_ym"],
                        "target_reaction_ym": target_summary["reaction_ym"],
                        "reaction_gap_months": target_lag - source_lag,
                        "propagation_lag_months": best_match["lag"],
                        "correlation": _round(best_match["correlation"], 3),
                        "observation_count": best_match["observations"],
                    }
                )

    return sorted(
        candidates,
        key=lambda row: (
            row["reaction_gap_months"],
            -row["correlation"],
            -row["observation_count"],
        ),
    )


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
    calc_start_ym = _add_months(start_ym, -12)
    threshold_pct = 5.0
    data_range = _available_summary_range(con)

    requested_codes = set(region_codes) if region_codes else VISIBLE_ANALYSIS_REGION_CODES
    analysis_region_codes = sorted(requested_codes & VISIBLE_ANALYSIS_REGION_CODES)
    rows = _monthly_index_rows(con, calc_start_ym, end_ym, analysis_region_codes)
    grouped_rows = _group_by_region(rows)

    regions = []
    for dong_code, monthly_rows in grouped_rows.items():
        row_by_ym = {row["year_month"]: row for row in monthly_rows}
        analysis_rows = [
            row
            for row in monthly_rows
            if start_ym <= row["year_month"] <= end_ym
        ]
        baseline_row = row_by_ym.get(event_ym)
        baseline_source = "event_month"
        if baseline_row is None:
            baseline_row = next(
                (
                    row
                    for row in reversed(monthly_rows)
                    if row["year_month"] <= event_ym
                ),
                None,
            )
            baseline_source = "fallback_previous_observation"

        if baseline_row is None:
            regions.append(
                {
                    "dong_code": dong_code,
                    "baseline": None,
                    "window_summary": {
                        "window_months": window_months,
                        "final_price_change_pct": None,
                        "final_price_yoy_pct": None,
                        "final_excess_price_change_pct": None,
                        "final_volume_change_pct": None,
                        "max_price_rise_pct": None,
                        "max_price_drop_pct": None,
                        "reaction_ym": None,
                        "lag_months": None,
                        "reaction_direction": "unknown",
                        "reaction_role": "no_clear_reaction",
                        "direction": "unknown",
                        "impact_score": None,
                        "is_complete_window": False,
                        "missing_reason": "baseline_data_missing",
                        "warnings": ["No baseline month was available on or before the event month."],
                    },
                    "monthly": [],
                }
            )
            continue

        baseline_price = baseline_row["avg_deal_amount"]
        baseline_median_price = baseline_row["median_deal_amount"]
        baseline_price_per_sqm = baseline_row["avg_price_per_sqm"]
        baseline_volume = baseline_row["deal_count"]

        warnings: list[str] = []
        if baseline_source == "fallback_previous_observation":
            warnings.append(
                f"Event month data missing; baseline fell back to {baseline_row['year_month']}."
            )
        if baseline_row["is_low_volume"]:
            warnings.append("Baseline month is marked as low volume.")

        monthly = []
        for row in analysis_rows:
            relative_month = _month_diff(event_ym, row["year_month"])
            yoy_row = row_by_ym.get(_add_months(row["year_month"], -12))
            previous_month_row = row_by_ym.get(_add_months(row["year_month"], -1))

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
            price_yoy = (
                _pct_change(yoy_row["avg_price_per_sqm"], row["avg_price_per_sqm"])
                if _is_eligible_month(row) and _is_eligible_month(yoy_row)
                else None
            )
            monthly_price_return = (
                _pct_change(
                    previous_month_row["avg_price_per_sqm"],
                    row["avg_price_per_sqm"],
                )
                if _is_eligible_month(row) and _is_eligible_month(previous_month_row)
                else None
            )

            monthly.append(
                {
                    "year_month": row["year_month"],
                    "relative_month": relative_month,
                    "avg_deal_amount": _round(row["avg_deal_amount"]),
                    "median_deal_amount": _round(row["median_deal_amount"]),
                    "avg_price_per_sqm": _round(row["avg_price_per_sqm"]),
                    "deal_count": row["deal_count"],
                    "price_change_from_event_pct": _round(price_change),
                    "price_yoy_pct": _round(price_yoy),
                    "deal_amount_change_from_event_pct": _round(deal_amount_change),
                    "median_price_change_from_event_pct": _round(median_price_change),
                    "volume_change_from_event_pct": _round(volume_change),
                    "monthly_price_return_pct": _round(monthly_price_return),
                    "is_low_volume": row["is_low_volume"],
                }
            )

        final_row = next(
            (row for row in monthly if row["relative_month"] == window_months),
            None,
        )
        post_rows = [row for row in monthly if row["relative_month"] > 0]
        expected_month_count = window_months * 2 + 1
        reaction_ym, lag_months, reaction_direction = _first_reaction(monthly, threshold_pct)

        final_price_change = (
            final_row["price_change_from_event_pct"] if final_row else None
        )
        final_price_yoy = final_row["price_yoy_pct"] if final_row else None
        final_deal_amount_change = (
            final_row["deal_amount_change_from_event_pct"] if final_row else None
        )
        final_volume_change = (
            final_row["volume_change_from_event_pct"] if final_row else None
        )
        post_price_changes = [
            row["price_change_from_event_pct"]
            for row in post_rows
            if not row["is_low_volume"] and row["price_change_from_event_pct"] is not None
        ]
        max_price_rise = max(post_price_changes) if post_price_changes else None
        max_price_drop = min(post_price_changes) if post_price_changes else None

        direction = _reaction_label(final_price_change)

        impact_score = None
        if final_price_change is not None and final_volume_change is not None:
            impact_score = abs(final_price_change) * 0.6 + abs(final_volume_change) * 0.4

        low_volume_month_count = sum(1 for row in monthly if row["is_low_volume"])
        if low_volume_month_count:
            warnings.append(
                f"{low_volume_month_count} month(s) in the analysis window are marked as low volume."
            )
        if final_row and final_row["is_low_volume"]:
            warnings.append("Final comparison month is marked as low volume.")

        regions.append(
            {
                "dong_code": dong_code,
                "baseline": {
                    "year_month": baseline_row["year_month"],
                    "baseline_source": baseline_source,
                    "avg_deal_amount": _round(baseline_price),
                    "median_deal_amount": _round(baseline_median_price),
                    "avg_price_per_sqm": _round(baseline_price_per_sqm),
                    "deal_count": baseline_volume,
                    "is_low_volume": baseline_row["is_low_volume"],
                },
                "window_summary": {
                    "window_months": window_months,
                    "final_price_change_pct": _round(final_price_change),
                    "final_price_yoy_pct": _round(final_price_yoy),
                    "final_excess_price_change_pct": None,
                    "final_deal_amount_change_pct": _round(final_deal_amount_change),
                    "final_volume_change_pct": _round(final_volume_change),
                    "max_price_rise_pct": _round(max_price_rise),
                    "max_price_drop_pct": _round(max_price_drop),
                    "reaction_ym": reaction_ym,
                    "lag_months": lag_months,
                    "reaction_direction": reaction_direction,
                    "reaction_role": "no_clear_reaction",
                    "direction": direction,
                    "impact_score": _round(impact_score),
                    "is_complete_window": len(monthly) == expected_month_count,
                    "observed_month_count": len(monthly),
                    "expected_month_count": expected_month_count,
                    "warnings": warnings,
                },
                "monthly": monthly,
            }
        )

    _annotate_peer_averages(regions)
    _assign_reaction_roles(regions)
    propagation_candidates = _build_propagation_candidates(regions, window_months)

    final_price_changes = [
        region["window_summary"]["final_price_change_pct"]
        for region in regions
        if region["window_summary"]["final_price_change_pct"] is not None
    ]
    final_price_yoys = [
        region["window_summary"]["final_price_yoy_pct"]
        for region in regions
        if region["window_summary"]["final_price_yoy_pct"] is not None
    ]
    final_excess_changes = [
        region["window_summary"]["final_excess_price_change_pct"]
        for region in regions
        if region["window_summary"]["final_excess_price_change_pct"] is not None
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
    leader_count = sum(
        1
        for region in regions
        if region["window_summary"]["reaction_role"] == "leader"
    )
    follower_count = sum(
        1
        for region in regions
        if region["window_summary"]["reaction_role"] == "follower"
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
            "yoy_reference": "same_month_previous_year",
            "peer_average_scope": "requested_regions_or_all_regions",
            "low_volume_policy": "excluded_from_yoy_peer_average_reaction_and_propagation",
        },
        "data_range": data_range,
        "requested_region_count": len(region_codes) if region_codes else None,
        "summary": {
            "region_count": len(regions),
            "complete_window_count": complete_count,
            "avg_price_change_after_window_pct": _round(_average(final_price_changes)),
            "avg_price_yoy_after_window_pct": _round(_average(final_price_yoys)),
            "avg_excess_price_change_after_window_pct": _round(_average(final_excess_changes)),
            "avg_volume_change_after_window_pct": _round(_average(final_volume_changes)),
            "rising_region_count": rising_count,
            "falling_region_count": falling_count,
            "strong_reaction_region_count": strong_reaction_count,
            "leader_region_count": leader_count,
            "follower_region_count": follower_count,
            "propagation_candidate_count": len(propagation_candidates),
        },
        "rankings": _top_rankings(regions),
        "propagation_candidates": propagation_candidates,
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
