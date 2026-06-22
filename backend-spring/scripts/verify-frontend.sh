#!/bin/bash
set -euo pipefail

echo "=== Frontend Verify ==="

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR/frontend"

npm run lint
npm run build

echo "OK: Frontend lint and build passed."