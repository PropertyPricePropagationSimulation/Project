"""Verify MOLIT apartment trade API coverage for candidate LAWD_CD values."""

from __future__ import annotations

import os
import re
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen


ROOT_DIR = Path(__file__).resolve().parents[1]
ENV_PATH = ROOT_DIR / ".env"
API_URL = "https://apis.data.go.kr/1613000/RTMSDataSvcAptTradeDev/getRTMSDataSvcAptTradeDev"


def load_env_key(name: str) -> str:
    if ENV_PATH.exists():
        for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
            if not line.strip() or line.lstrip().startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            if key.strip() == name:
                return value.strip().strip('"').strip("'")
    return os.getenv(name, "")


def total_count(api_key: str, lawd_cd: str, deal_ymd: str) -> int | None:
    query = urlencode(
        {
            "serviceKey": api_key,
            "LAWD_CD": lawd_cd,
            "DEAL_YMD": deal_ymd,
            "pageNo": "1",
            "numOfRows": "10",
        },
        safe="%",
    )
    with urlopen(f"{API_URL}?{query}", timeout=20) as response:
        text = response.read().decode("utf-8", errors="replace")
    match = re.search(r"<totalCount>(\d+)</totalCount>", text)
    return int(match.group(1)) if match else None


def main() -> None:
    api_key = load_env_key("MOLIT_API_KEY") or load_env_key("molit.api.key")
    if not api_key:
        raise SystemExit("MOLIT_API_KEY is missing")

    candidates = {
        "suwon_parent": ["41110"],
        "suwon_wards": ["41111", "41113", "41115", "41117"],
        "seongnam_parent": ["41130"],
        "seongnam_wards": ["41131", "41133", "41135"],
        "anyang_parent": ["41170"],
        "anyang_wards": ["41171", "41173"],
        "bucheon_candidates": ["41190", "41192", "41194", "41196", "41195", "41197", "41199"],
        "ansan_parent": ["41270"],
        "ansan_wards": ["41271", "41273"],
        "goyang_parent": ["41280"],
        "goyang_wards": ["41281", "41285", "41287"],
        "yongin_parent": ["41460"],
        "yongin_wards": ["41461", "41463", "41465"],
        "gimpo": ["41570"],
        "hwaseong_candidates": ["41590", "41591", "41593", "41595"],
    }
    months = ["200601", "202401"]

    for label, codes in candidates.items():
        print(f"[{label}]")
        for code in codes:
            counts = []
            for month in months:
                try:
                    count = total_count(api_key, code, month)
                except Exception as exc:
                    counts.append(f"{month}=ERR:{exc.__class__.__name__}")
                else:
                    counts.append(f"{month}={count}")
            print(f"{code} " + " ".join(counts))


if __name__ == "__main__":
    main()
