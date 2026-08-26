#!/bin/sh
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname "$0")" && pwd)
SUITE_DIR=$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)

if [ "$#" -lt 1 ]; then
  printf '%s\n' "Usage: ./scripts/run.sh <search|lookup|reader> [args...]" >&2
  exit 1
fi

SUBSKILL=$1
shift

case "$SUBSKILL" in
  search)
    exec "$SUITE_DIR/search/scripts/run.sh" "$@"
    ;;
  lookup)
    exec "$SUITE_DIR/lookup/scripts/run.sh" "$@"
    ;;
  reader)
    exec "$SUITE_DIR/reader/scripts/run.sh" "$@"
    ;;
  *)
    printf '%s\n' "Unknown subskill: $SUBSKILL" >&2
    printf '%s\n' "Expected one of: search, lookup, reader" >&2
    exit 1
    ;;
esac
