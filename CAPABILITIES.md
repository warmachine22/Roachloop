# Roach Loop — 70 Capability Implementation Map

Roach Loop v3 implements the original 70-capability design as one coherent assurance protocol. This file maps each design item to its executable surface.

| ID | Capability | Primary implementation |
|---|---|---|
| RL-01 | Deterministic verification kernel | `verify` |
| RL-02 | Tamper-evident event ledger | `ledger.jsonl` |
| RL-03 | Hashed evidence manifests | `evidence/*/manifest.json` |
| RL-04 | Exact Git provenance binding | `behavior receipt head/tree` |
| RL-05 | Stale evidence invalidation | `freshness/check` |
| RL-06 | Illegal-state rejection | `transition()` |
| RL-07 | Formal checkpoint state machine | `TRANSITIONS` |
| RL-08 | Assertion/evidence separation | `proof_type fields` |
| RL-09 | Requirement lifecycle | `requirement` |
| RL-10 | Bidirectional traceability graph | `graph()` |
| RL-11 | Machine-readable requirements | `requirements.json` |
| RL-12 | Deterministic independent audit | `audit` |
| RL-13 | Reviewer identity/context provenance | `review` |
| RL-14 | Review disagreement/finding lifecycle | `finding` |
| RL-15 | Risk-adaptive assurance | `PROFILE_POLICY` |
| RL-16 | Automatic risk escalation | `detect_risk` |
| RL-17 | Gate/plugin provider interface | `plugin` |
| RL-18 | Sandboxed verification adapter | `verify --sandbox` |
| RL-19 | Reproducible environment fingerprint | `environment_fingerprint` |
| RL-20 | Deterministic test receipts | `behavior evidence` |
| RL-21 | Baseline/mutation hooks | `baseline / --mutation` |
| RL-22 | Change-impact analysis | `impact` |
| RL-23 | Evidence dependency graph | `graph` |
| RL-24 | Evidence freshness | `freshness` |
| RL-25 | Exact-artifact human approval | `approve` |
| RL-26 | Objective/subjective proof classification | `proof_type/proof_strength` |
| RL-27 | Proof-strength provenance | `proof_strength` |
| RL-28 | AI provenance metadata | `review metadata` |
| RL-29 | Protocol versioning | `PROTOCOL` |
| RL-30 | Explicit upgrades | `upgrade` |
| RL-31 | Doctor diagnostics | `doctor` |
| RL-32 | Human-readable status | `status` |
| RL-33 | Evidence dashboard/report | `report` |
| RL-34 | Why-green | `why` |
| RL-35 | Why-not-green | `why` |
| RL-36 | Checkpoint seals | `seal` |
| RL-37 | Release seals | `release` |
| RL-38 | Portable assurance reports | `report` |
| RL-39 | JSON output/API surface | `--json/export` |
| RL-40 | Formal protocol specification | `ROACH-PROTOCOL.md` |
| RL-41 | Open compatibility model | `protocol JSON` |
| RL-42 | CI enforcement | `GitHub Actions` |
| RL-43 | Pre-push enforcement | `prepush install` |
| RL-44 | Secret-aware evidence | `redact/secret scan` |
| RL-45 | Security gate adapter | `plugin security` |
| RL-46 | Accessibility gate adapter | `plugin accessibility` |
| RL-47 | Performance gate adapter | `plugin performance` |
| RL-48 | Migration gate adapter | `plugin migration` |
| RL-49 | External evidence providers | `external` |
| RL-50 | Human product authority | `config human_authority` |
| RL-51 | First-class redirect | `redirect` |
| RL-52 | Decision lineage | `decision` |
| RL-53 | Architecture drift | `architecture` |
| RL-54 | Contradiction detection | `conflicts` |
| RL-55 | Explicit uncertainty | `blocked/uncertainty status` |
| RL-56 | External dependency registry | `dependency` |
| RL-57 | Environment capability model | `capabilities` |
| RL-58 | No silent downgrade | `risk downgrade rejection` |
| RL-59 | Assurance profiles | `fast/standard/strict` |
| RL-60 | Dogfooding support | `self state + examples` |
| RL-61 | Hostile/tamper tests | `tests/test_roach.py` |
| RL-62 | Threat model | `threat-model` |
| RL-63 | Assurance-not-truth semantics | `config assurance_semantics` |
| RL-64 | Benchmark ledger | `benchmark` |
| RL-65 | Example corpus | `examples` |
| RL-66 | Self-verification site | `site` |
| RL-67 | Live proof export | `export` |
| RL-68 | AI-independent verifier | `verify-project` |
| RL-69 | Small trusted computing base | `scripts/roach.py` |
| RL-70 | Proof-carrying bundle | `release/report/evidence bundle` |

## What “implemented” means

For deterministic capabilities, Roach contains executable code and regression tests. For capabilities that inherently depend on outside systems (for example Semgrep, Lighthouse/axe, migration test harnesses, or container engines), Roach implements a provider contract, capability detection, evidence capture, fail-closed policy, and provenance; the external executable must still exist in the project environment.

Roach deliberately does not fake unavailable tools or human judgment. Strict assurance fails rather than silently downgrading when a required capability is unavailable.

## Trusted core

The trusted computing base is intentionally small: `scripts/roach.py`, Git, the configured verification executables, and the human identity/intent assertions supplied to Roach. Everything else—including coding-agent narration—is treated as untrusted input until backed by evidence.
