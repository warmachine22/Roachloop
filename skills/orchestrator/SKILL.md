---
name: roach-loop-orchestrator
description: Use Roach Loop for substantial feature, refactor, migration, or multi-step coding work.
---
# Roach Loop Orchestrator
Roach Loop is software-first. Do not simulate its state machine in prose.

1. Before substantial work run `python3 scripts/roach.py next`.
2. Run `python3 scripts/roach.py context <id> --role worker` for the active checkpoint.
3. Work only on declared requirements.
4. Never manually edit Roach-managed gate state or fabricate evidence.
5. Use `python3 scripts/roach.py verify <id>` for behavior verification.
6. Reviewers use the reviewer context packet, not builder reasoning.
7. Stop for real human acceptance when requested.
8. Auditors use the auditor context packet and inspect evidence.
9. Before claiming completion run `python3 scripts/roach.py verify-project`.
10. If intent changes, preserve history, supersede affected work, and re-plan.

The human owns intent. Agents implement and judge semantics. Roach owns deterministic facts.
