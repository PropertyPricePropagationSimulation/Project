"""Print current target MOLIT LAWD_CD values."""

from __future__ import annotations

import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.config_regions import get_project_region_groups, get_region_codes


def main() -> None:
    codes = get_region_codes()
    groups = get_project_region_groups()
    print(f"target_code_count={len(codes)}")
    print(",".join(codes))
    print(f"suwon={','.join(groups['41110'])}")
    print(f"bucheon={','.join(groups['41190'])}")
    print(f"hwaseong={','.join(groups['41590'])}")


if __name__ == "__main__":
    main()
