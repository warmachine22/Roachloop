---
name: roach-loop-orchestrator
description: Use Roach Loop for substantial feature, refactor, migration, or multi-step coding work.
---
# Roach Loop Orchestrator

Roach is software-first. Do not simulate its state machine in prose and do not directly edit managed gate state.

1. Run `python3 scripts/roach.py next`.
2. Run `python3 scripts/roach.py context <id> --role worker --json`.
3. Work only on the checkpoint's declared requirements/files.
4. Record a fail-first baseline where configured.
5. Commit the candidate before executable verification.
6. Run `python3 scripts/roach.py verify <id>`; never self-declare behavior passed.
7. For UI work, capture matching-state reference/implementation artifacts and use the UI reviewer skill.
8. Give adversarial reviewers isolated reviewer packets. Standard/Strict require two independent identities.
9. Fix every blocking finding and rerun invalidated proof.
10. Stop for actual human acceptance when requested.
11. Run deterministic `audit`, then `seal`.
12. Before reporting project completion run `verify-project`.
13. If intent changes, use `redirect`; preserve history and supersede affected work.
14. If Roach reports unavailable required capabilities or stale evidence, do not downgrade or bypass them.

Human: intent and subjective acceptance.
Models: implementation and semantic judgment.
Roach: deterministic facts, provenance, policy, freshness, and seals.
