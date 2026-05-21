#!/usr/bin/env sh
# Build Docker images for the workflow tracker.
# Usage: ./scripts/build.sh
set -eu
cd "$(dirname "$0")/.."
docker compose build "$@"
