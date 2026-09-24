# Start Here — Roach Loop v3

## Verify Roach itself

```bash
python3 -m unittest discover -s tests -v
python3 scripts/roach.py capabilities --json
```

## Install into a Git project

```bash
./install.sh /path/to/project
cd /path/to/project
python3 scripts/roach.py init --name "My Product" --profile standard
```

Windows:

```powershell
.\install.ps1 -Target C:\path\to\project
```

## Give Claude/Codex this instruction

```text
This repository uses Roach Loop.
Run python3 scripts/roach.py next before substantial work.
For the active checkpoint use python3 scripts/roach.py context <checkpoint> --role worker.
Never manually edit Roach-managed gates or fabricate evidence.
Run python3 scripts/roach.py verify-project before claiming completion.
Stop when Roach requires human judgment.
```

## Normal loop

```bash
python3 scripts/roach.py next
python3 scripts/roach.py context CP-001 --role worker --json
# implement and commit
python3 scripts/roach.py verify CP-001
# review commands as policy requires
python3 scripts/roach.py approve CP-001 --approver "<human>"
python3 scripts/roach.py audit CP-001
python3 scripts/roach.py seal CP-001
```

## Change of mind

Do not silently rewrite accepted intent:

```bash
python3 scripts/roach.py redirect \
  --reason "We now want passwordless sign-in" \
  --checkpoints CP-003,CP-004 \
  --human "<human>"
```

Then supersede/update requirements and re-plan.

## Useful diagnostics

```bash
python3 scripts/roach.py doctor --json
python3 scripts/roach.py freshness --json
python3 scripts/roach.py status --json
python3 scripts/roach.py verify-project --json
python3 scripts/roach.py report
```
