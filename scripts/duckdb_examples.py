"""Run example DuckDB queries against the imported `sale_raw` table.

Usage:
    python scripts/duckdb_examples.py --duckdb-file ssafy.duckdb --table sale_raw

Prints:
 - Recent 10 records by `saved_at_ts`
 - Top 10 deals by numeric `DEAL_AMOUNT`
 - Monthly summary (count and avg amount) for recent months
 - Counts per `LAWD_CD`
 - Top apartments by number of records
"""
import argparse
from pathlib import Path
import duckdb
import pandas as pd


def run_examples(duckdb_file: Path, table: str = "sale_raw"):
    conn = duckdb.connect(database=str(duckdb_file), read_only=True)

    # Helper to run and pretty-print
    def qdf(sql: str):
        try:
            return conn.execute(sql).df()
        except Exception as e:
            print(f"Query failed: {e}")
            return pd.DataFrame()

    print("\n-- Recent 10 records (by saved_at_ts) --")
    sql_recent = f"""
    SELECT raw_file, LAWD_CD, DEAL_YMD, DEAL_DAY, APT_NAME, DONG, DEAL_AMOUNT, saved_at_ts
    FROM {table}
    ORDER BY saved_at_ts DESC NULLS LAST
    LIMIT 10
    """
    print(qdf(sql_recent).to_string(index=False))

    print("\n-- Top 10 deals by numeric DEAL_AMOUNT --")
    sql_top_amount = f"""
    SELECT raw_file, LAWD_CD, APT_NAME, DONG, DEAL_AMOUNT,
      CAST(NULLIF(REGEXP_REPLACE(DEAL_AMOUNT, '[^0-9]', ''), '') AS BIGINT) AS deal_amount_num
    FROM {table}
    WHERE DEAL_AMOUNT IS NOT NULL
    ORDER BY deal_amount_num DESC NULLS LAST
    LIMIT 10
    """
    print(qdf(sql_top_amount).to_string(index=False))

    print("\n-- Monthly summary (year/month) --")
    sql_monthly = f"""
    SELECT year, month, cnt, avg_amount
    FROM (
      SELECT SUBSTRING(DEAL_YMD,1,4) AS year, SUBSTRING(DEAL_YMD,5,2) AS month,
        COUNT(*) AS cnt,
        AVG(CAST(NULLIF(REGEXP_REPLACE(DEAL_AMOUNT, '[^0-9]', ''), '') AS DOUBLE)) AS avg_amount
      FROM {table}
      GROUP BY year, month
      ORDER BY year DESC, month DESC
    )
    LIMIT 12
    """
    print(qdf(sql_monthly).to_string(index=False))

    print("\n-- Counts per LAWD_CD (top 20) --")
    sql_counts = f"""
    SELECT LAWD_CD, COUNT(*) AS cnt
    FROM {table}
    GROUP BY LAWD_CD
    ORDER BY cnt DESC
    LIMIT 20
    """
    print(qdf(sql_counts).to_string(index=False))

    print("\n-- Top apartments by record count (top 20) --")
    sql_apt = f"""
    SELECT APT_NAME, COUNT(*) AS cnt
    FROM {table}
    GROUP BY APT_NAME
    ORDER BY cnt DESC
    LIMIT 20
    """
    print(qdf(sql_apt).to_string(index=False))

    conn.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--duckdb-file", default="ssafy.duckdb", help="DuckDB file to read from")
    parser.add_argument("--table", default="sale_raw", help="Table name to query")
    args = parser.parse_args()

    run_examples(Path(args.duckdb_file), table=args.table)


if __name__ == "__main__":
    main()
