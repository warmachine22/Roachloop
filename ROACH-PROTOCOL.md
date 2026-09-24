# Roach Loop Protocol v3

## 1. Purpose

Roach Loop is a portable assurance protocol for agent-written software. It does not treat a model's narration as proof.

**Principle:** agents may propose facts; deterministic machinery decides what is true where deterministic verification is possible.

Humans own product intent and subjective acceptance. Models are useful for semantic judgment. Roach binds those judgments to artifacts and surrounds them with deterministic provenance.

## 2. Trusted computing base

The intended TCB is deliberately small:

1. `scripts/roach.py`
2. Git object/state semantics
3. configured deterministic verification/provider executables
4. explicit human identity/intent assertions

Skills and model reasoning are orchestration aids, not sources of machine truth.

## 3. Managed data

A Roach project uses `.roach/`:

- `state.json` — checkpoint state
- `requirements.json` — FR-/QR- requirements
- `ledger.jsonl` — hash-chained events
- `evidence/<checkpoint>/` — receipts, reviews, approvals, audits, seals
- `findings.json` — defect/review finding lifecycle
- `decisions.json` — decision lineage
- `external.json` — dependencies and externally supplied evidence
- `architecture.json` — machine-checkable architecture constraints
- `plugins.json` — evidence-provider configuration
- `environment.json` — optional frozen environment fingerprint
- `benchmarks.json` — measurement records
- `reports/` — portable reports

## 4. State machine

Core lifecycle:

```text
planned
  ↓
implementing
  ↓
behavior_verified
  ↓
ui_verified              (when UI required)
  ↓
adversarial_verified     (when profile requires)
  ↓
human_accepted
  ↓
audited
  ↓
sealed
```

`blocked` and `superseded` are explicit side states. Illegal transitions are rejected.

Profiles may omit gates but cannot forge a gate result. Fast mode advances across omitted waypoints explicitly and records why.

## 5. Requirements and traceability

Requirements are structured FR-/QR- objects with status, kind, priority, acceptance criteria, and explicit conflicts. Every non-superseded checkpoint maps to requirement IDs and relevant files/globs.

`verify-project` reports uncovered active requirements and explicit active conflicts.

The graph connects:

```text
requirement ↔ checkpoint ↔ relevant files ↔ evidence
                  ↕
             findings / decisions
```

## 6. Behavior proof

A behavior gate passes only when Roach executes the declared command and it exits zero.

The receipt records:

- protocol version
- checkpoint and requirement IDs
- Git HEAD/tree
- relevant-file SHA-256 snapshot
- command
- sandbox state
- environment fingerprint
- exit code
- stdout/stderr hashes
- evidence hash

Roach never stores raw command output in the receipt, reducing accidental secret retention.

## 7. Freshness

Current relevant-file hashes are compared with the receipt snapshot. A relevant file added, removed, or modified makes proof stale. Unrelated changes do not invalidate the checkpoint.

`freshness`, `impact`, `check`, `why`, and `verify-project` expose the result.

## 8. Evidence integrity

Every evidence object is SHA-256 hashed. Every checkpoint evidence directory has a manifest containing per-file hashes and a manifest hash.

Every ledger event includes the previous event hash and its own digest.

Tampering with either is reported by deterministic verification.

## 9. Review independence

Reviewer records include reviewer identity, model identity, role, Git head, verdict, and isolated context hash.

Standard/Strict adversarial review requires two distinct reviewer identities. A failing review creates a blocking finding. Audit fails with unresolved findings.

Workers, reviewers, and auditors receive different context packets.

## 10. Human approval

Human approval is a subjective proof type. It is bound either to current Git HEAD or to the SHA-256 of an existing artifact file. Arbitrary free-text artifact identifiers are rejected.

Human acceptance is never replaced by model approval unless a separately defined autonomous mode is explicitly built by the consuming project.

## 11. Audit

`audit` reconstructs checkpoint consistency from evidence, findings, traceability, and freshness. It generates a deterministic audit receipt.

Audit is different from semantic code review: it verifies whether the record agrees with the artifacts and policy.

## 12. Risk and assurance profiles

Automatic risk signals inspect checkpoint title/files for authentication, permissions, payments, migrations, secrets, PII, infrastructure, and other sensitive areas.

A user may raise risk but may not silently force risk below automatic detection.

Profiles:

- **fast** — behavior + human + audit
- **standard** — behavior + UI when applicable + two adversarial reviewers + human + audit
- **strict** — standard plus sandbox-required verification, mutation expectation for configured critical tests, and stronger clean-state constraints

High/critical risk can add specialized gates such as security/performance.

## 13. Specialized deterministic providers

Roach ships dependency-free baseline providers in `scripts/providers.py` for:

- security
- accessibility
- performance
- migration/data-integrity

Projects may replace or augment them through `.roach/plugins.json`. Missing required executables fail closed.

## 14. Sandboxing and environment reproduction

Strict verification requires Docker or Podman. Verification receipts include OS/runtime/lockfile fingerprints.

`environment freeze` / `environment check` detect environment drift.

`reproduce <checkpoint>` reruns the recorded behavior command and compares its result, refusing environment drift unless explicitly allowed.

## 15. Context compiler

`context <checkpoint> --role worker|reviewer|auditor` emits minimum role-specific JSON and estimates token size against role budgets.

A packet over budget is rejected so oversized checkpoints are split rather than forcing the model to absorb the whole project.

## 16. Redirects, decisions, uncertainty

Intent changes are recorded with `redirect`; affected checkpoints are superseded instead of rewritten.

`decision` stores chosen alternatives and rationale.

Blocked work remains explicit. Requirements can be superseded and the schemas allow unknown/blocked requirement states rather than fabricated certainty.

## 17. Architecture and contradictions

Architecture rules may be registered as file globs plus forbidden regexes. `architecture check` deterministically detects violations.

Explicit requirement conflicts are surfaced by `verify-project`.

Semantic contradictions remain a review concern; Roach does not pretend regexes replace product reasoning.

## 18. Releases and reports

A checkpoint seal binds requirements, current evidence, Git state, and manifest provenance.

A release seal requires all non-superseded checkpoints sealed and the whole project verifier clean.

`report` emits JSON, HTML, and dependency-free PDF. `export` emits machine-readable status for dashboards/sites.

## 19. CI and local enforcement

The repository includes:

- GitHub Actions core assurance tests
- a self-dogfood workflow that executes a full Roach lifecycle
- a pre-push verifier installer
- a Claude stop hook
- cross-platform installers

## 20. Security semantics

Roach establishes evidence-backed assurance, not absolute truth. Read `THREAT-MODEL.md` for explicit threat boundaries and non-claims.

## 21. Compatibility

The protocol is intentionally open. JSON schemas live under `schemas/`; alternate implementations may produce compatible evidence if they honor the state/evidence/hash semantics.

The reference implementation identifies itself as `roach-loop/3.0`.
