#!/usr/bin/env bash
set -u
PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$PWD}"
STATE="$PROJECT_DIR/.roach/state.json"
ROACH="$PROJECT_DIR/scripts/roach.py"
[ -f "$STATE" ] || exit 0
[ -f "$ROACH" ] || { echo "ROACH: scripts/roach.py missing" >&2; exit 2; }
command -v python3 >/dev/null 2>&1 || { echo "ROACH: python3 missing" >&2; exit 2; }
cd "$PROJECT_DIR" || exit 2
OUTPUT="$(python3 "$ROACH" verify-project 2>&1)"
RC=$?
if [ $RC -ne 0 ]; then
 echo "ROACH STOP HOOK: project assurance record is invalid:"
 echo "$OUTPUT"
 exit 2
fi
exit 0
