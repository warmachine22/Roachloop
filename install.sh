#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-.}"
SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
mkdir -p "$ROOT/scripts" "$ROOT/skills/orchestrator"
cp "$SRC/scripts/roach.py" "$ROOT/scripts/roach.py"\ncp "$SRC/scripts/providers.py" "$ROOT/scripts/providers.py"
cp "$SRC/skills/orchestrator/SKILL.md" "$ROOT/skills/orchestrator/SKILL.md"
chmod +x "$ROOT/scripts/roach.py"
echo "Roach Loop installed in $ROOT"
echo "Next: cd $ROOT && python3 scripts/roach.py init --name \"My Product\""
