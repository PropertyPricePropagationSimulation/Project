#!/bin/bash
set -euo pipefail

echo "=== Analysis Integration Verify ==="

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR/backend"

# AI 연동 관련 테스트만 필터링
./mvnw -q test -Dtest="*Analysis*,*Balloon*,*Scenario*" -DfailIfNoTests=false

echo "OK: Analysis integration tests passed."
echo "NOTE: AI 모델 출력 품질은 이 스크립트 검증 대상이 아님."