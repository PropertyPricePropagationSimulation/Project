"""Check raw apartment sale XML coverage by region/year/month."""

from __future__ import annotations

import argparse
import csv
import re
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT_DIR / "raw"


def parse_count(path: Path) -> int:
    root = ET.parse(path).getroot()
    total_text = root.findtext(".//totalCount")
    if total_text is not None and total_text.strip().isdigit():
        return int(total_text)
    return len(root.findall(".//item"))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="raw/sale_data_gap_report.csv")
    args = parser.parse_args()

    pattern = re.compile(r"sale_data_(\d{5})_(\d{6})_p(\d+)_")
    stats = defaultdict(lambda: {"months": set(), "total_items": 0, "zero_months": set(), "files": 0})
    monthly = defaultdict(int)
    bad_files = []

    for path in RAW_DIR.glob("sale_data_*_*.xml"):
        match = pattern.search(path.name)
        if not match:
            continue
        region, ym, _page = match.groups()
        key = (region, ym[:4])
        try:
            count = parse_count(path)
        except Exception:
            bad_files.append(str(path))
            count = 0

        stats[key]["months"].add(ym)
        stats[key]["total_items"] += count
        stats[key]["files"] += 1
        monthly[(region, ym)] += count

    for (region, ym), count in monthly.items():
        if count == 0:
            stats[(region, ym[:4])]["zero_months"].add(ym)

    output_path = ROOT_DIR / args.output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8-sig", newline="") as csv_file:
        fieldnames = [
            "region",
            "year",
            "collected_month_count",
            "total_items",
            "zero_month_count",
            "zero_months",
            "all_collected_months_zero",
        ]
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        for (region, year), data in sorted(stats.items()):
            months = sorted(data["months"])
            zero_months = sorted(data["zero_months"])
            writer.writerow(
                {
                    "region": region,
                    "year": year,
                    "collected_month_count": len(months),
                    "total_items": data["total_items"],
                    "zero_month_count": len(zero_months),
                    "zero_months": ";".join(zero_months),
                    "all_collected_months_zero": str(bool(months) and data["total_items"] == 0).lower(),
                }
            )

    all_zero = [
        (region, year, len(data["months"]), data["total_items"], sorted(data["zero_months"]))
        for (region, year), data in sorted(stats.items())
        if data["months"] and data["total_items"] == 0
    ]

    print(f"raw_xml_files={sum(data['files'] for data in stats.values())}")
    print(f"region_year_pairs={len(stats)}")
    print(f"bad_files={len(bad_files)}")
    print(f"report={output_path}")
    print("all_collected_months_zero:")
    for region, year, month_count, total, zero_months in all_zero:
        print(f"{region} {year} months={month_count} total_items={total} zero_months={','.join(zero_months)}")


if __name__ == "__main__":
    main()
