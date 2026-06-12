from pathlib import Path
import duckdb
import logging

logger = logging.getLogger(__name__)

# Default DB file under project `result/` directory
DEFAULT_DB = Path(__file__).resolve().parents[2] / "result" / "ssafy.duckdb"
SUMMARY_TABLE = "house_monthly_summary"
SUMMARY_COLUMNS = [
    "dong_code",
    "deal_year",
    "deal_month",
    "deal_count",
    "avg_deal_amount",
    "median_deal_amount",
    "avg_price_per_sqm",
    "min_price_per_sqm",
    "max_price_per_sqm",
    "is_low_volume",
    "year_month",
]
EVENT_COLUMNS = {
    "id",
    "name",
    "event_type",
    "event_date",
    "event_ym",
    "source",
    "description",
}


def _quote_identifier(identifier: str) -> str:
    return '"' + identifier.replace('"', '""') + '"'


def _drop_legacy_houses_objects(con: duckdb.DuckDBPyConnection) -> list[str]:
    """Remove old per-transaction tables/views from previous DB registrations."""
    dropped = []
    legacy_views = con.execute(
        """
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'main'
          AND table_type = 'VIEW'
          AND (table_name = 'houses_union' OR table_name LIKE 'houses_%')
        """
    ).fetchall()

    for (view_name,) in legacy_views:
        con.execute(f"DROP VIEW IF EXISTS {_quote_identifier(view_name)}")
        dropped.append(view_name)

    legacy_tables = con.execute(
        """
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'main'
          AND table_type = 'BASE TABLE'
          AND table_name = 'houses'
        """
    ).fetchall()

    for (table_name,) in legacy_tables:
        con.execute(f"DROP TABLE IF EXISTS {_quote_identifier(table_name)}")
        dropped.append(table_name)

    return dropped


def _table_exists(con: duckdb.DuckDBPyConnection, table_name: str) -> bool:
    return bool(
        con.execute(
            """
            SELECT 1
            FROM information_schema.tables
            WHERE table_schema = 'main'
              AND table_name = ?
            """,
            [table_name],
        ).fetchone()
    )


def _table_columns(con: duckdb.DuckDBPyConnection, table_name: str) -> set[str]:
    return {
        column_name
        for (column_name,) in con.execute(
            """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = 'main'
              AND table_name = ?
            """,
            [table_name],
        ).fetchall()
    }


def _create_events_table(con: duckdb.DuckDBPyConnection) -> None:
    con.execute(
        """
        CREATE TABLE IF NOT EXISTS events(
            id INTEGER PRIMARY KEY,
            name VARCHAR NOT NULL,
            event_type VARCHAR NOT NULL,
            event_date DATE NOT NULL,
            event_ym VARCHAR NOT NULL,
            source VARCHAR,
            description VARCHAR
        )
        """
    )


def _ensure_events_schema(con: duckdb.DuckDBPyConnection) -> None:
    if not _table_exists(con, "events"):
        _create_events_table(con)
        return

    existing_columns = _table_columns(con, "events")
    if EVENT_COLUMNS.issubset(existing_columns):
        return

    row_count = con.execute("SELECT COUNT(*) FROM events").fetchone()[0]
    if row_count == 0:
        con.execute("DROP TABLE events")
        _create_events_table(con)
        return

    if "event_ym" not in existing_columns:
        con.execute("ALTER TABLE events ADD COLUMN event_ym VARCHAR")
        con.execute("UPDATE events SET event_ym = strftime(event_date, '%Y%m')")
        con.execute("ALTER TABLE events ALTER COLUMN event_ym SET NOT NULL")
    if "source" not in existing_columns:
        con.execute("ALTER TABLE events ADD COLUMN source VARCHAR")
    if "description" not in existing_columns:
        con.execute("ALTER TABLE events ADD COLUMN description VARCHAR")


def _create_event_detail_tables(con: duckdb.DuckDBPyConnection) -> None:
    con.execute(
        """
        CREATE TABLE IF NOT EXISTS base_rate_event_details(
            event_id INTEGER PRIMARY KEY,
            previous_rate DOUBLE NOT NULL,
            new_rate DOUBLE NOT NULL,
            delta DOUBLE NOT NULL,
            direction VARCHAR NOT NULL,
            previous_observed_date DATE,
            stat_code VARCHAR,
            item_code VARCHAR,
            item_name VARCHAR,
            FOREIGN KEY(event_id) REFERENCES events(id)
        )
        """
    )
    con.execute(
        """
        CREATE TABLE IF NOT EXISTS policy_event_details(
            event_id INTEGER PRIMARY KEY,
            policy_category VARCHAR,
            policy_direction VARCHAR,
            target_region VARCHAR,
            affected_asset VARCHAR,
            announced_date DATE,
            effective_date DATE,
            source_url VARCHAR,
            FOREIGN KEY(event_id) REFERENCES events(id)
        )
        """
    )


def get_connection(db_path: Path | str | None = None) -> duckdb.DuckDBPyConnection:
    """Return a DuckDB connection to the given path (file-backed)."""
    path = Path(db_path) if db_path else DEFAULT_DB
    path.parent.mkdir(parents=True, exist_ok=True)
    # duckdb.connect accepts a path string; using file-backed DB so data persists
    return duckdb.connect(str(path))


def init_schema(db_path: Path | str | None = None) -> None:
    """Create DuckDB-managed application tables."""
    con = get_connection(db_path)
    con.execute(
        """
        CREATE TABLE IF NOT EXISTS house_monthly_summary(
            dong_code VARCHAR,
            deal_year BIGINT,
            deal_month BIGINT,
            deal_count BIGINT,
            avg_deal_amount DOUBLE,
            median_deal_amount DOUBLE,
            avg_price_per_sqm DOUBLE,
            min_price_per_sqm DOUBLE,
            max_price_per_sqm DOUBLE,
            is_low_volume BOOLEAN,
            year_month VARCHAR
        )
        """
    )
    _ensure_events_schema(con)
    _create_event_detail_tables(con)


def init_sample(db_path: Path | str | None = None) -> None:
    """Create DuckDB application schema."""
    init_schema(db_path)


def register_parquet_files(db_path: Path | str | None = None) -> dict:
    """Register the monthly summary Parquet file in DuckDB.

    The application DB is expected to expose region/month aggregate trade
    information, not the cleaned per-transaction partitions.
    """
    con = get_connection(db_path)
    db_path = Path(db_path) if db_path else DEFAULT_DB

    summary_path = db_path.parents[1] / "processed" / "monthly_summary" / "house_monthly_summary.parquet"
    if not summary_path.exists():
        logger.warning("Monthly summary not found at %s, skipping registration", summary_path)
        return {"status": "skipped", "reason": "house_monthly_summary.parquet not found"}

    dropped_legacy_objects = _drop_legacy_houses_objects(con)
    path_for_sql = summary_path.resolve().as_posix()
    selected_columns = ", ".join(SUMMARY_COLUMNS)
    con.execute(
        f"""
        CREATE OR REPLACE TABLE {SUMMARY_TABLE} AS
        SELECT {selected_columns}
        FROM read_parquet('{path_for_sql}')
        """
    )

    record_count = con.execute(f"SELECT COUNT(*) FROM {SUMMARY_TABLE}").fetchone()[0]
    return {
        "status": "completed",
        "registered_count": 1,
        "registered": [
            {
                "type": "materialized_table",
                "name": SUMMARY_TABLE,
                "path": "processed/monthly_summary/house_monthly_summary.parquet",
                "full_path": path_for_sql,
                "columns": SUMMARY_COLUMNS,
                "record_count": record_count,
            }
        ],
        "dropped_legacy_objects": dropped_legacy_objects,
        "errors": [],
    }


def list_tables(db_path: Path | str | None = None):
    con = get_connection(db_path)
    return con.execute(
        "SELECT table_name, table_type FROM information_schema.tables WHERE table_schema='main' ORDER BY table_type, table_name"
    ).fetchall()


def query(sql: str, db_path: Path | str | None = None):
    con = get_connection(db_path)
    return con.execute(sql).fetchall()

