"""Test DuckDB registration and querying of collected Parquet files."""

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.services.duckdb_service import register_parquet_files, get_connection, list_tables
from app.config import BASE_DIR

DB_PATH = BASE_DIR / "result" / "ssafy.duckdb"

def test_duckdb():
    """Register Parquet files and run sample queries."""
    print(f"DuckDB path: {DB_PATH}")
    print(f"Manifest path: {BASE_DIR / 'processed' / 'manifest.json'}")
    
    # Register Parquet files
    print("\n=== Registering Parquet files in DuckDB ===")
    result = register_parquet_files(str(DB_PATH))
    print(f"Registration status: {result['status']}")
    print(f"Registered views: {result.get('registered_count', 0)}")
    if result.get('errors'):
        print(f"Errors: {result['errors']}")
    
    # List tables
    print("\n=== DuckDB Tables ===")
    con = get_connection(str(DB_PATH))
    tables = list_tables(str(DB_PATH))
    for (table_name,) in tables:
        try:
            count = con.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
            print(f"  {table_name}: {count} rows")
        except Exception as e:
            print(f"  {table_name}: [error reading count - {e}]")
    
    # Sample query if houses table exists
    print("\n=== Sample Query ===")
    try:
        query_result = con.execute(
            "SELECT apt_name, deal_year, deal_month, deal_amount FROM houses LIMIT 5"
        ).fetchall()
        
        if query_result:
            print("Top 5 houses:")
            for row in query_result:
                print(f"  {row[0]}: {row[1]}-{row[2]} ₩{row[3]}")
        else:
            print("No data in houses table yet")
    except Exception as e:
        print(f"Query error: {e}")

if __name__ == "__main__":
    test_duckdb()
