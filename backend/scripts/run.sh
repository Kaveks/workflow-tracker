#!/usr/bin/env sh
# Start the workflow tracker stack (backend + frontend).
# Usage: ./scripts/run.sh        # detached
#        ./scripts/run.sh fg     # foreground (Ctrl-C to stop)
set -eu
cd "$(dirname "$0")/.."

if [ "${1:-}" = "fg" ]; then
  docker compose up
else
  docker compose up -d
  echo ""
  echo "Backend:  http://localhost:8000/api/docs"
  echo "Frontend: http://localhost:3000"
fi
