#!/usr/bin/env bash
# Portable stand-in for `make reproduce` where make is not installed (Windows).
set -euo pipefail
cd "$(dirname "$0")"

PY="${PY:-python}"
STAGES=("$@")
if [ ${#STAGES[@]} -eq 0 ]; then
  STAGES=(nulls trials neff dsr charts)
fi

for s in "${STAGES[@]}"; do
  echo "== stage: $s"
  PYTHONPATH=src "$PY" -m "btrap.pipeline" "$s"
done
echo "reproduced without touching the holdout."
