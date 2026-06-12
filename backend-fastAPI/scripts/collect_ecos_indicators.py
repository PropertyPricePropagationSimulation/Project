"""Collect ECOS economic indicators used by the project.

The targets mirror the ECOS tables supplied as downloaded condition files:
- 1.3.1. 한국은행 기준금리 및 여수신금리
- 1.3.3.2.1. 예금은행 대출금리(신규취급액 기준)
- 4.2.1. 소비자물가지수

Usage:
  python scripts/collect_ecos_indicators.py --start-ym 200501 --end-ym 202512
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import time
from calendar import monthrange
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import urlopen


ROOT_DIR = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT_DIR / "raw" / "ecos"
PROCESSED_DIR = ROOT_DIR / "processed" / "ecos"
DEFAULT_API_BASE_URL = "https://ecos.bok.or.kr/api/StatisticSearch"


@dataclass(frozen=True)
class EcosTarget:
    stat_code: str
    stat_name: str
    cycle: str
    item_code1: str | None = None


TARGETS = [
    EcosTarget("722Y001", "1.3.1. 한국은행 기준금리 및 여수신금리", "D", "0101000"),
    EcosTarget("121Y006", "1.3.3.2.1. 예금은행 대출금리(신규취급액 기준)", "M", "BECBLA0302"),
    EcosTarget("901Y009", "4.2.1. 소비자물가지수", "M", "0"),
]


CSV_COLUMNS = [
    "stat_code",
    "stat_name",
    "cycle",
    "time",
    "item_code1",
    "item_name1",
    "item_code2",
    "item_name2",
    "item_code3",
    "item_name3",
    "item_code4",
    "item_name4",
    "unit_name",
    "data_value",
]


def load_env_file(path: Path) -> None:
    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip("\"'"))


def get_ecos_api_key() -> str:
    load_env_file(ROOT_DIR / ".env")
    api_key = os.getenv("ECOS_API_KEY") or os.getenv("ecos.api.key")
    if not api_key:
        raise RuntimeError("ECOS_API_KEY 또는 ecos.api.key가 .env에 설정되어 있어야 합니다.")
    return api_key


def validate_ym(value: str, field_name: str) -> str:
    if len(value) != 6 or not value.isdigit():
        raise ValueError(f"{field_name} must be YYYYMM format.")
    month = int(value[4:6])
    if month < 1 or month > 12:
        raise ValueError(f"{field_name} has invalid month.")
    return value


def period_for_cycle(cycle: str, start_ym: str, end_ym: str) -> tuple[str, str]:
    if cycle == "D":
        end_year = int(end_ym[:4])
        end_month = int(end_ym[4:6])
        return f"{start_ym}01", f"{end_ym}{monthrange(end_year, end_month)[1]:02d}"
    return start_ym, end_ym


def build_url(
    api_key: str,
    stat_code: str,
    cycle: str,
    start_time: str,
    end_time: str,
    start_count: int,
    end_count: int,
    item_code1: str | None = None,
) -> str:
    base_url = os.getenv("ECOS_API_BASE_URL", DEFAULT_API_BASE_URL).rstrip("/")
    parts = [
        base_url,
        api_key,
        "json",
        "kr",
        str(start_count),
        str(end_count),
        stat_code,
        cycle,
        start_time,
        end_time,
    ]
    if item_code1:
        parts.append(item_code1)
    return "/".join(parts)


def read_json_url(url: str, retries: int = 3, delay_seconds: float = 1.0) -> dict[str, Any]:
    last_error: Exception | None = None
    for attempt in range(retries + 1):
        try:
            with urlopen(url, timeout=60) as response:
                return json.loads(response.read().decode("utf-8"))
        except (HTTPError, URLError, TimeoutError) as exc:
            last_error = exc
            if attempt < retries:
                time.sleep(delay_seconds * (attempt + 1))
                continue
            break
    raise RuntimeError(f"ECOS request failed: {last_error}") from last_error


def normalize_row(row: dict[str, Any], target: EcosTarget) -> dict[str, Any]:
    return {
        "stat_code": target.stat_code,
        "stat_name": target.stat_name,
        "cycle": target.cycle,
        "time": row.get("TIME"),
        "item_code1": row.get("ITEM_CODE1"),
        "item_name1": row.get("ITEM_NAME1"),
        "item_code2": row.get("ITEM_CODE2"),
        "item_name2": row.get("ITEM_NAME2"),
        "item_code3": row.get("ITEM_CODE3"),
        "item_name3": row.get("ITEM_NAME3"),
        "item_code4": row.get("ITEM_CODE4"),
        "item_name4": row.get("ITEM_NAME4"),
        "unit_name": row.get("UNIT_NAME"),
        "data_value": row.get("DATA_VALUE"),
    }


def save_raw_json(target: EcosTarget, start_time: str, end_time: str, start_count: int, end_count: int, payload: dict[str, Any]) -> Path:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    item_suffix = f"_{target.item_code1}" if target.item_code1 else ""
    raw_path = RAW_DIR / f"{target.stat_code}_{target.cycle}{item_suffix}_{start_time}_{end_time}_{start_count}_{end_count}.json"
    raw_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return raw_path


def collect_target(
    api_key: str,
    target: EcosTarget,
    start_ym: str,
    end_ym: str,
    page_size: int,
    save_raw: bool,
) -> list[dict[str, Any]]:
    start_time, end_time = period_for_cycle(target.cycle, start_ym, end_ym)
    rows: list[dict[str, Any]] = []
    start_count = 1
    total_count: int | None = None

    while total_count is None or start_count <= total_count:
        end_count = start_count + page_size - 1
        url = build_url(
            api_key,
            target.stat_code,
            target.cycle,
            start_time,
            end_time,
            start_count,
            end_count,
            target.item_code1,
        )
        payload = read_json_url(url)

        if "RESULT" in payload:
            result = payload["RESULT"]
            code = result.get("CODE")
            message = result.get("MESSAGE")
            if code != "INFO-200":
                raise RuntimeError(f"{target.stat_code} ECOS error {code}: {message}")

        body = payload.get("StatisticSearch", {})
        total_count = int(body.get("list_total_count") or 0)
        page_rows = body.get("row") or []
        if isinstance(page_rows, dict):
            page_rows = [page_rows]

        if save_raw:
            save_raw_json(target, start_time, end_time, start_count, end_count, payload)

        rows.extend(normalize_row(row, target) for row in page_rows)
        print(f"{target.stat_code} {target.cycle}: {len(rows):,}/{total_count:,} rows")

        if not page_rows:
            break
        start_count += len(page_rows)

    return rows


def write_csv(rows: list[dict[str, Any]], start_ym: str, end_ym: str) -> Path:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    output_path = PROCESSED_DIR / f"ecos_indicators_{start_ym}_{end_ym}.csv"
    with output_path.open("w", encoding="utf-8-sig", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    return output_path


def write_manifest(output_path: Path, rows: list[dict[str, Any]], start_ym: str, end_ym: str) -> Path:
    manifest_path = PROCESSED_DIR / "manifest.json"
    by_stat: dict[str, int] = {}
    for row in rows:
        by_stat[row["stat_code"]] = by_stat.get(row["stat_code"], 0) + 1

    manifest = {
        "created_at": datetime.now(UTC).isoformat(),
        "start_ym": start_ym,
        "end_ym": end_ym,
        "output": str(output_path.relative_to(ROOT_DIR)),
        "row_count": len(rows),
        "targets": [
            {
                "stat_code": target.stat_code,
                "stat_name": target.stat_name,
                "cycle": target.cycle,
                "rows": by_stat.get(target.stat_code, 0),
            }
            for target in TARGETS
        ],
    }
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Collect project ECOS indicators into CSV.")
    parser.add_argument("--start-ym", default="200501", help="조회 시작 월(YYYYMM)")
    parser.add_argument("--end-ym", default="202512", help="조회 종료 월(YYYYMM)")
    parser.add_argument("--page-size", type=int, default=10000, help="ECOS 페이지당 조회 건수")
    parser.add_argument("--no-raw", action="store_true", help="원본 ECOS JSON 저장을 생략")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    start_ym = validate_ym(args.start_ym, "start_ym")
    end_ym = validate_ym(args.end_ym, "end_ym")
    if start_ym > end_ym:
        raise ValueError("start_ym must be earlier than or equal to end_ym.")
    if args.page_size < 1 or args.page_size > 100000:
        raise ValueError("page_size must be between 1 and 100000.")

    api_key = get_ecos_api_key()
    all_rows: list[dict[str, Any]] = []
    for target in TARGETS:
        all_rows.extend(
            collect_target(
                api_key=api_key,
                target=target,
                start_ym=start_ym,
                end_ym=end_ym,
                page_size=args.page_size,
                save_raw=not args.no_raw,
            )
        )

    output_path = write_csv(all_rows, start_ym, end_ym)
    manifest_path = write_manifest(output_path, all_rows, start_ym, end_ym)
    print(f"Saved {len(all_rows):,} rows to {output_path}")
    print(f"Saved manifest to {manifest_path}")


if __name__ == "__main__":
    main()
