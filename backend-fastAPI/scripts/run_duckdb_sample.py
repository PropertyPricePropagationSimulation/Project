"""Run a quick DuckDB sample to initialize a DB and run a simple query.

Usage:
  Activate virtualenv (backend-fastAPI/.venv) then run:
    python run_duckdb_sample.py

This prints created tables and sample rows.
"""

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.services import duckdb_service


def main():
    print("Initializing sample DuckDB database (result/ssafy.duckdb)...")
    duckdb_service.init_sample()

    tables = duckdb_service.list_tables()
    print("Tables:", tables)

    rows = duckdb_service.query("SELECT * FROM houses")
    print("Rows:")
    for r in rows:
        print(r)


if __name__ == "__main__":
    main()
