"""Run the initial ETL to create processed/parquet files and manifest.

Usage:
  Activate virtualenv then:
    python run_etl.py
"""

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.services import etl


def main():
    print("Running initial ETL (sample mode)...")
    etl.run_initial_load(sample=True)
    print("ETL complete. Check backend-fastAPI/processed/ for output and manifest.json")


if __name__ == "__main__":
    main()
