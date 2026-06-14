"""Preprocess collected ECOS indicators into analysis-ready tables.

Inputs:
  processed/ecos/ecos_indicators_<start_ym>_<end_ym>.csv

Outputs:
  processed/ecos/base_rate_changes_<start_ym>_<end_ym>.csv
  processed/ecos/monthly_macro_indicators_<start_ym>_<end_ym>.csv
"""

from __future__ import annotations

import argparse
import csv
import json
from calendar import monthrange
from collections import defaultdict
from dataclasses import dataclass
from datetime import UTC, date, datetime
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
PROCESSED_DIR = ROOT_DIR / "processed" / "ecos"

BASE_RATE_CODE = "722Y001"
BASE_RATE_ITEM_CODE = "0101000"
MORTGAGE_RATE_CODE = "121Y006"
MORTGAGE_RATE_ITEM_CODE = "BECBLA0302"
CPI_CODE = "901Y009"
CPI_ITEM_CODE = "0"


@dataclass(frozen=True)
class IndicatorRow:
    stat_code: str
    time: str
    item_code1: str
    item_name1: str
    value: float


def parse_value(value: str) -> float:
    return float(str(value).replace(",", "").strip())


def parse_date(value: str) -> date:
    if len(value) != 8:
        raise ValueError(f"Expected YYYYMMDD date, got {value!r}")
    return date(int(value[:4]), int(value[4:6]), int(value[6:8]))


def iter_months(start_ym: str, end_ym: str) -> list[str]:
    start_index = int(start_ym[:4]) * 12 + int(start_ym[4:6])
    end_index = int(end_ym[:4]) * 12 + int(end_ym[4:6])
    return [f"{(index - 1) // 12}{(index - 1) % 12 + 1:02d}" for index in range(start_index, end_index + 1)]


def read_indicator_rows(input_path: Path) -> list[IndicatorRow]:
    rows: list[IndicatorRow] = []
    with input_path.open("r", encoding="utf-8-sig", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            value = row.get("data_value")
            if value in {None, ""}:
                continue
            rows.append(
                IndicatorRow(
                    stat_code=row["stat_code"],
                    time=row["time"],
                    item_code1=row["item_code1"],
                    item_name1=row["item_name1"],
                    value=parse_value(value),
                )
            )
    return rows


def build_base_rate_changes(base_rows: list[IndicatorRow]) -> list[dict[str, str | float]]:
    sorted_rows = sorted(base_rows, key=lambda row: row.time)
    changes: list[dict[str, str | float]] = []
    previous: IndicatorRow | None = None

    for row in sorted_rows:
        if previous is None:
            previous = row
            continue
        if row.value == previous.value:
            previous = row
            continue

        delta = round(row.value - previous.value, 4)
        changes.append(
            {
                "event_date": parse_date(row.time).isoformat(),
                "event_ym": row.time[:6],
                "previous_rate": previous.value,
                "new_rate": row.value,
                "delta": delta,
                "direction": "hike" if delta > 0 else "cut",
                "previous_observed_date": parse_date(previous.time).isoformat(),
                "stat_code": row.stat_code,
                "item_code": row.item_code1,
                "item_name": row.item_name1,
            }
        )
        previous = row

    return changes


def get_month_end_base_rate(base_rows: list[IndicatorRow], ym: str) -> float | None:
    month_rows = [row for row in base_rows if row.time.startswith(ym)]
    if month_rows:
        return sorted(month_rows, key=lambda row: row.time)[-1].value

    prior_rows = [row for row in base_rows if row.time[:6] < ym]
    if prior_rows:
        return sorted(prior_rows, key=lambda row: row.time)[-1].value
    return None


def average(values: list[float]) -> float | None:
    if not values:
        return None
    return round(sum(values) / len(values), 6)


def build_monthly_macro(rows: list[IndicatorRow], changes: list[dict[str, str | float]], start_ym: str, end_ym: str) -> list[dict[str, str | float | int | None]]:
    base_rows = [row for row in rows if row.stat_code == BASE_RATE_CODE and row.item_code1 == BASE_RATE_ITEM_CODE]
    mortgage_by_month = {
        row.time: row.value
        for row in rows
        if row.stat_code == MORTGAGE_RATE_CODE and row.item_code1 == MORTGAGE_RATE_ITEM_CODE
    }
    cpi_by_month = {
        row.time: row.value
        for row in rows
        if row.stat_code == CPI_CODE and row.item_code1 == CPI_ITEM_CODE
    }

    base_values_by_month: dict[str, list[float]] = defaultdict(list)
    for row in base_rows:
        base_values_by_month[row.time[:6]].append(row.value)

    changes_by_month: dict[str, list[dict[str, str | float]]] = defaultdict(list)
    for change in changes:
        changes_by_month[str(change["event_ym"])].append(change)

    monthly_rows: list[dict[str, str | float | int | None]] = []
    for ym in iter_months(start_ym, end_ym):
        year = int(ym[:4])
        month = int(ym[4:6])
        month_changes = changes_by_month.get(ym, [])
        delta_sum = round(sum(float(change["delta"]) for change in month_changes), 4)
        base_rate_end = get_month_end_base_rate(base_rows, ym)
        base_rate_avg = average(base_values_by_month.get(ym, []))
        mortgage_rate = mortgage_by_month.get(ym)
        cpi = cpi_by_month.get(ym)
        prior_cpi = cpi_by_month.get(previous_month(ym))

        monthly_rows.append(
            {
                "year_month": ym,
                "month_start_date": f"{year:04d}-{month:02d}-01",
                "month_end_date": f"{year:04d}-{month:02d}-{monthrange(year, month)[1]:02d}",
                "base_rate_end": base_rate_end,
                "base_rate_avg": base_rate_avg,
                "base_rate_changed": "true" if month_changes else "false",
                "base_rate_change_count": len(month_changes),
                "base_rate_delta_sum": delta_sum,
                "base_rate_change_dates": ";".join(str(change["event_date"]) for change in month_changes),
                "mortgage_rate": mortgage_rate,
                "cpi": cpi,
                "cpi_mom_pct": round((cpi / prior_cpi - 1) * 100, 6) if cpi is not None and prior_cpi else None,
            }
        )

    return monthly_rows


def previous_month(ym: str) -> str:
    year = int(ym[:4])
    month = int(ym[4:6])
    if month == 1:
        return f"{year - 1}12"
    return f"{year}{month - 1:02d}"


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_manifest(start_ym: str, end_ym: str, input_path: Path, changes_path: Path, monthly_path: Path, change_count: int, monthly_count: int) -> None:
    manifest_path = PROCESSED_DIR / "preprocess_manifest.json"
    manifest = {
        "created_at": datetime.now(UTC).isoformat(),
        "start_ym": start_ym,
        "end_ym": end_ym,
        "input": str(input_path.relative_to(ROOT_DIR)),
        "outputs": {
            "base_rate_changes": {
                "path": str(changes_path.relative_to(ROOT_DIR)),
                "rows": change_count,
            },
            "monthly_macro_indicators": {
                "path": str(monthly_path.relative_to(ROOT_DIR)),
                "rows": monthly_count,
            },
        },
    }
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Preprocess collected ECOS indicators.")
    parser.add_argument("--start-ym", default="200501", help="Start month in YYYYMM format.")
    parser.add_argument("--end-ym", default="202512", help="End month in YYYYMM format.")
    parser.add_argument("--input", default=None, help="Input normalized ECOS CSV path.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    start_ym = args.start_ym
    end_ym = args.end_ym
    input_path = Path(args.input) if args.input else PROCESSED_DIR / f"ecos_indicators_{start_ym}_{end_ym}.csv"
    if not input_path.is_absolute():
        input_path = ROOT_DIR / input_path
    if not input_path.exists():
        raise FileNotFoundError(input_path)

    rows = read_indicator_rows(input_path)
    base_rows = [row for row in rows if row.stat_code == BASE_RATE_CODE and row.item_code1 == BASE_RATE_ITEM_CODE]
    changes = build_base_rate_changes(base_rows)
    monthly = build_monthly_macro(rows, changes, start_ym, end_ym)

    changes_path = PROCESSED_DIR / f"base_rate_changes_{start_ym}_{end_ym}.csv"
    monthly_path = PROCESSED_DIR / f"monthly_macro_indicators_{start_ym}_{end_ym}.csv"

    write_csv(
        changes_path,
        changes,
        [
            "event_date",
            "event_ym",
            "previous_rate",
            "new_rate",
            "delta",
            "direction",
            "previous_observed_date",
            "stat_code",
            "item_code",
            "item_name",
        ],
    )
    write_csv(
        monthly_path,
        monthly,
        [
            "year_month",
            "month_start_date",
            "month_end_date",
            "base_rate_end",
            "base_rate_avg",
            "base_rate_changed",
            "base_rate_change_count",
            "base_rate_delta_sum",
            "base_rate_change_dates",
            "mortgage_rate",
            "cpi",
            "cpi_mom_pct",
        ],
    )
    write_manifest(start_ym, end_ym, input_path, changes_path, monthly_path, len(changes), len(monthly))
    print(f"Saved {len(changes):,} base-rate change events to {changes_path}")
    print(f"Saved {len(monthly):,} monthly macro rows to {monthly_path}")


if __name__ == "__main__":
    main()
