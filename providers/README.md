# Roach Loop evidence providers

Roach Loop can normalize evidence from specialized deterministic tools instead of asking an LLM to imitate them.

Default provider slots:

- `security` — defaults to Semgrep when available.
- `accessibility` — configure axe/Playwright or another accessibility command.
- `performance` — configure Lighthouse, k6, autocannon, pytest-benchmark, or another performance command.
- `migration` — configure a project-specific forward/rollback/data-integrity test.

Providers live in `.roach/plugins.json` after `roach init`.

A provider contract is:

```json
{
  "command": "the deterministic command to execute",
  "proof": "proof classification",
  "requires": ["required-executable"]
}
```

Run a provider with:

```bash
python3 scripts/roach.py plugin run security --checkpoint CP-004
```

Roach captures the command, exit code, output hashes, provider identity, Git state, and evidence hash. Missing required executables fail closed.
