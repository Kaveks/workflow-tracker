#!/usr/bin/env sh
# Stop and remove all containers, volumes, and locally built images.
# Use this to fully reset the dev environment.
# Usage: ./scripts/drop.sh
set -eu
cd "$(dirname "$0")/.."

echo "Stopping containers and dropping volumes/images for workflow-tracker..."
docker compose down -v --rmi local --remove-orphans
echo "Done."
