---
name: adversarial-review
description: Run Roach Loop's dual independent adversarial review with context isolation, reviewer provenance, disagreement findings, and gate enforcement.
---
# Roach Loop Adversarial Review

Roach Standard and Strict require two independent reviewer identities.

Each reviewer gets only:
```bash
python3 scripts/roach.py context <CP> --role reviewer --json
```
Do not give either reviewer builder reasoning or the other reviewer's output.

Review architecture, error handling, security, tests, requirement coverage, and changed code. Every failure must state a concrete finding.

Record a failing review:
```bash
python3 scripts/roach.py review <CP> adversarial fail \
  --reviewer reviewer-a --model <model> --finding "..."
```
Roach opens a blocking finding. Fix it, re-run affected executable proof, then close the finding with its resolution.

Record approval:
```bash
python3 scripts/roach.py review <CP> adversarial pass --reviewer reviewer-a --model <model>
python3 scripts/roach.py review <CP> adversarial pass --reviewer reviewer-b --model <model>
```

The same reviewer identity cannot occupy both slots. Roach records model, reviewer, role, timestamp, current Git head, and the isolated context hash.
