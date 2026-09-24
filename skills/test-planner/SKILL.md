---
name: test-planner
description: Define executable user-perspective proof for Roach Loop behavior gates, including fail-first baselines, edges, and optional mutation checks.
---
# Roach Loop Test Planner

Behavior truth comes from executable receipts, not prose.

For the active checkpoint, obtain only the worker packet:
```bash
python3 scripts/roach.py context <CP> --role worker --json
```

Create tests from the user's perspective. Cover happy path, invalid input, permissions, boundaries, empty states, failures, and important regressions. Prefer fast deterministic tests.

When a fail-first baseline is meaningful, configure `--baseline-verify` and run:
```bash
python3 scripts/roach.py baseline <CP>
```
Roach requires the baseline to fail; a passing baseline is rejected as non-discriminating.

After implementation is committed:
```bash
python3 scripts/roach.py verify <CP>
```

For critical checkpoints, configure a mutation-testing command. Roach can require it under strict assurance. Never mark the behavior gate manually.
