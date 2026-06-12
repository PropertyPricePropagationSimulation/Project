from dataclasses import dataclass
from pathlib import Path
import os

from dotenv import load_dotenv

# Project root directory
BASE_DIR = Path(__file__).resolve().parents[1]

load_dotenv(dotenv_path=BASE_DIR / ".env")


@dataclass(frozen=True)
class Settings:
    juso_api_key: str | None = os.getenv("JUSO_API_KEY")
    molit_api_key: str | None = os.getenv("MOLIT_API_KEY")
    ecos_api_key: str | None = os.getenv("ECOS_API_KEY", os.getenv("ecos.api.key"))
    molit_api_url: str = os.getenv(
        "MOLIT_API_URL",
        os.getenv(
            "MOLT_API_URL",
            "https://apis.data.go.kr/1613000/RTMSDataSvcAptTradeDev/getRTMSDataSvcAptTradeDev",
        ),
    )
    molit_region_codes: str | None = os.getenv("MOLIT_REGION_CODES", os.getenv("MOLT_REGION_CODES"))
    molit_deal_ym: str | None = os.getenv("MOLIT_DEAL_YM", os.getenv("MOLT_DEAL_YM"))
    molit_request_delay_seconds: float = float(os.getenv("MOLIT_REQUEST_DELAY_SECONDS", "3"))
    molit_max_retries: int = int(os.getenv("MOLIT_MAX_RETRIES", "10"))
    molit_retry_backoff_base_seconds: float = float(os.getenv("MOLIT_RETRY_BACKOFF_BASE_SECONDS", "5"))
    molit_retry_backoff_max_seconds: float = float(os.getenv("MOLIT_RETRY_BACKOFF_MAX_SECONDS", "300"))
    molit_retry_after_max_seconds: float = float(os.getenv("MOLIT_RETRY_AFTER_MAX_SECONDS", "600"))
    molit_page_size: int = int(os.getenv("MOLIT_PAGE_SIZE", "1000"))
    molit_skip_existing_processed: bool = os.getenv("MOLIT_SKIP_EXISTING_PROCESSED", "true").lower() == "true"
    ecos_api_base_url: str = os.getenv("ECOS_API_BASE_URL", "https://ecos.bok.or.kr/api/StatisticSearch")
    ecos_stat_targets: str | None = os.getenv("ECOS_STAT_TARGETS")
    ecos_search_start_date: str | None = os.getenv("ECOS_SEARCH_START_DATE")
    ecos_search_end_date: str | None = os.getenv("ECOS_SEARCH_END_DATE")
    rone_api_url: str | None = os.getenv("RONE_API_URL")
    rone_api_key: str | None = os.getenv("RONE_API_KEY", os.getenv("rone.api.key"))
    raw_base_dir: Path = Path(__file__).resolve().parents[1] / "raw"


settings = Settings()
