---
name: ui-reviewer
description: Perform Roach Loop UI review against matching-state reference artifacts and record screenshots plus semantic verdict as evidence.
---
# Roach Loop UI Reviewer

Use only when the checkpoint declares UI work. A logic-only checkpoint must be created with `--no-ui`; UI cannot be silently skipped later.

Capture reference and implementation in the same state and scope. Archive screenshots/files, then attach them:
```bash
python3 scripts/roach.py external add --id UI-REF-001 --kind ui-reference --checkpoint <CP> --path <reference.png> --source human-reference
python3 scripts/roach.py external add --id UI-IMPL-001 --kind ui-capture --checkpoint <CP> --path <implementation.png> --source browser-capture
```

A fresh vision reviewer compares structure, spacing, alignment, size, state behavior, errors, and interaction. Any fixable blocker fails the gate.

Record:
```bash
python3 scripts/roach.py review <CP> ui fail --reviewer ui-a --model <model> --finding "..."
# or after zero blockers:
python3 scripts/roach.py review <CP> ui pass --reviewer ui-a --model <model>
```

For accessibility, also run the deterministic provider:
```bash
python3 scripts/roach.py plugin run accessibility --checkpoint <CP>
```
when the project's assurance policy calls for it.
