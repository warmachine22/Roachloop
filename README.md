# Roach Loop

**Proof-carrying development for coding agents.**

Roach Loop is an augmented, re-engineered descendant of the MIT-licensed JohnArks Method. It keeps checkpoint discipline and human product authority, while moving critical truth out of agent-written status files into deterministic software.

> Agents may propose facts. Deterministic machinery decides what is true.

## First-class foundation

- machine-owned checkpoint state transitions
- exact Git-tree verification receipts
- tamper-evident hash-chained ledger
- mandatory gate policy
- requirement → checkpoint traceability
- stale-evidence detection
- fast / standard / strict assurance profiles
- role-specific context compiler
- independent `verify-project`
- `doctor`, `next`, `status`, and `seal`
- hostile/tamper regression tests
- Vercel-ready documentation site

## Quick start

```bash
git clone https://github.com/warmachine22/Roachloop.git
cd Roachloop
python3 -m unittest discover -s tests -v
python3 scripts/roach.py init --name "My Product"
python3 scripts/roach.py requirement add FR-001 "User can sign in"
python3 scripts/roach.py checkpoint add CP-001 "Sign in" --requirements FR-001 --verify "pytest -q tests/test_login.py"
python3 scripts/roach.py start CP-001
python3 scripts/roach.py verify CP-001
python3 scripts/roach.py next
```

## Minimal agent instruction

```text
This repository uses Roach Loop.
Before substantial work run: python3 scripts/roach.py next
Use: python3 scripts/roach.py context <checkpoint> --role worker
Never manually edit Roach-managed gate state.
Before claiming completion run: python3 scripts/roach.py verify-project
```

The human owns intent. Agents implement and review. Roach owns deterministic facts and provenance.

See `ROACH-PROTOCOL.md` for the protocol and `NOTICE.md` for upstream attribution.
