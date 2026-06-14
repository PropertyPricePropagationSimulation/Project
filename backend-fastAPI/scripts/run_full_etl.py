"""Run full initial ETL to collect all regions (2000-present) and write to processed Parquet.

Usage:
  Activate virtualenv then:
    python run_full_etl.py

This will:
  1. Fetch legal dong codes for Seoul + metro cities via JUSO API
  2. Collect sale data from MOLIT API (2000-present)
  3. Write Parquet partitions under processed/
  4. Update manifest.json

WARNING: This script makes many API calls and may take significant time.
Requires .env with JUSO_API_KEY and MOLIT_API_KEY set.
"""

import asyncio
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.services import collector, etl
from app.config_regions import get_region_codes


async def run_full_collection():
    """Collect sale data for all target regions (2000-present)."""
    region_codes = get_region_codes()
    
    print(f"Collecting data for {len(region_codes)} regions (2000-present)...")
    print(f"Region codes: {region_codes}")
    
    # Determine year range: 2000 to current year
    import datetime
    current_year = datetime.datetime.now().year
    start_year = 2000
    
    total_periods = 0
    for region_code in region_codes:
        print(f"\n--- Collecting for region: {region_code} ---")
        try:
            result = await collector.collect_sale_data(
                start_year=start_year,
                end_year=current_year,
                region=region_code,
                save_raw=True,
                save_processed=True,
            )
            periods = result.get("periods", [])
            total_periods += len(periods)
            print(f"  Collected {len(periods)} periods, processed items saved to Parquet")
            for p in periods:
                if p.get("processed_path"):
                    print(f"    ✓ {p['deal_ym']}: {p.get('item_count', 0)} items → {p['processed_path']}")
                else:
                    print(f"    {p['deal_ym']}: {p.get('item_count', 0)} items (no processed path)")
        except Exception as exc:
            print(f"  ERROR collecting region {region_code}: {exc}")
            continue
    
    print(f"\n=== ETL Complete ===")
    print(f"Total periods collected: {total_periods}")
    print(f"Check processed/ for Parquet files and manifest.json for metadata")


if __name__ == "__main__":
    asyncio.run(run_full_collection())
