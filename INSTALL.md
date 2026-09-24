# Install Roach Loop

## Recommended

Clone Roach Loop, run its tests, then copy/install it into the Git project you want to protect.

```bash
git clone https://github.com/warmachine22/Roachloop.git
cd Roachloop
python3 -m unittest discover -s tests -v
./install.sh /path/to/your/project
cd /path/to/your/project
python3 scripts/roach.py init --name "My Product"
```

## Claude / Codex instruction

Add this small rule to your project-level agent instructions:

```text
This repository uses Roach Loop.
Before substantial work run python3 scripts/roach.py next.
Use python3 scripts/roach.py context <checkpoint> --role worker.
Never manually edit Roach-managed gate state.
Before claiming completion run python3 scripts/roach.py verify-project.
```

For Claude Code you may additionally wire `hooks/stop-gate-check.sh` into a Stop hook. Codex and other agents can use the same CLI without relying on a hook.

## First checkpoint

```bash
python3 scripts/roach.py requirement add FR-001 "User can sign in"
python3 scripts/roach.py checkpoint add CP-001 "Sign in" --requirements FR-001 --verify "pytest -q tests/test_login.py"
python3 scripts/roach.py start CP-001
# implement and commit candidate code
python3 scripts/roach.py verify CP-001
python3 scripts/roach.py next
```

Roach writes managed state to `.roach/`. Do not manually mark gates passed there.
