#!/bin/bash
set -euo pipefail

echo "=== Risk File Check ==="

RISKY=$(git diff HEAD --name-only | grep -E \
  "application.*\.(ya?ml|properties)|SecurityConfig|pom\.xml|package(-lock)?\.json|schema|migration|FilterRegistration" || true)

if [ -n "$RISKY" ]; then
  echo "RISKY FILES CHANGED:"
  echo "$RISKY"
  echo "Human review required before commit."
  exit 1
fi

echo "OK: No risky files changed."