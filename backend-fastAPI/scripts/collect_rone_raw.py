"""Collect R-ONE apartment index raw XML for project target regions.

R-ONE region codes are not the same as MOLIT LAWD_CD values. This collector
uses R-ONE CLS_ID values mapped from the project target regions.

Targets:
- A_2024_00045: (monthly) apartment sale price index
- A_2024_00050: (monthly) apartment jeonse price index
"""

from __future__ import annotations

import argparse
import json
import os
import time
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from urllib.error import URLError
from urllib.parse import urlencode
from urllib.request import urlopen


ROOT_DIR = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT_DIR / "raw" / "rone"
BASE_URL = "https://www.reb.or.kr/r-one/openapi/SttsApiTblData.do"


@dataclass(frozen=True)
class RoneTarget:
    name: str
    statbl_id: str
    statbl_name: str
    dtacycle_cd: str
    item_ids: tuple[str, ...]


TARGETS = [
    RoneTarget(
        name="apartment_sale_price_index",
        statbl_id="A_2024_00045",
        statbl_name="(월) 매매가격지수_아파트",
        dtacycle_cd="MM",
        item_ids=("500001", "100001"),
    ),
    RoneTarget(
        name="apartment_jeonse_price_index",
        statbl_id="A_2024_00050",
        statbl_name="(월) 전세가격지수_아파트",
        dtacycle_cd="MM",
        item_ids=("500001", "100001"),
    ),
]


# project LAWD_CD(5 digits) -> R-ONE CLS_ID for apartment regional index tables
TARGET_REGION_MAP = [
    {"name": "anyang", "lawd_cd": "41170", "rone_cls_id": "520019"},
    {"name": "seongnam", "lawd_cd": "41130", "rone_cls_id": "520020"},
    {"name": "yongin", "lawd_cd": "41460", "rone_cls_id": "520025"},
    {"name": "suwon", "lawd_cd": "41110", "rone_cls_id": "520026"},
    {"name": "bucheon", "lawd_cd": "41190", "rone_cls_id": "520028"},
    {"name": "ansan", "lawd_cd": "41270", "rone_cls_id": "520029"},
    {"name": "hwaseong", "lawd_cd": "41590", "rone_cls_id": "520032"},
    {"name": "gimpo", "lawd_cd": "41570", "rone_cls_id": "520044"},
    {"name": "goyang", "lawd_cd": "41280", "rone_cls_id": "520045"},
    {"name": "jongno_gu", "lawd_cd": "11110", "rone_cls_id": "530011"},
    {"name": "jung_gu", "lawd_cd": "11140", "rone_cls_id": "530012"},
    {"name": "yongsan_gu", "lawd_cd": "11170", "rone_cls_id": "530013"},
    {"name": "seongdong_gu", "lawd_cd": "11200", "rone_cls_id": "530015"},
    {"name": "gwangjin_gu", "lawd_cd": "11215", "rone_cls_id": "530016"},
    {"name": "dongdaemun_gu", "lawd_cd": "11230", "rone_cls_id": "530017"},
    {"name": "jungnang_gu", "lawd_cd": "11260", "rone_cls_id": "530018"},
    {"name": "seongbuk_gu", "lawd_cd": "11290", "rone_cls_id": "530019"},
    {"name": "gangbuk_gu", "lawd_cd": "11305", "rone_cls_id": "530020"},
    {"name": "dobong_gu", "lawd_cd": "11320", "rone_cls_id": "530021"},
    {"name": "nowon_gu", "lawd_cd": "11350", "rone_cls_id": "530022"},
    {"name": "eunpyeong_gu", "lawd_cd": "11380", "rone_cls_id": "530024"},
    {"name": "seodaemun_gu", "lawd_cd": "11410", "rone_cls_id": "530025"},
    {"name": "mapo_gu", "lawd_cd": "11440", "rone_cls_id": "530026"},
    {"name": "yangcheon_gu", "lawd_cd": "11470", "rone_cls_id": "530029"},
    {"name": "gangseo_gu", "lawd_cd": "11500", "rone_cls_id": "530030"},
    {"name": "guro_gu", "lawd_cd": "11530", "rone_cls_id": "530031"},
    {"name": "geumcheon_gu", "lawd_cd": "11545", "rone_cls_id": "530032"},
    {"name": "yeongdeungpo_gu", "lawd_cd": "11560", "rone_cls_id": "530033"},
    {"name": "dongjak_gu", "lawd_cd": "11590", "rone_cls_id": "530034"},
    {"name": "gwanak_gu", "lawd_cd": "11620", "rone_cls_id": "530035"},
    {"name": "seocho_gu", "lawd_cd": "11650", "rone_cls_id": "530037"},
    {"name": "gangnam_gu", "lawd_cd": "11680", "rone_cls_id": "530038"},
    {"name": "songpa_gu", "lawd_cd": "11710", "rone_cls_id": "530039"},
    {"name": "gangdong_gu", "lawd_cd": "11740", "rone_cls_id": "530040"},
]
TARGET_CLS_IDS = {region["rone_cls_id"] for region in TARGET_REGION_MAP}
REGION_BY_CLS_ID = {region["rone_cls_id"]: region for region in TARGET_REGION_MAP}


def load_env_file(path: Path) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip("\"'"))


def get_rone_api_key() -> str:
    load_env_file(ROOT_DIR / ".env")
    api_key = os.getenv("RONE_API_KEY") or os.getenv("rone.api.key")
    if not api_key:
        raise RuntimeError("RONE_API_KEY or rone.api.key must be configured in .env.")
    return api_key


def validate_ym(value: str, field_name: str) -> str:
    if len(value) != 6 or not value.isdigit():
        raise ValueError(f"{field_name} must be YYYYMM format.")
    month = int(value[4:6])
    if month < 1 or month > 12:
        raise ValueError(f"{field_name} has invalid month.")
    return value


def iter_months(start_ym: str, end_ym: str):
    start_index = int(start_ym[:4]) * 12 + int(start_ym[4:6])
    end_index = int(end_ym[:4]) * 12 + int(end_ym[4:6])
    if start_index > end_index:
        raise ValueError("start_ym must be earlier than or equal to end_ym.")

    for index in range(start_index, end_index + 1):
        year = (index - 1) // 12
        month = (index - 1) % 12 + 1
        yield f"{year}{month:02d}"


def build_params(api_key: str, target: RoneTarget, ym: str, page: int, page_size: int) -> dict[str, str | int]:
    params: dict[str, str | int] = {
        "KEY": api_key,
        "pIndex": page,
        "pSize": page_size,
        "STATBL_ID": target.statbl_id,
        "DTACYCLE_CD": target.dtacycle_cd,
        "WRTTIME_IDTFR_ID": ym,
    }
    for index, item_id in enumerate(target.item_ids, start=1):
        params[f"ITM_ID{index}"] = item_id
    return params


def request_xml(params: dict[str, str | int], retries: int = 3, delay_seconds: float = 1.0) -> str:
    url = f"{BASE_URL}?{urlencode(params)}"
    last_error: Exception | None = None
    for attempt in range(retries + 1):
        try:
            with urlopen(url, timeout=60) as response:
                return response.read().decode("utf-8")
        except (ConnectionError, TimeoutError, URLError) as exc:
            last_error = exc
            if attempt < retries:
                time.sleep(delay_seconds * (attempt + 1))
                continue
            break
    raise RuntimeError(f"R-ONE request failed: {last_error}") from last_error


def response_status(root: ET.Element) -> tuple[str, str, int]:
    code = root.findtext(".//CODE") or ""
    message = root.findtext(".//MESSAGE") or ""
    total_count_text = root.findtext(".//list_total_count")
    total_count = int(total_count_text) if total_count_text and total_count_text.isdigit() else len(root.findall(".//row"))
    return code, message, total_count


def filter_to_target_regions(text: str) -> tuple[str, int]:
    root = ET.fromstring(text)
    kept = 0
    for row in list(root.findall("row")):
        cls_id = row.findtext("CLS_ID") or ""
        if cls_id not in TARGET_CLS_IDS:
            root.remove(row)
            continue

        region = REGION_BY_CLS_ID[cls_id]
        ET.SubElement(row, "PROJECT_LAWD_CD").text = region["lawd_cd"]
        ET.SubElement(row, "PROJECT_REGION_NAME").text = region["name"]
        kept += 1

    count_node = root.find("./head/list_total_count")
    if count_node is not None:
        count_node.text = str(kept)

    xml_body = ET.tostring(root, encoding="unicode")
    return '<?xml version="1.0" encoding="UTF-8"?>\n' + xml_body + "\n", kept


def raw_path_for(target: RoneTarget, ym: str, page: int) -> Path:
    return RAW_DIR / target.name / f"{target.statbl_id}_{ym}_p{page}.xml"


def save_raw(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def redacted_params(params: dict[str, str | int]) -> dict[str, str | int]:
    return {key: ("***REDACTED***" if key.upper() == "KEY" else value) for key, value in params.items()}


def collect_target(api_key: str, target: RoneTarget, start_ym: str, end_ym: str, page_size: int, delay_seconds: float):
    saved = []
    no_data_months = []

    for ym in iter_months(start_ym, end_ym):
        page = 1
        saved_for_month = 0
        total_count = None

        while total_count is None or (page - 1) * page_size < total_count:
            path = raw_path_for(target, ym, page)
            params = build_params(api_key, target, ym, page, page_size)

            if path.exists():
                filtered_text = path.read_text(encoding="utf-8")
                root = ET.fromstring(filtered_text)
                _, _, total_count = response_status(root)
                kept_count = len(root.findall(".//row"))
                status = "existing"
            else:
                response_text = request_xml(params)
                root = ET.fromstring(response_text)
                code, message, total_count = response_status(root)
                if code == "INFO-200":
                    no_data_months.append(ym)
                    break
                if code != "INFO-000":
                    raise RuntimeError(f"{target.name} {ym} page {page}: {code} {message}")

                filtered_text, kept_count = filter_to_target_regions(response_text)
                if kept_count == 0:
                    break
                save_raw(path, filtered_text)
                status = "collected"

            saved.append(
                {
                    "target": target.name,
                    "statbl_id": target.statbl_id,
                    "statbl_name": target.statbl_name,
                    "year_month": ym,
                    "page": page,
                    "source_total_count": total_count,
                    "target_region_row_count": kept_count,
                    "raw_path": str(path.relative_to(ROOT_DIR)),
                    "params": redacted_params(params),
                    "status": status,
                }
            )
            saved_for_month += 1
            page += 1

            if delay_seconds > 0:
                time.sleep(delay_seconds)

        print(f"{target.name} {ym}: saved {saved_for_month} page(s)")

    return saved, no_data_months


def write_manifest(start_ym: str, end_ym: str, saved: list[dict], no_data: dict[str, list[str]]) -> Path:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    manifest_path = RAW_DIR / f"manifest_{start_ym}_{end_ym}.json"
    manifest = {
        "created_at": datetime.now(UTC).isoformat(),
        "start_ym": start_ym,
        "end_ym": end_ym,
        "base_url": BASE_URL,
        "note": "Rows are filtered by R-ONE CLS_ID, not MOLIT LAWD_CD. Mapping is included below.",
        "target_regions": TARGET_REGION_MAP,
        "saved_file_count": len(saved),
        "targets": [
            {
                "name": target.name,
                "statbl_id": target.statbl_id,
                "statbl_name": target.statbl_name,
                "dtacycle_cd": target.dtacycle_cd,
                "item_ids": list(target.item_ids),
                "saved_pages": sum(1 for item in saved if item["target"] == target.name),
                "no_data_months": no_data.get(target.name, []),
            }
            for target in TARGETS
        ],
        "files": saved,
    }
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Collect R-ONE raw XML responses for project regions.")
    parser.add_argument("--start-ym", default="200501", help="Start month in YYYYMM format.")
    parser.add_argument("--end-ym", default="202512", help="End month in YYYYMM format.")
    parser.add_argument("--page-size", type=int, default=1000, help="Rows per request. R-ONE max is 1000.")
    parser.add_argument("--delay-seconds", type=float, default=0.05, help="Small delay between requests.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    start_ym = validate_ym(args.start_ym, "start_ym")
    end_ym = validate_ym(args.end_ym, "end_ym")
    if args.page_size < 1 or args.page_size > 1000:
        raise ValueError("page_size must be between 1 and 1000.")

    api_key = get_rone_api_key()
    all_saved = []
    no_data_by_target = {}
    for target in TARGETS:
        saved, no_data_months = collect_target(
            api_key=api_key,
            target=target,
            start_ym=start_ym,
            end_ym=end_ym,
            page_size=args.page_size,
            delay_seconds=args.delay_seconds,
        )
        all_saved.extend(saved)
        no_data_by_target[target.name] = no_data_months

    manifest_path = write_manifest(start_ym, end_ym, all_saved, no_data_by_target)
    print(f"Saved {len(all_saved):,} raw XML files under {RAW_DIR}")
    print(f"Saved manifest to {manifest_path}")


if __name__ == "__main__":
    main()
