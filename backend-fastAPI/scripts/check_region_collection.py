"""Check collection coverage per region.

Reports, for each target region from `app.config_regions.get_region_codes()`:
- number of manifest entries
- total rows recorded in manifest
- number of raw files found
- total items found in raw files (by parsing XML)
- sample months with data

Usage:
  python scripts/check_region_collection.py
"""
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import json
import re
import xml.etree.ElementTree as ET
from collections import defaultdict

from app.config_regions import get_region_codes
from app.services import etl


BASE = Path(__file__).resolve().parents[1]
RAW_DIR = BASE / "raw"
PROCESSED_DIR = BASE / "processed"
MANIFEST = PROCESSED_DIR / "manifest.json"


def parse_raw_file(p: Path):
    try:
        root = ET.parse(p).getroot()
        items = root.findall('.//item')
        tc_node = root.find('.//totalCount')
        tc = int(tc_node.text) if tc_node is not None and tc_node.text and tc_node.text.isdigit() else 0
        return {"items": len(items), "totalCount": tc}
    except Exception:
        return {"items": 0, "totalCount": 0}


def main():
    region_codes = get_region_codes()

    manifest_entries = []
    if MANIFEST.exists():
        try:
            manifest_entries = json.loads(MANIFEST.read_text(encoding="utf-8")).get("processed", [])
        except Exception:
            manifest_entries = []

    manifest_by_region = defaultdict(list)
    for e in manifest_entries:
        rc = e.get("dong_code")
        manifest_by_region[rc].append(e)

    raw_files = sorted(
        path for path in RAW_DIR.glob("sale_data_*.xml")
        if not path.name.startswith("failed_")
    ) if RAW_DIR.exists() else []
    raw_by_region = defaultdict(list)
    name_pattern = re.compile(r"sale_data_(\d{5})_(\d{6})_p\d+")
    for f in raw_files:
        match = name_pattern.search(f.stem)
        if match:
            rc, _ym = match.groups()
            raw_by_region[rc].append(f)

    report = []
    for rc in sorted(region_codes):
        man = manifest_by_region.get(rc, [])
        man_count = len(man)
        man_rows = sum(e.get("rows", 0) for e in man)

        raws = raw_by_region.get(rc, [])
        raw_count = len(raws)
        raw_items = 0
        months_with_data = set()
        for f in raws:
            parsed = parse_raw_file(f)
            raw_items += parsed.get("items", 0)
            match = name_pattern.search(f.stem)
            if match:
                months_with_data.add(match.group(2))

        report.append({
            "region": rc,
            "manifest_entries": man_count,
            "manifest_rows": man_rows,
            "raw_files": raw_count,
            "raw_items": raw_items,
            "months_with_data_sample": sorted(list(months_with_data))[:5],
        })

    # print summary
    total_regions = len(region_codes)
    regions_with_data = sum(1 for r in report if r["raw_items"] > 0 or r["manifest_rows"] > 0)
    print(f"Regions targeted: {total_regions}")
    print(f"Regions with any data: {regions_with_data}")
    print("\nPer-region summary (showing regions with no data first):")
    for r in sorted(report, key=lambda x: (-(x["raw_items"] + x["manifest_rows"]), x["region"])):
        print(f"{r['region']}: manifest_entries={r['manifest_entries']}, manifest_rows={r['manifest_rows']}, raw_files={r['raw_files']}, raw_items={r['raw_items']}, months_sample={r['months_with_data_sample']}")

    # write report
    out = BASE / "collection_report.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nReport saved to: {out}")


if __name__ == '__main__':
    main()
