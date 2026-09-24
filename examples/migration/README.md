# Example: database migration

Requirements:
- FR-001: Existing rows preserve semantic meaning.
- QR-001: Forward migration succeeds.
- QR-002: Rollback succeeds or an explicit irreversible decision is recorded.

Use a checkpoint whose files include `migrations/*`. Configure `migration-test.sh` to create a fixture database, run forward migration, verify data, roll back, and verify data again.

```bash
python3 scripts/roach.py plugin run migration --checkpoint CP-MIG
```

The provider output is hashed into evidence. High-risk detection can also add a security gate.
