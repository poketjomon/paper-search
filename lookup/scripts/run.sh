#!/bin/sh
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname "$0")" && pwd)
SKILL_DIR=$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)

if [ "$#" -ge 1 ] && [ "$1" = "download" ]; then
  shift
  exec python3 "$SKILL_DIR/scripts/download_papers.py" "$@"
fi

exec python3 "$SKILL_DIR/scripts/alphaxiv_lookup.py" "$@"
