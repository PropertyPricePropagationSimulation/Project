import json
import re
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List

import duckdb
import pandas as pd

from app.config import BASE_DIR
from app.services import etl

RAW_DIR = BASE_DIR / "raw"
PROCESSED_DIR = BASE_DIR / "processed"
SUMMARY_DIR = PROCESSED_DIR / "monthly_summary"
SUMMARY_DIR.mkdir(parents=True, exist_ok=True)


FIELD_ALIASES = {
    "apt_name": ["aptNm", "APT_NAME", "아파트", "아파트명", "건물명"],
    "sido_name": ["sido", "SIDO", "시도"],
    "gugun_name": ["sggNm", "gugun", "GUGUN", "시군구"],
    "dong_name": ["umdNm", "dong", "DONG", "법정동", "법정동명"],
    "jibun": ["jibun", "JIBUN", "번지", "지번"],
    "road_name": ["roadNm", "ROAD", "도로명"],
    "build_year": ["buildYear", "BUILD_YEAR", "건축년도"],
    "floor": ["floor", "FLOOR", "층"],
    "deal_amount": ["dealAmount", "DEAL_AMOUNT", "거래금액"],
    "exclu_use_ar": ["excluUseAr", "EXCLU_USE_AR", "전용면적"],
    "deal_year": ["dealYear", "DEAL_YEAR", "년"],
    "deal_month": ["dealMonth", "DEAL_MONTH", "월"],
    "deal_day": ["dealDay", "DEAL_DAY", "일", "일자"],
    "deal_type": ["dealingGbn", "DEALING_GBN", "거래유형"],
    "cancel_type": ["cdealType", "cancelDealType", "해제여부"],
    "cancel_date": ["cdealDay", "cancelDealDay", "해제사유발생일"],
}


def _first_value(row: Dict[str, Any], aliases: List[str]) -> Any:
    for key in aliases:
        value = row.get(key)
        if value is not None and str(value).strip() != "":
            return value
    return None


def _to_int(value: Any) -> int | None:
    if value is None:
        return None
    text = re.sub(r"[^0-9-]", "", str(value))
    if text in {"", "-"}:
        return None
    return int(text)


def _to_float(value: Any) -> float | None:
    if value is None:
        return None
    text = str(value).replace(",", "").strip()
    if text == "":
        return None
    try:
        return float(text)
    except ValueError:
        return None


def _parse_meta(path: Path) -> Dict[str, Any]:
    meta_path = path.with_suffix(path.suffix + ".meta.json")
    if not meta_path.exists():
        return {}
    try:
        return json.loads(meta_path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _extract_region_from_name(path: Path) -> str | None:
    match = re.search(r"sale_data_(\d+)_(\d{6})_p\d+", path.stem)
    if match:
        return match.group(1)
    return None


def _extract_deal_ym_from_name(path: Path) -> str | None:
    match = re.search(r"sale_data_(\d+)_(\d{6})_p\d+", path.stem)
    if match:
        return match.group(2)
    return None


def _raw_xml_files(raw_dir: Path = RAW_DIR) -> Iterable[Path]:
    if not raw_dir.exists():
        return []
    return sorted(
        path for path in raw_dir.glob("sale_data_*.xml")
        if not path.name.startswith("failed_")
    )


def _parse_items(path: Path) -> List[Dict[str, Any]]:
    root = ET.fromstring(path.read_text(encoding="utf-8"))
    rows = []
    for item in root.findall(".//item"):
        rows.append({child.tag: child.text for child in item})
    return rows


def _normalize_row(row: Dict[str, Any], path: Path) -> Dict[str, Any]:
    meta = _parse_meta(path)
    params = meta.get("params", {})
    deal_ym = str(params.get("DEAL_YMD") or _extract_deal_ym_from_name(path) or "")
    region = str(params.get("LAWD_CD") or _extract_region_from_name(path) or "")

    deal_year = _to_int(_first_value(row, FIELD_ALIASES["deal_year"]))
    deal_month = _to_int(_first_value(row, FIELD_ALIASES["deal_month"]))
    deal_day = _to_int(_first_value(row, FIELD_ALIASES["deal_day"]))
    if deal_ym and len(deal_ym) == 6:
        deal_year = deal_year or int(deal_ym[:4])
        deal_month = deal_month or int(deal_ym[4:6])

    contract_date = None
    if deal_year and deal_month and deal_day:
        try:
            contract_date = datetime(deal_year, deal_month, deal_day).date().isoformat()
        except ValueError:
            contract_date = None

    deal_amount = _to_int(_first_value(row, FIELD_ALIASES["deal_amount"]))
    area = _to_float(_first_value(row, FIELD_ALIASES["exclu_use_ar"]))
    price_per_sqm = None
    if deal_amount is not None and area and area > 0:
        price_per_sqm = round(deal_amount / area, 4)

    deal_type = str(_first_value(row, FIELD_ALIASES["deal_type"]) or "")
    cancel_type = str(_first_value(row, FIELD_ALIASES["cancel_type"]) or "")
    cancel_date = _first_value(row, FIELD_ALIASES["cancel_date"])
    is_cancelled = bool(cancel_date) or cancel_type not in {"", "0", "N", "n", "정상"}
    is_direct_trade = "직거래" in deal_type
    is_special_trade = is_direct_trade

    return {
        "apt_name": _first_value(row, FIELD_ALIASES["apt_name"]),
        "sido_name": _first_value(row, FIELD_ALIASES["sido_name"]),
        "gugun_name": _first_value(row, FIELD_ALIASES["gugun_name"]),
        "dong_name": _first_value(row, FIELD_ALIASES["dong_name"]),
        "dong_code": region,
        "jibun": _first_value(row, FIELD_ALIASES["jibun"]),
        "road_name": _first_value(row, FIELD_ALIASES["road_name"]),
        "build_year": _to_int(_first_value(row, FIELD_ALIASES["build_year"])),
        "floor": _to_int(_first_value(row, FIELD_ALIASES["floor"])),
        "deal_year": deal_year,
        "deal_month": deal_month,
        "deal_day": deal_day,
        "contract_date": contract_date,
        "estimated_contract_date": contract_date,
        "date_uncertainty_days": 30 if contract_date else None,
        "deal_amount": deal_amount,
        "exclu_use_ar": area,
        "price_per_sqm": price_per_sqm,
        "deal_type": deal_type or None,
        "cancel_type": cancel_type or None,
        "cancel_date": str(cancel_date) if cancel_date else None,
        "is_cancelled": is_cancelled,
        "is_direct_trade": is_direct_trade,
        "is_special_trade": is_special_trade,
        "source_raw_file": path.name,
        "preprocessed_at": datetime.utcnow().isoformat(),
    }


def _drop_outliers(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty or "price_per_sqm" not in df.columns:
        return df

    keep_parts = []
    group_cols = ["dong_code", "deal_year", "deal_month"]
    for _, group in df.groupby(group_cols, dropna=False):
        comparable = group[~group["is_special_trade"].fillna(False)]
        special = group[group["is_special_trade"].fillna(False)]
        if len(comparable) < 20:
            keep_parts.append(group.assign(is_outlier=False))
            continue

        low = comparable["price_per_sqm"].quantile(0.01)
        high = comparable["price_per_sqm"].quantile(0.99)
        comparable = comparable.assign(
            is_outlier=(comparable["price_per_sqm"] < low) | (comparable["price_per_sqm"] > high)
        )
        special = special.assign(is_outlier=False)
        keep_parts.append(pd.concat([comparable, special], ignore_index=True))

    return pd.concat(keep_parts, ignore_index=True) if keep_parts else df


def _monthly_summary(df: pd.DataFrame, min_deal_count: int) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()

    analysis_df = df[
        (~df["is_cancelled"].fillna(False))
        & (~df["is_outlier"].fillna(False))
        & df["deal_amount"].notna()
        & df["exclu_use_ar"].notna()
    ].copy()
    if analysis_df.empty:
        return pd.DataFrame()

    summary = (
        analysis_df.groupby(["dong_code", "deal_year", "deal_month"], dropna=False)
        .agg(
            deal_count=("deal_amount", "size"),
            avg_deal_amount=("deal_amount", "mean"),
            median_deal_amount=("deal_amount", "median"),
            avg_price_per_sqm=("price_per_sqm", "mean"),
            min_price_per_sqm=("price_per_sqm", "min"),
            max_price_per_sqm=("price_per_sqm", "max"),
        )
        .reset_index()
    )
    summary["is_low_volume"] = summary["deal_count"] < min_deal_count
    summary["year_month"] = summary["deal_year"].astype(int).astype(str) + summary["deal_month"].astype(int).astype(str).str.zfill(2)
    summary["created_at"] = datetime.utcnow().isoformat()
    return summary


def _write_summary_parquet(summary: pd.DataFrame) -> str | None:
    if summary.empty:
        return None
    path = SUMMARY_DIR / "house_monthly_summary.parquet"
    duckdb.from_df(summary).to_parquet(str(path))
    return str(path)


def _write_cleaned_partitions(df: pd.DataFrame) -> List[Dict[str, Any]]:
    written = []
    if df.empty:
        return written

    for (year, month, dong), group in df.groupby(["deal_year", "deal_month", "dong_code"], dropna=False):
        if pd.isna(year) or pd.isna(month) or not dong:
            continue
        path = etl.write_parquet_from_df(group, int(year), int(month), str(dong))
        entry = {
            "path": str(path.relative_to(etl.PROCESSED_DIR)),
            "year": int(year),
            "month": int(month),
            "dong_code": str(dong),
            "rows": len(group),
            "pipeline": "G2",
            "created_at": datetime.utcnow().isoformat(),
        }
        etl.update_manifest(entry)
        written.append({**entry, "full_path": str(path)})
    return written


def run_preprocess(
    min_deal_count: int = 3,
    save_cleaned: bool = True,
    save_summary: bool = True,
) -> Dict[str, Any]:
    raw_files = list(_raw_xml_files())
    rows = []
    errors = []

    for path in raw_files:
        try:
            for item in _parse_items(path):
                rows.append(_normalize_row(item, path))
        except Exception as exc:
            errors.append({"file": path.name, "error": str(exc)})

    if not rows:
        return {
            "status": "no_data",
            "raw_files": len(raw_files),
            "rows": 0,
            "errors": errors,
            "message": "No successful sale_data_*.xml raw files were available to preprocess.",
        }

    df = pd.DataFrame(rows)
    before_cancel_filter = len(df)
    df = df[~df["is_cancelled"].fillna(False)].copy()
    cancelled_count = before_cancel_filter - len(df)
    df = _drop_outliers(df)
    outlier_count = int(df["is_outlier"].fillna(False).sum()) if "is_outlier" in df.columns else 0
    cleaned_df = df[~df["is_outlier"].fillna(False)].copy()

    written = _write_cleaned_partitions(cleaned_df) if save_cleaned else []
    summary_df = _monthly_summary(cleaned_df, min_deal_count=min_deal_count)
    summary_path = _write_summary_parquet(summary_df) if save_summary else None

    return {
        "status": "success",
        "raw_files": len(raw_files),
        "input_rows": len(rows),
        "cancelled_removed": cancelled_count,
        "outliers_removed": outlier_count,
        "cleaned_rows": len(cleaned_df),
        "monthly_summary_rows": len(summary_df),
        "monthly_summary_path": summary_path,
        "written_partitions": written,
        "errors": errors,
    }


def get_preprocess_status() -> Dict[str, Any]:
    raw_files = list(_raw_xml_files())
    manifest_path = etl.PROCESSED_DIR / "manifest.json"
    summary_path = SUMMARY_DIR / "house_monthly_summary.parquet"
    return {
        "status": "ready",
        "raw_success_files": len(raw_files),
        "processed_dir": str(PROCESSED_DIR),
        "manifest_exists": manifest_path.exists(),
        "monthly_summary_exists": summary_path.exists(),
    }
