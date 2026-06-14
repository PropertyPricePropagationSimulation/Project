"""Import preprocessed ECOS base-rate changes into DuckDB event tables."""
import argparse
import csv
from pathlib import Path
from typing import Any

from app.services.duckdb_service import DEFAULT_DB, get_connection, init_schema


DEFAULT_CSV = Path("processed") / "ecos" / "base_rate_changes_200501_202512.csv"
EVENT_TYPE = "base_rate"
SOURCE = "ECOS"


def _next_event_id(con: Any) -> int:
    current = con.execute("SELECT COALESCE(MAX(id), 0) FROM events").fetchone()[0]
    return int(current) + 1


def _event_exists(con: Any, row: dict[str, str]) -> bool:
    return bool(
        con.execute(
            """
            SELECT 1
            FROM events e
            JOIN base_rate_event_details d ON d.event_id = e.id
            WHERE e.event_type = ?
              AND e.event_date = CAST(? AS DATE)
              AND d.stat_code = ?
              AND d.item_code = ?
              AND d.new_rate = CAST(? AS DOUBLE)
              AND d.previous_rate = CAST(? AS DOUBLE)
            """,
            [
                EVENT_TYPE,
                row["event_date"],
                row["stat_code"],
                row["item_code"],
                row["new_rate"],
                row["previous_rate"],
            ],
        ).fetchone()
    )


def _direction_label(direction: str) -> str:
    if direction == "hike":
        return "인상"
    if direction == "cut":
        return "인하"
    return "변경"


def _format_rate(value: str) -> str:
    return f"{float(value):g}"


def _build_event_name(row: dict[str, str]) -> str:
    label = _direction_label(row["direction"])
    previous_rate = _format_rate(row["previous_rate"])
    new_rate = _format_rate(row["new_rate"])
    return f"{row['item_name']} {label} {previous_rate}% -> {new_rate}%"


def _build_description(row: dict[str, str]) -> str:
    label = _direction_label(row["direction"])
    previous_rate = _format_rate(row["previous_rate"])
    new_rate = _format_rate(row["new_rate"])
    delta = _format_rate(row["delta"])
    return f"{row['item_name']} {previous_rate}%에서 {new_rate}%로 {delta}%p {label}"


def import_base_rate_events(csv_path: Path, db_path: Path) -> dict[str, int]:
    init_schema(db_path)
    con = get_connection(db_path)

    imported = 0
    skipped = 0
    with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if _event_exists(con, row):
                skipped += 1
                continue

            event_id = _next_event_id(con)
            con.execute(
                """
                INSERT INTO events (
                    id,
                    name,
                    event_type,
                    event_date,
                    event_ym,
                    source,
                    description
                )
                VALUES (?, ?, ?, CAST(? AS DATE), ?, ?, ?)
                """,
                [
                    event_id,
                    _build_event_name(row),
                    EVENT_TYPE,
                    row["event_date"],
                    row["event_ym"],
                    SOURCE,
                    _build_description(row),
                ],
            )
            con.execute(
                """
                INSERT INTO base_rate_event_details (
                    event_id,
                    previous_rate,
                    new_rate,
                    delta,
                    direction,
                    previous_observed_date,
                    stat_code,
                    item_code,
                    item_name
                )
                VALUES (?, ?, ?, ?, ?, CAST(? AS DATE), ?, ?, ?)
                """,
                [
                    event_id,
                    row["previous_rate"],
                    row["new_rate"],
                    row["delta"],
                    row["direction"],
                    row["previous_observed_date"],
                    row["stat_code"],
                    row["item_code"],
                    row["item_name"],
                ],
            )
            imported += 1

    return {"imported": imported, "skipped": skipped}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", default=str(DEFAULT_CSV), help="Base-rate change CSV path")
    parser.add_argument("--db", default=str(DEFAULT_DB), help="DuckDB file path")
    args = parser.parse_args()

    csv_path = Path(args.csv)
    db_path = Path(args.db)
    result = import_base_rate_events(csv_path, db_path)
    print(f"Imported {result['imported']} base-rate events.")
    print(f"Skipped {result['skipped']} existing events.")
    print(f"DuckDB: {db_path}")


if __name__ == "__main__":
    main()
