---
name: design-planner
description: Define human-readable architecture/design rules and encode machine-checkable drift constraints for Roach Loop.
---
# Roach Loop Design Planner

Create or update the project's `design.md` / `ARCHITECTURE.md` with explicit stack, boundaries, state/data flow, error conventions, visual tokens, component rules, and banned patterns.

Whenever a rule can be checked deterministically, also register it:
```bash
python3 scripts/roach.py architecture add \
  --id AR-001 \
  --files "src/ui/*.py" \
  --forbidden-regex "direct_database_call" \
  --reason "UI must use the service layer"
```

Validate machine rules with:
```bash
python3 scripts/roach.py architecture check
```

Do not encode subjective preferences as blocking regex rules. The architecture document remains the semantic standard used by reviewers.
