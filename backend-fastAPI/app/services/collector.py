import asyncio
import json
import random
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import httpx
import pandas as pd

from app.config import settings
from app.services import etl

RAW_DIR = settings.raw_base_dir
RAW_DIR.mkdir(parents=True, exist_ok=True)


class ApiRateLimitError(RuntimeError):
    """Raised when an external API keeps returning 429 after retries."""


def _build_raw_path(name: str, suffix: str) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
    return RAW_DIR / f"{name}_{timestamp}.{suffix}"


def _redact_params(params: Dict[str, Any]) -> Dict[str, Any]:
    secret_keys = {"servicekey", "confmkey", "apikey", "authkey"}
    return {
        key: "***REDACTED***" if key.lower() in secret_keys else value
        for key, value in params.items()
    }


def _redact_url(url: str) -> str:
    redacted_url = url
    for secret in [settings.molit_api_key, settings.juso_api_key, settings.ecos_api_key, settings.rone_api_key]:
        if secret:
            redacted_url = redacted_url.replace(secret, "***REDACTED***")

    parts = urlsplit(redacted_url)
    query = urlencode(_redact_params(dict(parse_qsl(parts.query))), doseq=True)
    return urlunsplit((parts.scheme, parts.netloc, parts.path, query, parts.fragment))


def _save_raw_payload(name: str, params: Dict[str, Any], response_text: str, suffix: str) -> str:
    raw_path = _build_raw_path(name, suffix)
    raw_path.write_text(response_text, encoding="utf-8")

    meta_path = raw_path.with_suffix(raw_path.suffix + ".meta.json")
    meta = {
        "saved_at": datetime.now().isoformat(),
        "raw_file": raw_path.name,
        "params": _redact_params(params),
    }
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    return str(raw_path)


def _safe_raw_name(value: str) -> str:
    return "".join(ch if ch.isalnum() else "_" for ch in value).strip("_") or "unknown"


def _save_failed_response(params: Dict[str, Any], response: httpx.Response) -> str:
    prefix = "failed_response"
    suffix = "txt"
    if "DEAL_YMD" in params:
        prefix = f"failed_sale_data_{params.get('LAWD_CD', 'unknown')}_{params.get('DEAL_YMD')}_p{params.get('pageNo', 1)}"
        suffix = "xml"
    elif "currentPage" in params:
        prefix = "failed_legal_dong_code"
        suffix = "json"

    raw_path = _build_raw_path(prefix, suffix)
    raw_path.write_text(response.text, encoding="utf-8")

    meta_path = raw_path.with_suffix(raw_path.suffix + ".meta.json")
    meta = {
        "saved_at": datetime.now().isoformat(),
        "raw_file": raw_path.name,
        "status_code": response.status_code,
        "reason_phrase": response.reason_phrase,
        "url": _redact_url(str(response.request.url)),
        "params": _redact_params(params),
    }
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    return str(raw_path)


def _validate_ym(value: str | int, field_name: str) -> str:
    ym = str(value)
    if len(ym) != 6 or not ym.isdigit():
        raise ValueError(f"{field_name} must be YYYYMM format.")
    month = int(ym[4:6])
    if month < 1 or month > 12:
        raise ValueError(f"{field_name} has invalid month.")
    return ym


def _iter_months(start_ym: str | int, end_ym: str | int) -> Iterable[str]:
    start = _validate_ym(start_ym, "start_ym")
    end = _validate_ym(end_ym, "end_ym")

    start_index = int(start[:4]) * 12 + int(start[4:6])
    end_index = int(end[:4]) * 12 + int(end[4:6])
    if start_index > end_index:
        raise ValueError("start_ym must be earlier than or equal to end_ym.")

    for index in range(start_index, end_index + 1):
        year = (index - 1) // 12
        month = (index - 1) % 12 + 1
        yield f"{year}{month:02d}"


def _parse_molit_xml(text: str) -> Dict[str, Any]:
    root = ET.fromstring(text)
    items = []
    for item in root.findall(".//item"):
        items.append({child.tag: child.text for child in item})

    total_count = None
    total_count_node = root.find(".//totalCount")
    if total_count_node is not None:
        total_count = int(total_count_node.text or 0)

    return {"total_count": total_count, "items": items}


def _extract_juso_rows(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    results = data.get("results", {})
    juso = results.get("juso", [])
    if isinstance(juso, list):
        return juso
    return []


def _normalize_house_item(item: Dict[str, Any], deal_ym: str, region: str) -> Dict[str, Any]:
    def val(*keys: str):
        for key in keys:
            if key in item and item[key] is not None:
                return item[key]
        return None

    year = int(deal_ym[:4])
    month = int(deal_ym[4:6])
    return {
        "no": None,
        "apt_seq": None,
        "apt_name": val("아파트", "APT_NAME", "aptNm", "건물명"),
        "sido_name": val("시도", "sido", "SIDO"),
        "gugun_name": val("시군구", "gugun", "GUGUN"),
        "dong_name": val("법정동", "법정동명", "dong", "DONG"),
        "dong_code": region,
        "jibun": val("번지", "지번", "JIBUN"),
        "road_name": val("도로명", "ROAD"),
        "build_year": val("건축년도", "BUILD_YEAR"),
        "latitude": None,
        "longitude": None,
        "apt_dong": val("아파트동", "aptDong", "AptDong"),
        "floor": val("층", "FLOOR"),
        "deal_year": year,
        "deal_month": month,
        "deal_day": val("일", "DEAL_DAY", "일자"),
        "exclu_use_ar": val("전용면적", "EXCLU_USE_AR"),
        "deal_amount": val("거래금액", "DEAL_AMOUNT"),
    }


async def _http_get_with_retry(
    client: httpx.AsyncClient,
    url: str,
    params: Dict[str, Any],
    max_retries: int | None = None,
    backoff_base: float | None = None,
) -> httpx.Response:
    max_retries = settings.molit_max_retries if max_retries is None else max_retries
    backoff_base = settings.molit_retry_backoff_base_seconds if backoff_base is None else backoff_base

    def retry_after_delay(response: httpx.Response) -> float | None:
        retry_after = response.headers.get("Retry-After")
        if not retry_after:
            return None
        try:
            return min(float(retry_after), settings.molit_retry_after_max_seconds)
        except ValueError:
            return None

    def retry_delay(attempt: int, response: httpx.Response | None = None) -> float:
        header_delay = retry_after_delay(response) if response is not None else None
        if header_delay is not None:
            return header_delay
        delay = min(backoff_base * (2**attempt), settings.molit_retry_backoff_max_seconds)
        return delay + random.uniform(0, 0.5)

    for attempt in range(max_retries + 1):
        try:
            if settings.molit_request_delay_seconds > 0:
                await asyncio.sleep(settings.molit_request_delay_seconds)

            response = await client.get(url, params=params)
            if response.status_code == 429 or response.status_code >= 500:
                if attempt < max_retries:
                    await asyncio.sleep(retry_delay(attempt, response))
                    continue
                failed_raw_path = _save_failed_response(params, response)
                if response.status_code == 429:
                    raise ApiRateLimitError(
                        "External API returned 429 Too Many Requests after retries. "
                        f"Failure response was saved to {failed_raw_path}."
                    )
            response.raise_for_status()
            return response
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 429:
                if attempt < max_retries:
                    await asyncio.sleep(retry_delay(attempt, exc.response))
                    continue
                failed_raw_path = _save_failed_response(params, exc.response)
                raise ApiRateLimitError(
                    "External API returned 429 Too Many Requests after retries. "
                    f"Failure response was saved to {failed_raw_path}. "
                    "Reduce the date/region range or wait for the provider quota window to reset."
                ) from exc
            _save_failed_response(params, exc.response)
            raise
        except httpx.RequestError:
            if attempt < max_retries:
                await asyncio.sleep(retry_delay(attempt))
                continue
            raise

    raise RuntimeError("HTTP retry loop ended unexpectedly.")


async def collect_legal_dong_code(region: str, page: int = 1, count_per_page: int = 100) -> Dict[str, Any]:
    if not settings.juso_api_key:
        raise ValueError("JUSO_API_KEY is not configured.")

    url = "https://www.juso.go.kr/addrlink/addrLinkApiJsonp.do"
    params = {
        "currentPage": page,
        "countPerPage": count_per_page,
        "keyword": region,
        "confmKey": settings.juso_api_key,
        "resultType": "json",
    }

    async with httpx.AsyncClient(timeout=30) as client:
        response = await _http_get_with_retry(client, url, params)
        data = response.json()

    raw_path = _save_raw_payload("legal_dong_code", params, response.text, "json")
    return {
        "region": region,
        "api_url": url,
        "saved_raw": raw_path,
        "result": data,
        "rows": _extract_juso_rows(data),
    }


async def resolve_region_codes(region_keyword: str) -> Dict[str, Any]:
    data = await collect_legal_dong_code(region_keyword)
    codes = []
    for row in data.get("rows", []):
        code = row.get("admCd") or row.get("법정동코드")
        if code:
            codes.append(str(code)[:5])

    unique_codes = sorted(set(codes))
    return {
        "keyword": region_keyword,
        "region_codes": unique_codes,
        "source": data,
    }


async def collect_ecos_raw(
    stat_code: str,
    cycle: str,
    start_time: str,
    end_time: str,
    item_code1: str | None = None,
    item_code2: str | None = None,
    item_code3: str | None = None,
    item_code4: str | None = None,
    start_count: int = 1,
    end_count: int = 100000,
    language: str = "kr",
    output_format: str = "json",
) -> Dict[str, Any]:
    """Collect an ECOS StatisticSearch response and store the original payload in raw/."""
    if not settings.ecos_api_key:
        raise ValueError("ECOS_API_KEY is not configured.")

    output_format = output_format.lower()
    if output_format not in {"json", "xml"}:
        raise ValueError("output_format must be json or xml.")

    path_parts = [
        settings.ecos_api_base_url.rstrip("/"),
        settings.ecos_api_key,
        output_format,
        language,
        str(start_count),
        str(end_count),
        stat_code,
        cycle,
        start_time,
        end_time,
    ]
    path_parts.extend(code for code in [item_code1, item_code2, item_code3, item_code4] if code)
    url = "/".join(path_parts)

    params = {
        "stat_code": stat_code,
        "cycle": cycle,
        "start_time": start_time,
        "end_time": end_time,
        "item_code1": item_code1,
        "item_code2": item_code2,
        "item_code3": item_code3,
        "item_code4": item_code4,
        "start_count": start_count,
        "end_count": end_count,
        "language": language,
        "output_format": output_format,
        "url": _redact_url(url),
    }

    async with httpx.AsyncClient(timeout=60) as client:
        response = await _http_get_with_retry(client, url, params={})

    raw_name = "_".join([
        "ecos",
        _safe_raw_name(stat_code),
        _safe_raw_name(cycle),
        _safe_raw_name(start_time),
        _safe_raw_name(end_time),
    ])
    raw_path = _save_raw_payload(raw_name, params, response.text, output_format)
    return {
        "status": "success",
        "source": "ECOS",
        "raw_path": raw_path,
        "status_code": response.status_code,
        "params": _redact_params(params),
    }


async def collect_rone_raw(params: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """Collect a configured R-ONE API response and store the original payload in raw/."""
    if not settings.rone_api_url:
        raise ValueError("RONE_API_URL is not configured.")

    request_params = dict(params or {})
    if settings.rone_api_key and not any(key.lower() in {"servicekey", "apikey", "authkey"} for key in request_params):
        request_params["serviceKey"] = settings.rone_api_key

    async with httpx.AsyncClient(timeout=60) as client:
        response = await _http_get_with_retry(client, settings.rone_api_url, request_params)

    content_type = response.headers.get("content-type", "").lower()
    suffix = "json" if "json" in content_type else "xml" if "xml" in content_type else "txt"
    raw_path = _save_raw_payload("rone", request_params, response.text, suffix)
    return {
        "status": "success",
        "source": "R-ONE",
        "raw_path": raw_path,
        "status_code": response.status_code,
        "params": _redact_params(request_params),
    }


async def collect_sale_data_for_period(
    start_ym: str | int,
    end_ym: str | int,
    region: str,
    save_raw: bool = True,
    save_processed: bool = True,
    skip_existing_processed: bool | None = None,
) -> Dict[str, Any]:
    if not settings.molit_api_key:
        raise ValueError("MOLIT_API_KEY is not configured.")
    if not region.isdigit():
        raise ValueError("region must be numeric LAWD_CD format.")

    summary = {
        "region": region,
        "start_ym": _validate_ym(start_ym, "start_ym"),
        "end_ym": _validate_ym(end_ym, "end_ym"),
        "periods": [],
    }
    skip_existing = settings.molit_skip_existing_processed if skip_existing_processed is None else skip_existing_processed

    async with httpx.AsyncClient(timeout=60) as client:
        for deal_ym in _iter_months(start_ym, end_ym):
            year = int(deal_ym[:4])
            month = int(deal_ym[4:6])
            processed_path = etl._partition_path(year, month, region)

            if save_processed and skip_existing and processed_path.exists():
                summary["periods"].append({
                    "deal_ym": deal_ym,
                    "status": "skipped_existing",
                    "page": None,
                    "item_count": None,
                    "total_count": None,
                    "raw_path": None,
                    "processed_path": str(processed_path),
                    })
                continue

            async def fetch_page(page_no: int) -> tuple[Dict[str, Any], List[Dict[str, Any]]]:
                params = {
                    "serviceKey": settings.molit_api_key,
                    "LAWD_CD": region,
                    "DEAL_YMD": deal_ym,
                    "pageNo": page_no,
                    "numOfRows": settings.molit_page_size,
                }
                response = await _http_get_with_retry(client, settings.molit_api_url, params)
                parsed = _parse_molit_xml(response.text)

                raw_path = None
                if save_raw:
                    raw_path = _save_raw_payload(
                        f"sale_data_{region}_{deal_ym}_p{page_no}",
                        params,
                        response.text,
                        "xml",
                    )

                items = parsed.get("items", [])
                page_summary = {
                    "deal_ym": deal_ym,
                    "status": "collected",
                    "page": page_no,
                    "item_count": len(items),
                    "total_count": parsed.get("total_count"),
                    "raw_path": raw_path,
                    "processed_path": None,
                }
                return page_summary, items

            first, first_items = await fetch_page(1)
            total_count = first.get("total_count") or 0
            if total_count == 0 and not first_items:
                first["status"] = "no_data"
                summary["periods"].append(first)
                continue

            summary["periods"].append(first)
            total_pages = (total_count + settings.molit_page_size - 1) // settings.molit_page_size
            all_items = list(first_items)

            for page_no in range(2, total_pages + 1):
                try:
                    page_summary, page_items = await fetch_page(page_no)
                    summary["periods"].append(page_summary)
                    all_items.extend(page_items)
                except Exception as exc:
                    summary["periods"].append({
                        "deal_ym": deal_ym,
                        "status": "error",
                        "page": page_no,
                        "error": str(exc),
                    })

            if save_processed and all_items:
                rows = [_normalize_house_item(item, deal_ym, region) for item in all_items]
                df = pd.DataFrame(rows)
                processed_path = etl.write_parquet_from_df(df, year, month, region)
                etl.update_manifest({
                    "path": str(processed_path.relative_to(etl.PROCESSED_DIR)),
                    "year": year,
                    "month": month,
                    "dong_code": region,
                    "rows": len(df),
                    "created_at": datetime.utcnow().isoformat(),
                })
                for period in summary["periods"]:
                    if period.get("deal_ym") == deal_ym and period.get("status") == "collected":
                        period["processed_path"] = str(processed_path)
                summary["periods"].append({
                    "deal_ym": deal_ym,
                    "status": "processed",
                    "page": None,
                    "item_count": len(all_items),
                    "total_count": total_count,
                    "raw_path": None,
                    "processed_path": str(processed_path),
                })

    return summary


async def collect_sale_data_for_regions(
    start_ym: str | int,
    end_ym: str | int,
    region_codes: List[str],
    save_raw: bool = True,
    save_processed: bool = True,
    skip_existing_processed: bool | None = None,
) -> Dict[str, Any]:
    if not region_codes:
        raise ValueError("region_codes must not be empty.")

    summary = {
        "start_ym": _validate_ym(start_ym, "start_ym"),
        "end_ym": _validate_ym(end_ym, "end_ym"),
        "regions": region_codes,
        "results": [],
    }
    for region_code in region_codes:
        try:
            result = await collect_sale_data_for_period(
                start_ym=start_ym,
                end_ym=end_ym,
                region=region_code,
                save_raw=save_raw,
                save_processed=save_processed,
                skip_existing_processed=skip_existing_processed,
            )
            summary["results"].append({
                "region": region_code,
                "status": "success",
                "periods_collected": len(result.get("periods", [])),
                "detail": result.get("periods", []),
            })
        except Exception as exc:
            if isinstance(exc, ApiRateLimitError):
                summary["results"].append({
                    "region": region_code,
                    "status": "rate_limited",
                    "error": str(exc),
                })
                summary["status"] = "rate_limited"
                break

            summary["results"].append({
                "region": region_code,
                "status": "error",
                "error": str(exc),
            })
    return summary


async def collect_sale_data(
    start_year: int,
    end_year: int,
    region: str,
    save_raw: bool = True,
    save_processed: bool = True,
    skip_existing_processed: bool | None = None,
) -> Dict[str, Any]:
    return await collect_sale_data_for_period(
        start_ym=f"{start_year}01",
        end_ym=f"{end_year}12",
        region=region,
        save_raw=save_raw,
        save_processed=save_processed,
        skip_existing_processed=skip_existing_processed,
    )
