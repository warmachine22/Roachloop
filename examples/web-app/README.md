# Example: account settings web app

Requirements:
- FR-001: User can update display name.
- FR-002: Validation errors are visible and understandable.
- QR-001: Form is keyboard accessible.

Suggested commands:

```bash
python3 scripts/roach.py init --name "Settings Demo" --profile standard
python3 scripts/roach.py requirement add FR-001 "User can update display name"
python3 scripts/roach.py requirement add FR-002 "Validation errors are visible and understandable"
python3 scripts/roach.py requirement add QR-001 "Form is keyboard accessible" --kind quality
python3 scripts/roach.py checkpoint add CP-001 "Settings form" \
  --requirements FR-001,FR-002,QR-001 \
  --files "site/settings.html,tests/test_settings.py" \
  --verify "python -m unittest tests.test_settings"
```

Run behavior proof, UI review, accessibility provider, two adversarial reviews, human approval, audit, then seal.
