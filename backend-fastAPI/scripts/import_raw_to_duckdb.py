"""Import collected raw sale_data XML files into a DuckDB table for exploration.

Usage:
    python scripts/import_raw_to_duckdb.py --raw-dir raw --duckdb-file ssafy.duckdb

This script looks for files named like `sale_data_*.xml` in the raw directory,
parses the XML plus the sidecar `.meta.json`, normalizes items, and appends
them into a DuckDB table named `sale_raw`.
"""
import argparse
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime
import duckdb
import pandas as pd
from typing import List, Dict, Any


def parse_molit_xml(text: str) -> Dict[str, Any]:
    root = ET.fromstring(text)
    items = []
    for item in root.findall('.//item'):
        row = {child.tag: child.text for child in item}
        items.append(row)

    total_count = None
    total_count_node = root.find('.//totalCount')
    if total_count_node is not None:
        try:
            total_count = int(total_count_node.text or 0)
        except Exception:
            total_count = None

    return {"total_count": total_count, "items": items}


def normalize_items(items: List[Dict[str, Any]], meta: Dict[str, Any]) -> List[Dict[str, Any]]:
    rows = []
    for it in items:
        def val(*keys):
            for k in keys:
                if k in it and it[k] is not None:
                    return it[k]
            return None

        rows.append({
            "raw_file": meta.get("raw_file"),
            "saved_at": meta.get("saved_at"),
            "LAWD_CD": meta.get("LAWD_CD"),
            "DEAL_YMD": meta.get("DEAL_YMD"),
            "APT_NAME": val("아파트", "APT_NAME", "건물명"),
            "DONG": val("법정동", "법정동명", "dong", "DONG"),
            "JIBUN": val("번지", "지번", "JIBUN"),
            "FLOOR": val("층", "FLOOR"),
            "BUILD_YEAR": val("건축년도", "BUILD_YEAR"),
            "EXCLU_USE_AR": val("전용면적", "EXCLU_USE_AR"),
            "DEAL_AMOUNT": val("거래금액", "DEAL_AMOUNT"),
            "DEAL_DAY": val("일", "DEAL_DAY", "일자"),
        })
    return rows


def import_raw(raw_dir: Path, duckdb_file: Path, table_name: str = "sale_raw"):
    files = sorted(
        path for path in raw_dir.glob("sale_data_*.xml")
        if not path.name.startswith("failed_")
    )
    if not files:
        print(f"No raw files found in {raw_dir}")
        return

    conn = duckdb.connect(database=str(duckdb_file), read_only=False)

    all_rows = []
    for f in files:
        try:
            meta_path = f.with_suffix(f.suffix + ".meta.json")
            payload = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.exists() else {}
            saved_at = payload.get("saved_at")
            params = payload.get("params", {})
            name_match = re.search(r"sale_data_(\d{5})_(\d{6})_p\d+", f.stem)
            lawd = params.get("LAWD_CD") or (name_match.group(1) if name_match else None)
            deal_ym = params.get("DEAL_YMD") or (name_match.group(2) if name_match else None)
            xml_text = f.read_text(encoding="utf-8")
            parsed = parse_molit_xml(xml_text)
            items = parsed.get("items", [])
            meta = {"raw_file": str(f), "saved_at": saved_at, "LAWD_CD": lawd, "DEAL_YMD": deal_ym}
            rows = normalize_items(items, meta)
            all_rows.extend(rows)
        except Exception as e:
            print(f"Failed to parse {f}: {e}")

    if not all_rows:
        print("No records to insert (all files contained zero items)")
        return

    df = pd.DataFrame(all_rows)

    # Ensure types
    if "saved_at" in df.columns:
        try:
            df["saved_at_ts"] = pd.to_datetime(df["saved_at"]).astype("datetime64[ns]")
        except Exception:
            df["saved_at_ts"] = pd.NaT

    # Write to DuckDB (upsert by appending for now)
    conn.execute(f"CREATE TABLE IF NOT EXISTS {table_name} AS SELECT * FROM df LIMIT 0")
    conn.register("to_insert_df", df)
    conn.execute(f"INSERT INTO {table_name} SELECT * FROM to_insert_df")
    conn.close()

    print(f"Imported {len(df)} records into {duckdb_file}:{table_name}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-dir", default="raw", help="raw directory containing sale_data_*.xml")
    parser.add_argument("--duckdb-file", default="ssafy.duckdb", help="DuckDB file to write to")
    parser.add_argument("--table", default="sale_raw", help="DuckDB table name")
    args = parser.parse_args()

    raw_dir = Path(args.raw_dir)
    duckdb_file = Path(args.duckdb_file)

    import_raw(raw_dir, duckdb_file, table_name=args.table)


if __name__ == "__main__":
    main()
