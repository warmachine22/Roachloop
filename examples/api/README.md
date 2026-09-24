# Example: headless API

Requirements:
- FR-001: Valid payload creates a record.
- FR-002: Invalid payload returns a deterministic validation error.
- QR-001: Authorization rejects callers without the required permission.

Suggested checkpoint:

```bash
python3 scripts/roach.py checkpoint add CP-API "Create record endpoint" \
  --requirements FR-001,FR-002,QR-001 \
  --files "api/*,tests/api/*" \
  --verify "pytest -q tests/api" \
  --no-ui
```

Because authorization is present, automatic risk detection should raise assurance rather than allowing a low-risk declaration.
