# Roach Loop

[![Roach Loop Assurance](https://github.com/warmachine22/Roachloop/actions/workflows/roach.yml/badge.svg)](https://github.com/warmachine22/Roachloop/actions/workflows/roach.yml)
[![Self Dogfood](https://github.com/warmachine22/Roachloop/actions/workflows/self-dogfood.yml/badge.svg)](https://github.com/warmachine22/Roachloop/actions/workflows/self-dogfood.yml)

**Proof-carrying development for coding agents.**

Roach Loop is a model-independent assurance layer for software built with Claude, Codex, and other coding agents.

> **Agents may propose facts. Deterministic machinery decides what is true.**

Humans remain authoritative over product intent and subjective acceptance. Agents implement and perform semantic review. Roach owns state transitions, executable receipts, evidence integrity, freshness, traceability, risk policy, and seals.

Roach Loop began as an augmented derivative of the MIT-licensed JohnArks Method. See [NOTICE.md](NOTICE.md).

## What v3 implements

The repository contains an executable registry for all **70 long-term capabilities** in the design. See [CAPABILITIES.md](CAPABILITIES.md).

Major layers include:

- deterministic checkpoint state machine and fail-closed gate policy
- append-only hash-chained event ledger
- evidence bundles with SHA-256 manifests
- exact Git/relevant-file provenance and stale-proof invalidation
- structured FR-/QR- requirements and bidirectional traceability
- fail-first baselines, behavior receipts, mutation hooks, and reproduction checks
- dual independent reviewer provenance and blocking finding lifecycle
- exact-artifact human approval and deterministic independent audit
- automatic risk escalation plus fast / standard / strict assurance profiles
- built-in security, accessibility, performance, and migration providers
- external evidence/provider contracts
- context compiler with worker/reviewer/auditor isolation and token budgets
- architecture drift and explicit requirement-conflict checks
- decision lineage, redirects, uncertainty/blocking, and external dependencies
- checkpoint seals, release seals, HTML/JSON/PDF assurance reports
- live/machine-readable status export, doctor, impact analysis, freshness, and why
- CI enforcement, pre-push enforcement, Windows/macOS/Linux installation
- self-dogfooding workflow, hostile tests, threat model, benchmark ledger, example corpus

## Quick verification

Do not trust this README. Run the implementation:

```bash
git clone https://github.com/warmachine22/Roachloop.git
cd Roachloop

python3 -m unittest discover -s tests -v
python3 scripts/roach.py capabilities --json
python3 scripts/providers.py security
python3 scripts/providers.py accessibility
python3 scripts/providers.py performance
```

GitHub Actions also runs Roach through a complete sealed lifecycle on itself.

## Install into a project

macOS/Linux:

```bash
./install.sh /path/to/project
```

Windows PowerShell:

```powershell
.\install.ps1 -Target C:\path\to\project
```

Then:

```bash
cd /path/to/project
python3 scripts/roach.py init --name "My Product" --profile standard
```

## A first checkpoint

```bash
python3 scripts/roach.py requirement add FR-001 "User can sign in" \
  --acceptance "Valid credentials create a session" \
  --acceptance "Invalid credentials are rejected"

python3 scripts/roach.py checkpoint add CP-001 "Sign in" \
  --requirements FR-001 \
  --files "src/auth/*,tests/auth/*" \
  --verify "pytest -q tests/auth"

python3 scripts/roach.py start CP-001

# build and commit the candidate
python3 scripts/roach.py verify CP-001

# UI review if applicable, then two independent adversarial reviews
python3 scripts/roach.py review CP-001 adversarial pass --reviewer reviewer-a --model <model>
python3 scripts/roach.py review CP-001 adversarial pass --reviewer reviewer-b --model <model>

python3 scripts/roach.py approve CP-001 --approver "<human>"
python3 scripts/roach.py audit CP-001
python3 scripts/roach.py seal CP-001
python3 scripts/roach.py verify-project
```

Use `python3 scripts/roach.py next` at any point to see the next protocol action.

## Minimal agent instruction

The agent does **not** need the 70 capabilities in its prompt:

```text
This repository uses Roach Loop.
Before substantial work run: python3 scripts/roach.py next
For the active checkpoint run: python3 scripts/roach.py context <checkpoint> --role worker
Never manually edit Roach-managed gate state or fabricate evidence.
Before claiming completion run: python3 scripts/roach.py verify-project
Stop when Roach requires human judgment.
```

That is intentional. As Roach becomes stronger, the procedural prompt should become smaller.

## Proof surfaces

```bash
python3 scripts/roach.py doctor --json
python3 scripts/roach.py status --json
python3 scripts/roach.py freshness --json
python3 scripts/roach.py impact --since <commit> --json
python3 scripts/roach.py why CP-001 --json
python3 scripts/roach.py report
python3 scripts/roach.py release v1.0.0 --tag
```

Read [ROACH-PROTOCOL.md](ROACH-PROTOCOL.md), [THREAT-MODEL.md](THREAT-MODEL.md), and [CAPABILITIES.md](CAPABILITIES.md) for the formal design.
