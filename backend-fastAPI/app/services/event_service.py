from typing import Any, Dict

from app.services.duckdb_service import get_connection, init_schema


def _row_to_event(row: tuple) -> Dict[str, Any]:
    event_id, name, event_type, event_date, event_ym, source, description = row
    return {
        "id": event_id,
        "name": name,
        "event_type": event_type,
        "event_date": event_date.isoformat() if hasattr(event_date, "isoformat") else str(event_date),
        "event_ym": event_ym,
        "source": source,
        "description": description,
    }


def _date_to_json(value: Any) -> str | None:
    if value is None:
        return None
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)


def _row_to_base_rate_detail(row: tuple | None) -> Dict[str, Any] | None:
    if row is None:
        return None

    (
        previous_rate,
        new_rate,
        delta,
        direction,
        previous_observed_date,
        stat_code,
        item_code,
        item_name,
    ) = row
    return {
        "previous_rate": previous_rate,
        "new_rate": new_rate,
        "delta": delta,
        "direction": direction,
        "previous_observed_date": _date_to_json(previous_observed_date),
        "stat_code": stat_code,
        "item_code": item_code,
        "item_name": item_name,
    }


def _row_to_policy_detail(row: tuple | None) -> Dict[str, Any] | None:
    if row is None:
        return None

    (
        policy_category,
        policy_direction,
        target_region,
        affected_asset,
        announced_date,
        effective_date,
        source_url,
    ) = row
    return {
        "policy_category": policy_category,
        "policy_direction": policy_direction,
        "target_region": target_region,
        "affected_asset": affected_asset,
        "announced_date": _date_to_json(announced_date),
        "effective_date": _date_to_json(effective_date),
        "source_url": source_url,
    }


def _event_detail(con: Any, event_id: int, event_type: str) -> Dict[str, Any] | None:
    if event_type == "base_rate":
        row = con.execute(
            """
            SELECT
                previous_rate,
                new_rate,
                delta,
                direction,
                previous_observed_date,
                stat_code,
                item_code,
                item_name
            FROM base_rate_event_details
            WHERE event_id = ?
            """,
            [event_id],
        ).fetchone()
        return _row_to_base_rate_detail(row)

    row = con.execute(
        """
        SELECT
            policy_category,
            policy_direction,
            target_region,
            affected_asset,
            announced_date,
            effective_date,
            source_url
        FROM policy_event_details
        WHERE event_id = ?
        """,
        [event_id],
    ).fetchone()
    return _row_to_policy_detail(row)


def _row_to_event_payload(con: Any, row: tuple, include_details: bool = True) -> Dict[str, Any]:
    event = _row_to_event(row)
    if include_details:
        event["detail"] = _event_detail(con, event["id"], event["event_type"])
    return event


def _event_ym(event_date: Any) -> str:
    if hasattr(event_date, "strftime"):
        return event_date.strftime("%Y%m")
    return str(event_date).replace("-", "")[:6]


def _next_event_id() -> int:
    con = get_connection()
    current = con.execute("SELECT COALESCE(MAX(id), 0) FROM events").fetchone()[0]
    return int(current) + 1


def create_event(payload: Dict[str, Any]) -> Dict[str, Any]:
    init_schema()
    con = get_connection()
    event_id = _next_event_id()
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
            payload["name"],
            payload["event_type"],
            payload["event_date"],
            _event_ym(payload["event_date"]),
            payload.get("source"),
            payload.get("description"),
        ],
    )
    row = con.execute(
        """
        SELECT id, name, event_type, event_date, event_ym, source, description
        FROM events
        WHERE id = ?
        """,
        [event_id],
    ).fetchone()
    return {"status": "success", "event": _row_to_event(row)}


def list_events() -> Dict[str, Any]:
    init_schema()
    con = get_connection()
    rows = con.execute(
        """
        SELECT id, name, event_type, event_date, event_ym, source, description
        FROM events
        ORDER BY event_date DESC, id DESC
        """
    ).fetchall()
    return {"status": "success", "events": [_row_to_event(row) for row in rows]}


def list_events_json(include_details: bool = True) -> Dict[str, Any]:
    init_schema()
    con = get_connection()
    rows = con.execute(
        """
        SELECT id, name, event_type, event_date, event_ym, source, description
        FROM events
        ORDER BY event_date DESC, id DESC
        """
    ).fetchall()
    events = [_row_to_event_payload(con, row, include_details) for row in rows]
    return {"status": "success", "count": len(events), "events": events}


def update_event(event_id: int, payload: Dict[str, Any]) -> Dict[str, Any]:
    init_schema()
    con = get_connection()
    exists = con.execute("SELECT id FROM events WHERE id = ?", [event_id]).fetchone()
    if not exists:
        return {"status": "not_found", "event_id": event_id}

    con.execute(
        """
        UPDATE events
        SET
            name = ?,
            event_type = ?,
            event_date = CAST(? AS DATE),
            event_ym = ?,
            source = ?,
            description = ?
        WHERE id = ?
        """,
        [
            payload["name"],
            payload["event_type"],
            payload["event_date"],
            _event_ym(payload["event_date"]),
            payload.get("source"),
            payload.get("description"),
            event_id,
        ],
    )
    row = con.execute(
        """
        SELECT id, name, event_type, event_date, event_ym, source, description
        FROM events
        WHERE id = ?
        """,
        [event_id],
    ).fetchone()
    return {"status": "success", "event": _row_to_event(row)}


def delete_event(event_id: int) -> Dict[str, Any]:
    init_schema()
    con = get_connection()
    exists = con.execute("SELECT id FROM events WHERE id = ?", [event_id]).fetchone()
    if not exists:
        return {"status": "not_found", "event_id": event_id}

    con.execute("DELETE FROM base_rate_event_details WHERE event_id = ?", [event_id])
    con.execute("DELETE FROM policy_event_details WHERE event_id = ?", [event_id])
    con.execute("DELETE FROM events WHERE id = ?", [event_id])
    return {"status": "success", "event_id": event_id}
