---
name: checkpoint-planner
description: Split substantial work into small Roach Loop checkpoints with stable requirement IDs, relevant-file scopes, risk classification, and exact verification commands.
---
# Roach Loop Checkpoint Planner

Roach state is software-owned. Never write checkpoint status or gates directly.

## Inputs
Run:
```bash
python3 scripts/roach.py requirement list --json
python3 scripts/roach.py status --json
```

Read product/design docs only as needed.

## Rules
Each checkpoint must:
1. map to one or more active FR-/QR- requirement IDs;
2. be small enough for one worker context packet;
3. declare an exact verification command;
4. declare relevant files/globs so evidence invalidation is precise;
5. declare `--no-ui` only when genuinely non-visual;
6. never manually lower automatically detected risk;
7. use a failing baseline when the behavior can be demonstrated absent before implementation;
8. use a mutation command for critical behavior when a mutation tool exists.

Create through the kernel:
```bash
python3 scripts/roach.py checkpoint add CP-001 "Login token validation" \
  --requirements FR-002,QR-004 \
  --files "src/auth/*.py,tests/auth/*.py" \
  --verify "pytest -q tests/auth/test_tokens.py"
```

Check context size:
```bash
python3 scripts/roach.py context CP-001 --role worker --json
```
If the packet exceeds its budget, split the checkpoint.

The plan is complete only when every active requirement is covered by at least one non-superseded checkpoint.
