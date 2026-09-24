# Roach Loop Threat Model

Roach Loop assumes coding agents, reviewers, and project state can be wrong. It does not assume an AI model is malicious; it assumes any probabilistic actor can produce incorrect or incomplete claims.

## Protected classes

- premature “done” claims
- skipped mandatory gates
- stale evidence reused after relevant code changes
- mutable status files that disagree with executed verification
- requirement drift and uncovered active requirements
- evidence tampering after creation
- reviewer identity reuse where independent review is required
- architecture rules silently violated by implementation
- known requirement contradictions
- accidental credential capture in evidence/report artifacts
- assurance downgrades below automatically detected risk

## Trust boundaries

The trusted computing base is deliberately small:

1. `scripts/roach.py`
2. Git object/state semantics
3. the executable verification/provider tools configured by the project
4. explicit human identity/intent assertions

Coding-agent narration, model reasoning, summaries, and manually edited gate claims are not treated as proof.

## Not claimed

Roach does **not** prove that software has no bugs, that a human has good product taste, that external services are truthful, or that a model reviewer is intelligent. It records and verifies the provenance and consistency of the evidence that exists.

## Fail-closed principle

A required capability that is unavailable should block the requested assurance profile rather than silently becoming “skipped.” External providers are capability-detected and their execution is captured as evidence.
