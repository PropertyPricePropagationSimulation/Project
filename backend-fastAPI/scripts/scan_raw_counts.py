"""Scan raw sale_data XML files and print per-file item counts.

Usage:
  python scripts/scan_raw_counts.py --raw-dir raw
"""
import argparse
from pathlib import Path
import xml.etree.ElementTree as ET


def scan(raw_dir: Path):
    files = sorted(
        path for path in raw_dir.glob('sale_data_*.xml')
        if not path.name.startswith('failed_')
    )
    if not files:
        print(f'No files in {raw_dir}')
        return

    total_files = 0
    total_items = 0
    for f in files:
        total_files += 1
        try:
            root = ET.parse(f).getroot()
            tc_node = root.find('.//totalCount')
            tc = int(tc_node.text) if tc_node is not None and tc_node.text and tc_node.text.isdigit() else 0
            items = root.findall('.//item')
            print(f"{f.name}: totalCount={tc}, items={len(items)}")
            total_items += len(items)
        except Exception as e:
            print(f"{f.name}: parse error: {e}")

    print(f"\nScanned {total_files} files, total items: {total_items}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--raw-dir', default='raw')
    args = parser.parse_args()
    scan(Path(args.raw_dir))


if __name__ == '__main__':
    main()
