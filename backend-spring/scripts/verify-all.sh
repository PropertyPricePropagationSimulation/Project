#!/bin/bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"

bash "$ROOT_DIR/scripts/verify-backend.sh"
bash "$ROOT_DIR/scripts/verify-analysis.sh"
# bash "$ROOT_DIR/scripts/verify-frontend.sh"  # frontend 디렉토리 생성 후 활성화

echo "=== All checks passed ==="