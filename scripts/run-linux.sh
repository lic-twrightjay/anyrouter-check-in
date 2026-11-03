#!/usr/bin/env bash
# Run the existing headed Playwright implementation without a physical display.
set -euo pipefail

project_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$project_dir"
export PATH="$HOME/.local/bin:$PATH"

if ! command -v uv >/dev/null 2>&1; then
  echo "[FAILED] uv not found; install uv for this Linux account first" >&2
  exit 1
fi
if ! command -v xvfb-run >/dev/null 2>&1; then
  echo "[FAILED] xvfb-run not found; install xvfb and xauth first" >&2
  exit 1
fi
if [[ ! -f .env ]] && [[ -z "${ANYROUTER_ACCOUNTS:-}" ]] && ! env | grep -q '^ANYROUTER_ACCOUNT_'; then
  echo "[FAILED] No .env or account environment variables found in the project directory" >&2
  exit 1
fi

exec xvfb-run -a -s '-screen 0 1920x1080x24 -nolisten tcp' \
  uv run --frozen python -u checkin.py
