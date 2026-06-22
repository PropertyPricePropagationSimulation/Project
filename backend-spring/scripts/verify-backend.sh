#!/bin/bash
set -euo pipefail

echo "=== Backend Verify ==="

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR/backend"

./mvnw -q test

echo "OK: All backend tests passed."