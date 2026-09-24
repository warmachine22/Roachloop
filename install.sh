#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-.}"
SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ ! -d "$ROOT/.git" ]; then
  echo "Roach Loop requires the target to be a Git repository: $ROOT" >&2
  exit 2
fi

mkdir -p "$ROOT/scripts" "$ROOT/skills" "$ROOT/schemas" "$ROOT/hooks" "$ROOT/templates"
cp "$SRC/scripts/roach.py" "$ROOT/scripts/roach.py"
cp "$SRC/scripts/providers.py" "$ROOT/scripts/providers.py"
cp -R "$SRC/skills/." "$ROOT/skills/"
cp -R "$SRC/schemas/." "$ROOT/schemas/"
cp -R "$SRC/hooks/." "$ROOT/hooks/"
cp -R "$SRC/templates/." "$ROOT/templates/"

chmod +x "$ROOT/scripts/roach.py" "$ROOT/scripts/providers.py"
find "$ROOT/hooks" -type f -name "*.sh" -exec chmod +x {} \; 2>/dev/null || true

cat > "$ROOT/ROACH-AGENT.md" <<'EOF'
# Roach Loop agent contract

This repository uses Roach Loop.
Before substantial work run: python3 scripts/roach.py next
For an active checkpoint run: python3 scripts/roach.py context <checkpoint> --role worker --json
Never manually edit Roach-managed gate state or fabricate evidence.
Before claiming completion run: python3 scripts/roach.py verify-project
Stop when Roach requires human judgment.
EOF

echo "Roach Loop installed in $ROOT"
echo "Next:"
echo "  cd $ROOT"
echo "  python3 scripts/roach.py init --name \"My Product\" --profile standard"
