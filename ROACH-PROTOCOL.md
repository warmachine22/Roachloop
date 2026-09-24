# Roach Loop Protocol v2

Roach Loop is a portable assurance layer for agent-written software.

## Governing principle

**Agents may propose facts. Deterministic machinery decides what is true.**

The human owns intent. Agents implement and perform semantic review. Roach owns state transitions, verification receipts, provenance checks, and seals.

## Managed state

A project stores durable data in `.roach/`:

- `state.json` — managed checkpoint state.
- `requirements.json` — structured requirements.
- `ledger.jsonl` — append-only hash-chained events.
- `evidence/<checkpoint>/` — machine-created receipts and seals.
- `config.json` — assurance policy.

Agents must not manually mark gates passed.

## Lifecycle

`planned → implementing → behavior_verified → ui_verified → adversarial_verified → human_accepted → audited → sealed`

A checkpoint can become `blocked` or `superseded`. Invalid transitions are rejected.

## Gate policy

Behavior, adversarial, human, and audit gates cannot be skipped. UI may be not-applicable only when the checkpoint is explicitly non-visual.

## Evidence receipts

Behavior verification records protocol version, checkpoint, requirement IDs, exact Git tree, HEAD, command, timestamps, exit code, and hashes of stdout/stderr. The receipt itself is hashed.

A changed Git tree makes that receipt stale.

## Tamper-evident ledger

Every managed event includes the previous event hash and its own SHA-256 digest. `verify-project` reconstructs the chain and reports tampering.

## Traceability

Every checkpoint can cite stable requirement IDs. Independent verification reports active requirements not covered by a non-superseded checkpoint.

## Context compiler

`roach context CP-014 --role worker|reviewer|auditor` emits a minimal role-specific packet. Workers see goals and verification; reviewers see current gates/tree; auditors see evidence references. This reduces repeated context loading and keeps reviews isolated.

## Assurance profiles

- **fast** — behavior, human, audit.
- **standard** — behavior, UI when applicable, adversarial, human, audit.
- **strict** — standard plus clean-worktree sealing and stronger provenance expectations.

## Seals

A checkpoint may be sealed only after required gates pass and current evidence validates. A seal binds the checkpoint, requirements, HEAD, and Git tree to a digest.

## Independent verification

`roach verify-project` checks the ledger, traceability, evidence integrity, freshness, and sealed-gate policy without asking an LLM whether the method was followed.

## Design direction

The trusted computing base should remain small. Models should be used where semantic judgment is valuable; Git, hashes, state transitions, test execution, evidence freshness, and traceability should remain deterministic.
