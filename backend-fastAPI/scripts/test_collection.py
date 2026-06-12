"""Quick test of data collection - Seoul Gangnam only, 2023-2024."""

import sys
from pathlib import Path
import asyncio
from app.services import collector

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

async def test_collection():
    """Test collection for a single region (Seoul Gangnam: 11680) for recent years only."""
    print("Testing data collection for Seoul Gangnam (11680), 2023-2024...")
    
    try:
        result = await collector.collect_sale_data(
            start_year=2023,
            end_year=2024,
            region="11680",
            save_raw=True,
            save_processed=True,
        )
        
        print(f"\n✓ Collection successful!")
        print(f"  Periods: {len(result.get('periods', []))}")
        for period in result.get("periods", []):
            print(f"    {period['deal_ym']}: {period.get('item_count', 0)} items")
            if period.get("processed_path"):
                print(f"      → Saved to: {period['processed_path']}")
        
        return True
    except Exception as exc:
        print(f"✗ Error: {exc}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_collection())
    sys.exit(0 if success else 1)
